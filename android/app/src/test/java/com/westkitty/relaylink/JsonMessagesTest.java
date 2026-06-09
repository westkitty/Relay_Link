package com.westkitty.relaylink;

import static org.junit.Assert.assertEquals;

import org.json.JSONObject;
import org.junit.Test;

public final class JsonMessagesTest {
    @Test
    public void helloIncludesTabletRoleAndToken() throws Exception {
        var payload = new JSONObject(JsonMessages.hello(new RelayConfig("10.0.0.2", "secret", 1440, 900)));

        assertEquals("hello", payload.getString("type"));
        assertEquals("tablet", payload.getString("role"));
        assertEquals("secret", payload.getString("token"));
    }

    @Test
    public void clipboardPayloadMatchesRelayProtocol() throws Exception {
        var payload = new JSONObject(JsonMessages.clipboard("hello"));

        assertEquals("clipboard", payload.getString("type"));
        assertEquals("text", payload.getString("format"));
        assertEquals("tablet", payload.getString("sender"));
        assertEquals("hello", payload.getString("content"));
    }
}

