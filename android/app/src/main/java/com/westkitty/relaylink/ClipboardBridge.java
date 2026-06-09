package com.westkitty.relaylink;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.function.Consumer;

public final class ClipboardBridge {
    private final ClipboardManager clipboardManager;
    private final Consumer<String> outboundText;
    private String lastSelfHash = "";
    private String lastSentHash = "";

    private final ClipboardManager.OnPrimaryClipChangedListener listener = this::onClipboardChanged;

    public ClipboardBridge(Context context, Consumer<String> outboundText) {
        this.clipboardManager = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
        this.outboundText = outboundText;
    }

    public void start() {
        clipboardManager.addPrimaryClipChangedListener(listener);
        onClipboardChanged();
    }

    public void stop() {
        clipboardManager.removePrimaryClipChangedListener(listener);
    }

    public void writeInbound(String content) {
        lastSelfHash = hash(content);
        clipboardManager.setPrimaryClip(ClipData.newPlainText("Relay Link", content));
    }

    private void onClipboardChanged() {
        var clip = clipboardManager.getPrimaryClip();
        if (clip == null || clip.getItemCount() == 0) {
            return;
        }
        var text = clip.getItemAt(0).coerceToText(null);
        if (text == null) {
            return;
        }
        var content = text.toString();
        if (content.isBlank()) {
            return;
        }
        var contentHash = hash(content);
        if (contentHash.equals(lastSelfHash)) {
            lastSelfHash = "";
            return;
        }
        if (contentHash.equals(lastSentHash)) {
            return;
        }
        lastSentHash = contentHash;
        outboundText.accept(content);
    }

    private String hash(String content) {
        try {
            var digest = MessageDigest.getInstance("SHA-256").digest(content.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest);
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 unavailable", exception);
        }
    }
}

