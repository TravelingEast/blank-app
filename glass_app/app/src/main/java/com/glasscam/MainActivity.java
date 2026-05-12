package com.glasscam;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.widget.TextView;

/**
 * Minimal entry-point activity.
 *
 * On Glass XE the prism display still works if present; this activity shows
 * a simple status screen. If you remove the display module you can still
 * launch the service via ADB:
 *
 *   adb shell am start -n com.glasscam/.MainActivity
 *   adb shell am startservice -n com.glasscam/.CameraStreamService
 *
 * Touch-pad gestures forwarded to the running service:
 *   Single tap  → immediate capture
 *   Swipe back  → toggle pause / resume
 */
public class MainActivity extends Activity {

    private TextView statusText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Full-screen, no title bar
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION);

        setContentView(R.layout.activity_main);
        statusText = findViewById(R.id.status_text);

        startService(new Intent(this, CameraStreamService.class));
        updateStatus("Running — tap to capture, swipe back to pause");
    }

    private void updateStatus(String msg) {
        if (statusText != null) statusText.setText(msg);
    }

    // Glass touchpad fires KEYCODE_DPAD_CENTER for a tap
    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_DPAD_CENTER) {
            sendServiceAction(CameraStreamService.ACTION_CAPTURE_NOW);
            updateStatus("Capturing…");
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    // Swipe-back on Glass touchpad fires KEYCODE_BACK
    @Override
    public void onBackPressed() {
        sendServiceAction(CameraStreamService.ACTION_TOGGLE_PAUSE);
    }

    private void sendServiceAction(String action) {
        Intent i = new Intent(this, CameraStreamService.class);
        i.setAction(action);
        startService(i);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        // Service keeps running; activity is just the control surface
    }
}
