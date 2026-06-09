package com.westkitty.relaylink;

import android.os.Handler;
import android.os.Looper;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;

import org.json.JSONException;
import org.json.JSONObject;

import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;

public final class RelayWebSocket {
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private final OkHttpClient client = new OkHttpClient.Builder()
            .pingInterval(15, TimeUnit.SECONDS)
            .build();
    private final RelayConfig config;
    private final Consumer<String> inboundClipboard;
    private final Consumer<String> status;
    private WebSocket webSocket;
    private boolean shouldRun;

    public RelayWebSocket(RelayConfig config, Consumer<String> inboundClipboard, Consumer<String> status) {
        this.config = config;
        this.inboundClipboard = inboundClipboard;
        this.status = status;
    }

    public void start() {
        shouldRun = true;
        connect();
    }

    public void stop() {
        shouldRun = false;
        if (webSocket != null) {
            webSocket.close(1000, "Relay Link stopped");
        }
        client.dispatcher().executorService().shutdown();
    }

    public void send(String message) {
        if (webSocket != null) {
            webSocket.send(message);
        }
    }

    private void connect() {
        status.accept("connecting " + config.webSocketUrl());
        var request = new Request.Builder().url(config.webSocketUrl()).build();
        webSocket = client.newWebSocket(request, new WebSocketListener() {
            @Override
            public void onOpen(WebSocket socket, Response response) {
                status.accept("connected");
                socket.send(JsonMessages.hello(config));
            }

            @Override
            public void onMessage(WebSocket socket, String text) {
                handleMessage(text);
            }

            @Override
            public void onFailure(WebSocket socket, Throwable throwable, Response response) {
                status.accept("disconnected: " + throwable.getClass().getSimpleName());
                reconnectLater();
            }

            @Override
            public void onClosed(WebSocket socket, int code, String reason) {
                status.accept("closed");
                reconnectLater();
            }
        });
    }

    private void handleMessage(String text) {
        try {
            var json = new JSONObject(text);
            if (!"clipboard".equals(json.optString("type"))) {
                return;
            }
            var content = json.optString("content", "");
            if (!content.isBlank()) {
                inboundClipboard.accept(content);
            }
        } catch (JSONException exception) {
            status.accept("bad json");
        }
    }

    private void reconnectLater() {
        if (shouldRun) {
            mainHandler.postDelayed(this::connect, 3000);
        }
    }
}

