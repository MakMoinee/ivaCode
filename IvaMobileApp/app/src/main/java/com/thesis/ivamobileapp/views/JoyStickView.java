package com.thesis.ivamobileapp.views;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;
import androidx.annotation.Nullable;

public class JoyStickView extends View {
    private float centerX, centerY;
    private float knobX, knobY;
    private float radius, knobRadius;
    private Paint outerCirclePaint, knobPaint, borderPaint;
    private JoystickListener listener;

    public JoyStickView(Context context) {
        this(context, null);
    }

    public JoyStickView(Context context, @Nullable AttributeSet attrs) {
        this(context, attrs, 0);
    }

    public JoyStickView(Context context, @Nullable AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }

    private void init() {
        outerCirclePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        outerCirclePaint.setColor(Color.parseColor("#1d1c21"));
        outerCirclePaint.setStyle(Paint.Style.FILL);

        borderPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        borderPaint.setColor(Color.parseColor("#33FFFFFF")); // Subtle transparent white border
        borderPaint.setStyle(Paint.Style.STROKE);
        borderPaint.setStrokeWidth(2f);

        knobPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        knobPaint.setColor(Color.parseColor("#17161b"));
        knobPaint.setStyle(Paint.Style.FILL);
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);
        centerX = w / 2f;
        centerY = h / 2f;
        
        float minDimension = Math.min(w, h);
        // We ensure that (radius + knobRadius) is less than (minDimension / 2) 
        // to prevent the knob from being clipped at the edges.
        radius = minDimension / 3.2f; 
        knobRadius = radius / 2.2f;

        resetJoystick();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        // Draw outer circle
        canvas.drawCircle(centerX, centerY, radius, outerCirclePaint);
        // Draw outer border so it's visible on black
        canvas.drawCircle(centerX, centerY, radius, borderPaint);
        // Draw joystick knob
        canvas.drawCircle(knobX, knobY, knobRadius, knobPaint);
        // Draw knob border
        canvas.drawCircle(knobX, knobY, knobRadius, borderPaint);
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        float dx = event.getX() - centerX;
        float dy = event.getY() - centerY;
        float distance = (float) Math.sqrt(dx * dx + dy * dy);

        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
            case MotionEvent.ACTION_MOVE:
                if (distance < radius) {
                    knobX = event.getX();
                    knobY = event.getY();
                } else {
                    float angle = (float) Math.atan2(dy, dx);
                    knobX = centerX + radius * (float) Math.cos(angle);
                    knobY = centerY + radius * (float) Math.sin(angle);
                }
                if (listener != null) {
                    listener.onJoystickMoved((knobX - centerX) / radius, (knobY - centerY) / radius);
                }
                break;

            case MotionEvent.ACTION_UP:
                resetJoystick();
                if (listener != null) {
                    listener.onJoystickMoved(0, 0);
                }
                break;
        }
        invalidate();
        return true;
    }

    private void resetJoystick() {
        knobX = centerX;
        knobY = centerY;
        invalidate();
    }

    public void setJoystickListener(JoystickListener listener) {
        this.listener = listener;
    }

    public interface JoystickListener {
        void onJoystickMoved(float xPercent, float yPercent);
    }
}
