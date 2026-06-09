package com.westkitty.relaylink;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;

public final class RelayService extends Service {
    public static final String ACTION_SEND_POINTER = "com.westkitty.relaylink.SEND_POINTER";
    public static final String EXTRA_X = "x";
    public static final String EXTRA_Y = "y";
    public static final String EXTRA_ACTION = "pointer_action";

    private static final String CHANNEL_ID = "relay_link";
    private RelayWebSocket relayWebSocket;
    private ClipboardBridge clipboardBridge;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        startForeground(1, notification("Relay Link connecting"));
        var config = RelayConfig.load(this);
        relayWebSocket = new RelayWebSocket(
                config,
                content -> clipboardBridge.writeInbound(content),
                status -> startForeground(1, notification("Relay Link " + status)));
        clipboardBridge = new ClipboardBridge(this, text -> relayWebSocket.send(JsonMessages.clipboard(text)));
        clipboardBridge.start();
        relayWebSocket.start();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_SEND_POINTER.equals(intent.getAction()) && relayWebSocket != null) {
            var x = intent.getFloatExtra(EXTRA_X, 0);
            var y = intent.getFloatExtra(EXTRA_Y, 0);
            var action = intent.getStringExtra(EXTRA_ACTION);
            relayWebSocket.send(JsonMessages.pointer(x, y, action == null ? "move" : action));
        }
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        if (clipboardBridge != null) {
            clipboardBridge.stop();
        }
        if (relayWebSocket != null) {
            relayWebSocket.stop();
        }
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private Notification notification(String text) {
        return new Notification.Builder(this, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_launcher)
                .setContentTitle("Relay Link")
                .setContentText(text)
                .setOngoing(true)
                .build();
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return;
        }
        var channel = new NotificationChannel(
                CHANNEL_ID,
                "Relay Link",
                NotificationManager.IMPORTANCE_LOW);
        getSystemService(NotificationManager.class).createNotificationChannel(channel);
    }
}

