package com.glasscam;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.util.Log;

/** Auto-starts the camera service when Glass boots. */
public class BootReceiver extends BroadcastReceiver {
    private static final String TAG = "GlassCam/Boot";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
            Log.i(TAG, "Boot complete — starting CameraStreamService");
            Intent service = new Intent(context, CameraStreamService.class);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(service);
            } else {
                context.startService(service);
            }
        }
    }
}
