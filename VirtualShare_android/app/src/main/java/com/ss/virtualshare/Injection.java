package com.ss.virtualshare;

import android.util.Log;

import java.io.DataOutputStream;

public final class Injection {

    static {
        System.loadLibrary ("vshare-lib");
    }

    public static final String TAG = "INJECTOR";
    public static final native void start (String deviceName);
    public static native void stop ();
    public static native void keydown (int key, int mask);
    public static native void keyup (int key, int mask);
    public static native void keydown2 (int key);
    public static native void keyup2 (int key);
    public static final native void movemouse (final int x, final int y);
    public static native void mousedown (int buttonId);
    public static native void mouseup (int buttonId);
    public static native void mousewheel (int x, int y);

    private Injection () { }

    public static void setPermissionsForInputDevice () {
        Log.d(TAG, "Starting injection");
        try {
            Process process = Runtime.getRuntime ().exec ("su");
            DataOutputStream dout = new DataOutputStream (process.getOutputStream ());
            dout.writeBytes ("chmod 666 /dev/uinput");
            dout.flush ();
            dout.close ();
            process.waitFor ();
            Log.d (TAG,"Access to /dev/uinput granted");
        } catch (Exception e) {
            e.printStackTrace ();
        }
    }

    public static void startInjection (String deviceName) {
        start (deviceName);
    }

    public static void stopInjection () {
        stop ();
    }
}