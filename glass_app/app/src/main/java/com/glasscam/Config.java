package com.glasscam;

import android.content.Context;
import android.os.Environment;
import android.util.Log;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.Properties;

/**
 * Reads config from /sdcard/glasscam/glasscam.conf so you can reconfigure
 * without recompiling. Push the file with:
 *   adb push glasscam.conf /sdcard/glasscam/glasscam.conf
 */
public class Config {
    private static final String TAG = "GlassCam/Config";
    private static final String CONFIG_PATH =
            Environment.getExternalStorageDirectory() + "/glasscam/glasscam.conf";

    public String serverUrl = "http://192.168.1.100:5000";
    public int captureIntervalSeconds = 4;
    public String defaultPrompt = "Briefly describe what you see in one sentence.";
    public String deviceId = android.os.Build.SERIAL;
    public boolean saveLocally = true;
    public boolean streamToServer = true;
    public int jpegQuality = 80;   // 0-100
    public int previewWidth = 1280;
    public int previewHeight = 720;

    public static Config load(Context context) {
        Config cfg = new Config();
        File f = new File(CONFIG_PATH);
        if (!f.exists()) {
            Log.w(TAG, "No config file found at " + CONFIG_PATH + " — using defaults");
            return cfg;
        }
        try {
            Properties p = new Properties();
            p.load(new BufferedReader(new FileReader(f)));

            if (p.containsKey("server_url"))      cfg.serverUrl = p.getProperty("server_url").trim();
            if (p.containsKey("interval"))        cfg.captureIntervalSeconds = Integer.parseInt(p.getProperty("interval").trim());
            if (p.containsKey("prompt"))          cfg.defaultPrompt = p.getProperty("prompt").trim();
            if (p.containsKey("device_id"))       cfg.deviceId = p.getProperty("device_id").trim();
            if (p.containsKey("save_locally"))    cfg.saveLocally = Boolean.parseBoolean(p.getProperty("save_locally").trim());
            if (p.containsKey("stream"))          cfg.streamToServer = Boolean.parseBoolean(p.getProperty("stream").trim());
            if (p.containsKey("jpeg_quality"))    cfg.jpegQuality = Integer.parseInt(p.getProperty("jpeg_quality").trim());

            Log.i(TAG, "Config loaded: server=" + cfg.serverUrl + " interval=" + cfg.captureIntervalSeconds + "s");
        } catch (IOException | NumberFormatException e) {
            Log.e(TAG, "Error reading config: " + e.getMessage());
        }
        return cfg;
    }
}
