package com.westkitty.relaylink;

import org.json.JSONException;
import org.json.JSONObject;

public final class JsonMessages {
    private JsonMessages() {}

    public static String hello(RelayConfig config) {
        var json = new JSONObject();
        try {
            json.put("type", "hello");
            json.put("role", "tablet");
            if (!config.token().isBlank()) {
                json.put("token", config.token());
            }
            return json.toString();
        } catch (JSONException exception) {
            throw new IllegalStateException("Unable to build hello payload", exception);
        }
    }

    public static String clipboard(String text) {
        var json = new JSONObject();
        try {
            json.put("type", "clipboard");
            json.put("format", "text");
            json.put("sender", "tablet");
            json.put("content", text);
            return json.toString();
        } catch (JSONException exception) {
            throw new IllegalStateException("Unable to build clipboard payload", exception);
        }
    }

    public static String pointer(float x, float y, String action) {
        var json = new JSONObject();
        try {
            json.put("type", "pointer");
            json.put("x", x);
            json.put("y", y);
            json.put("action", action);
            json.put("button", "left");
            return json.toString();
        } catch (JSONException exception) {
            throw new IllegalStateException("Unable to build pointer payload", exception);
        }
    }
}

