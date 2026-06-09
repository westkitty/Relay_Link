package com.westkitty.relaylink;

import android.content.Context;
import android.content.SharedPreferences;

public record RelayConfig(String host, String token, int macWidth, int macHeight) {
    private static final String PREFS = "relay_link";
    private static final String HOST = "host";
    private static final String TOKEN = "token";
    private static final String MAC_WIDTH = "mac_width";
    private static final String MAC_HEIGHT = "mac_height";

    public static RelayConfig load(Context context) {
        var prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return new RelayConfig(
                prefs.getString(HOST, "192.168.1.10"),
                prefs.getString(TOKEN, ""),
                prefs.getInt(MAC_WIDTH, 1440),
                prefs.getInt(MAC_HEIGHT, 900));
    }

    public void save(Context context) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit()
                .putString(HOST, host)
                .putString(TOKEN, token)
                .putInt(MAC_WIDTH, macWidth)
                .putInt(MAC_HEIGHT, macHeight)
                .apply();
    }

    public String webSocketUrl() {
        return "ws://" + host + ":8765";
    }
}

