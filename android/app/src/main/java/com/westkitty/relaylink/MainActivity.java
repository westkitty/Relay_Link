package com.westkitty.relaylink;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class MainActivity extends Activity {
    private EditText hostInput;
    private EditText tokenInput;
    private EditText widthInput;
    private EditText heightInput;
    private TextView statusView;
    private RelayConfig config;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        config = RelayConfig.load(this);
        applyLaunchExtras();
        setContentView(buildLayout());
        requestNotificationPermission();
        if (getIntent().getBooleanExtra("autostart", false)) {
            startRelay();
        }
    }

    private void applyLaunchExtras() {
        var intent = getIntent();
        if (intent == null) {
            return;
        }
        var host = intent.getStringExtra("host");
        var token = intent.getStringExtra("token");
        var macWidth = intent.getIntExtra("mac_width", config.macWidth());
        var macHeight = intent.getIntExtra("mac_height", config.macHeight());
        config = new RelayConfig(
                host == null || host.isBlank() ? config.host() : host,
                token == null ? config.token() : token,
                macWidth,
                macHeight);
        config.save(this);
    }

    private View buildLayout() {
        var root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(36, 36, 36, 36);
        root.setBackgroundColor(Color.rgb(248, 250, 252));

        var title = label("Relay Link Android");
        title.setTextSize(24);
        root.addView(title);

        hostInput = input(config.host(), "Mac IP address");
        tokenInput = input(config.token(), "Shared token");
        widthInput = input(String.valueOf(config.macWidth()), "Mac display width");
        heightInput = input(String.valueOf(config.macHeight()), "Mac display height");
        root.addView(hostInput);
        root.addView(tokenInput);
        root.addView(widthInput);
        root.addView(heightInput);

        var connect = button("Save and Start Relay");
        connect.setOnClickListener(view -> startRelay());
        root.addView(connect);

        var stop = button("Stop Relay");
        stop.setOnClickListener(view -> stopService(new Intent(this, RelayService.class)));
        root.addView(stop);

        statusView = label("Service idle");
        root.addView(statusView);

        var touchPadLabel = label("Pointer pad");
        root.addView(touchPadLabel);
        root.addView(new PointerPad(this, this::sendPointer));
        return root;
    }

    private void startRelay() {
        config = new RelayConfig(
                hostInput.getText().toString().trim(),
                tokenInput.getText().toString().trim(),
                parseDimension(widthInput, 1440),
                parseDimension(heightInput, 900));
        config.save(this);
        var intent = new Intent(this, RelayService.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent);
        } else {
            startService(intent);
        }
        statusView.setText("Relay service started for ws://" + config.host() + ":8765");
    }

    private void sendPointer(float normalizedX, float normalizedY, String action) {
        var intent = new Intent(this, RelayService.class);
        intent.setAction(RelayService.ACTION_SEND_POINTER);
        intent.putExtra(RelayService.EXTRA_X, normalizedX * config.macWidth());
        intent.putExtra(RelayService.EXTRA_Y, normalizedY * config.macHeight());
        intent.putExtra(RelayService.EXTRA_ACTION, action);
        startService(intent);
    }

    private void requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                        != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[] {Manifest.permission.POST_NOTIFICATIONS}, 10);
        }
    }

    private TextView label(String text) {
        var view = new TextView(this);
        view.setText(text);
        view.setTextColor(Color.rgb(15, 23, 42));
        view.setTextSize(16);
        view.setPadding(0, 14, 0, 8);
        return view;
    }

    private EditText input(String value, String hint) {
        var input = new EditText(this);
        input.setText(value);
        input.setHint(hint);
        input.setSingleLine(true);
        input.setTextColor(Color.rgb(15, 23, 42));
        input.setHintTextColor(Color.rgb(100, 116, 139));
        return input;
    }

    private Button button(String text) {
        var button = new Button(this);
        button.setText(text);
        return button;
    }

    private int parseDimension(EditText input, int fallback) {
        try {
            return Math.max(1, Integer.parseInt(input.getText().toString().trim()));
        } catch (NumberFormatException exception) {
            return fallback;
        }
    }

    private static final class PointerPad extends View {
        private final PointerSender pointerSender;

        PointerPad(Context context, PointerSender pointerSender) {
            super(context);
            this.pointerSender = pointerSender;
            setMinimumHeight(420);
            setBackgroundColor(Color.rgb(226, 232, 240));
        }

        @Override
        public boolean onTouchEvent(MotionEvent event) {
            var x = clamp(event.getX() / Math.max(1, getWidth()));
            var y = clamp(event.getY() / Math.max(1, getHeight()));
            var action = switch (event.getActionMasked()) {
                case MotionEvent.ACTION_DOWN -> "down";
                case MotionEvent.ACTION_UP -> "up";
                default -> "move";
            };
            pointerSender.send(x, y, action);
            return true;
        }

        private float clamp(float value) {
            return Math.max(0, Math.min(1, value));
        }
    }

    private interface PointerSender {
        void send(float normalizedX, float normalizedY, String action);
    }
}
