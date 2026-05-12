package com.glasscam;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.graphics.ImageFormat;
import android.graphics.Rect;
import android.graphics.SurfaceTexture;
import android.graphics.YuvImage;
import android.hardware.Camera;
import android.os.Build;
import android.os.Environment;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.speech.tts.TextToSpeech;
import android.util.Log;

import org.json.JSONObject;

import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

@SuppressWarnings("deprecation")
public class CameraStreamService extends Service {
    private static final String TAG = "GlassCam/Service";
    private static final int NOTIFICATION_ID = 42;
    private static final String CHANNEL_ID = "glasscam_channel";

    public static final String ACTION_CAPTURE_NOW = "com.glasscam.CAPTURE_NOW";
    public static final String ACTION_TOGGLE_PAUSE = "com.glasscam.TOGGLE_PAUSE";
    public static final String ACTION_STOP = "com.glasscam.STOP";

    private Camera camera;
    private SurfaceTexture surfaceTexture;
    private TextToSpeech tts;
    private Handler handler;
    private Config config;
    private boolean paused = false;
    private boolean ttsReady = false;
    private int cameraPreviewWidth;
    private int cameraPreviewHeight;

    // Runnable that fires every N seconds for continuous capture
    private final Runnable captureRunnable = new Runnable() {
        @Override
        public void run() {
            if (!paused) captureFrame();
            handler.postDelayed(this, config.captureIntervalSeconds * 1000L);
        }
    };

    @Override
    public void onCreate() {
        super.onCreate();
        handler = new Handler(Looper.getMainLooper());
        config = Config.load(this);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null) {
            String action = intent.getAction();
            if (ACTION_CAPTURE_NOW.equals(action)) {
                captureFrame();
                return START_STICKY;
            } else if (ACTION_TOGGLE_PAUSE.equals(action)) {
                paused = !paused;
                speak(paused ? "Paused." : "Resuming.");
                updateNotification();
                return START_STICKY;
            } else if (ACTION_STOP.equals(action)) {
                stopSelf();
                return START_NOT_STICKY;
            }
        }

        startForeground(NOTIFICATION_ID, buildNotification("Starting…"));
        initTts();
        initCamera();

        handler.postDelayed(captureRunnable, 2000); // small delay for TTS init
        return START_STICKY;
    }

    // ── Camera ──────────────────────────────────────────────────────────────

    private void initCamera() {
        try {
            camera = Camera.open(0);
            Camera.Parameters params = camera.getParameters();

            // Pick the best supported preview size close to 1280×720
            Camera.Size best = chooseBestSize(params.getSupportedPreviewSizes(),
                    config.previewWidth, config.previewHeight);
            params.setPreviewSize(best.width, best.height);
            cameraPreviewWidth = best.width;
            cameraPreviewHeight = best.height;

            // Also configure picture size for highest still quality
            Camera.Size bestPic = chooseBestSize(params.getSupportedPictureSizes(), 1280, 720);
            params.setPictureSize(bestPic.width, bestPic.height);
            params.setPictureFormat(ImageFormat.JPEG);
            params.setJpegQuality(config.jpegQuality);

            // Auto-focus if available
            List<String> focusModes = params.getSupportedFocusModes();
            if (focusModes != null && focusModes.contains(Camera.Parameters.FOCUS_MODE_CONTINUOUS_PICTURE)) {
                params.setFocusMode(Camera.Parameters.FOCUS_MODE_CONTINUOUS_PICTURE);
            } else if (focusModes != null && focusModes.contains(Camera.Parameters.FOCUS_MODE_AUTO)) {
                params.setFocusMode(Camera.Parameters.FOCUS_MODE_AUTO);
            }

            camera.setParameters(params);

            // SurfaceTexture lets us run preview without any visible display surface
            surfaceTexture = new SurfaceTexture(10);
            camera.setPreviewTexture(surfaceTexture);
            camera.startPreview();

            Log.i(TAG, "Camera ready: preview=" + cameraPreviewWidth + "×" + cameraPreviewHeight);
        } catch (Exception e) {
            Log.e(TAG, "Camera init failed: " + e.getMessage());
        }
    }

    private Camera.Size chooseBestSize(List<Camera.Size> sizes, int targetW, int targetH) {
        Camera.Size best = sizes.get(0);
        int bestDelta = Integer.MAX_VALUE;
        for (Camera.Size s : sizes) {
            int delta = Math.abs(s.width - targetW) + Math.abs(s.height - targetH);
            if (delta < bestDelta) { bestDelta = delta; best = s; }
        }
        return best;
    }

    /**
     * Takes a JPEG still via takePicture(). Restarts preview automatically so
     * the next capture cycle works. Runs on the main thread; upload is async.
     */
    private void captureFrame() {
        if (camera == null) { Log.w(TAG, "Camera not ready"); return; }
        try {
            camera.takePicture(null, null, null, (data, cam) -> {
                Log.d(TAG, "Captured " + data.length + " bytes");
                if (config.saveLocally) saveLocally(data);
                if (config.streamToServer) uploadFrame(data, config.defaultPrompt);
                try { cam.startPreview(); } catch (Exception ignored) {}
            });
        } catch (Exception e) {
            Log.e(TAG, "takePicture failed: " + e.getMessage());
            // Camera may have entered a bad state; re-initialise
            releaseCamera();
            initCamera();
        }
    }

    // ── HTTP upload ──────────────────────────────────────────────────────────

    private void uploadFrame(final byte[] jpegData, final String prompt) {
        new Thread(() -> {
            String boundary = "----GlassCamBoundary" + System.currentTimeMillis();
            HttpURLConnection conn = null;
            try {
                URL url = new URL(config.serverUrl + "/upload_frame");
                conn = (HttpURLConnection) url.openConnection();
                conn.setDoOutput(true);
                conn.setRequestMethod("POST");
                conn.setConnectTimeout(6000);
                conn.setReadTimeout(15000);
                conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
                conn.setRequestProperty("X-Device-Id", config.deviceId);

                try (OutputStream os = new BufferedOutputStream(conn.getOutputStream())) {
                    // -- frame field
                    writeMultipartField(os, boundary, "frame", "frame.jpg", "image/jpeg", jpegData);
                    // -- prompt field
                    writeMultipartText(os, boundary, "prompt", prompt);
                    // -- close
                    os.write(("\r\n--" + boundary + "--\r\n").getBytes(StandardCharsets.UTF_8));
                }

                int code = conn.getResponseCode();
                if (code == 200) {
                    BufferedReader br = new BufferedReader(
                            new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null) sb.append(line);
                    br.close();

                    JSONObject json = new JSONObject(sb.toString());
                    String responseText = json.getString("response");
                    Log.i(TAG, "AI: " + responseText);
                    speak(responseText);
                } else {
                    Log.w(TAG, "Server returned HTTP " + code);
                }
            } catch (Exception e) {
                Log.e(TAG, "Upload error: " + e.getMessage());
            } finally {
                if (conn != null) conn.disconnect();
            }
        }).start();
    }

    private void writeMultipartField(OutputStream os, String boundary,
            String name, String filename, String mime, byte[] data) throws IOException {
        String header = "--" + boundary + "\r\n"
                + "Content-Disposition: form-data; name=\"" + name
                + "\"; filename=\"" + filename + "\"\r\n"
                + "Content-Type: " + mime + "\r\n\r\n";
        os.write(header.getBytes(StandardCharsets.UTF_8));
        os.write(data);
        os.write("\r\n".getBytes(StandardCharsets.UTF_8));
    }

    private void writeMultipartText(OutputStream os, String boundary,
            String name, String value) throws IOException {
        String part = "--" + boundary + "\r\n"
                + "Content-Disposition: form-data; name=\"" + name + "\"\r\n\r\n"
                + value + "\r\n";
        os.write(part.getBytes(StandardCharsets.UTF_8));
    }

    // ── Local storage fallback ───────────────────────────────────────────────

    private void saveLocally(byte[] jpegData) {
        try {
            File dir = new File(Environment.getExternalStorageDirectory(), "glasscam/captures");
            if (!dir.exists()) dir.mkdirs();
            String ts = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
            File out = new File(dir, ts + ".jpg");
            try (FileOutputStream fos = new FileOutputStream(out)) {
                fos.write(jpegData);
            }
            Log.d(TAG, "Saved " + out.getAbsolutePath());
        } catch (IOException e) {
            Log.e(TAG, "Local save failed: " + e.getMessage());
        }
    }

    // ── TTS ──────────────────────────────────────────────────────────────────

    private void initTts() {
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                tts.setLanguage(Locale.US);
                ttsReady = true;
                speak("Glass AI camera ready.");
            }
        });
    }

    private void speak(final String text) {
        handler.post(() -> {
            if (tts != null && ttsReady) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                    tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "glasscam_utt");
                } else {
                    tts.speak(text, TextToSpeech.QUEUE_FLUSH, null);
                }
            }
        });
    }

    // ── Notification ─────────────────────────────────────────────────────────

    private Notification buildNotification(String status) {
        createNotificationChannel();
        Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);
        return builder
                .setContentTitle("GlassCam AI")
                .setContentText(paused ? "Paused — tap to resume" : status)
                .setSmallIcon(android.R.drawable.ic_menu_camera)
                .setOngoing(true)
                .build();
    }

    private Notification buildNotification() {
        return buildNotification("Streaming to AI…");
    }

    private void updateNotification() {
        NotificationManager nm = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm != null) nm.notify(NOTIFICATION_ID, buildNotification());
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel ch = new NotificationChannel(
                    CHANNEL_ID, "GlassCam", NotificationManager.IMPORTANCE_LOW);
            ch.setDescription("GlassCam AI camera service");
            NotificationManager nm = getSystemService(NotificationManager.class);
            if (nm != null) nm.createNotificationChannel(ch);
        }
    }

    // ── Lifecycle ────────────────────────────────────────────────────────────

    private void releaseCamera() {
        if (camera != null) {
            try { camera.stopPreview(); } catch (Exception ignored) {}
            camera.release();
            camera = null;
        }
    }

    @Override
    public void onDestroy() {
        handler.removeCallbacks(captureRunnable);
        releaseCamera();
        if (surfaceTexture != null) { surfaceTexture.release(); surfaceTexture = null; }
        if (tts != null) { tts.stop(); tts.shutdown(); }
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
