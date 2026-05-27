package com.thesis.ivamobileapp.uifragments;

import android.content.Context;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.thesis.ivamobileapp.databinding.FragmentHomeBinding;
import com.thesis.ivamobileapp.interfaces.FragmentHandler;
import com.thesis.ivamobileapp.views.JoyStickView;

public class HomeFragment extends Fragment {

    FragmentHomeBinding binding;
    FragmentHandler handler;
    private int lastDirection = -1; // -1: none, 0: forward, 1: backward, 2: left, 3: right
    private boolean isConnected = false; // Mock connection state
    private boolean isFollowMode = false;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentHomeBinding.inflate(LayoutInflater.from(requireContext()), container, false);
        setListeners();
        return binding.getRoot();
    }

    private void setListeners() {
        binding.btnFollow.setOnClickListener(v -> {
            isFollowMode = !isFollowMode;
            if (isFollowMode) {
                binding.btnFollow.setText("Disable Follow Mode");
                // Optional: change color to indicate active state
                binding.btnFollow.setBackgroundTintList(android.content.res.ColorStateList.valueOf(android.graphics.Color.parseColor("#4CAF50")));
            } else {
                binding.btnFollow.setText("Enable Follow Mode");
                binding.btnFollow.setBackgroundTintList(android.content.res.ColorStateList.valueOf(android.graphics.Color.parseColor("#1d1c21")));
            }
            handler.onToggleFollowMode(isFollowMode);
        });

        binding.btnAction.setOnClickListener(v -> {
            if (!isConnected) {
                handler.onConnectBT();
                // Mock state change for UI demonstration
                isConnected = true;
                binding.btnAction.setText("Disconnect from IVA");
                
                // Enable camera button when connected to IVA
                binding.btnCamera.setEnabled(true);
                binding.btnCamera.setAlpha(1.0f);
            } else {
                // handler.onDisconnectBT(); // Placeholder for future backend
                isConnected = false;
                binding.btnAction.setText("Connect to IVA");
                
                // Disable camera button when disconnected from IVA
                binding.btnCamera.setEnabled(false);
                binding.btnCamera.setAlpha(0.5f);
            }
        });

        binding.btnCamera.setOnClickListener(v -> {
            handler.onConnectCamera();
        });

        binding.joystickView.setJoystickListener((xPercent, yPercent) -> {
            int direction = -1;

            if (Math.abs(xPercent) > 0.5f || Math.abs(yPercent) > 0.5f) {
                if (Math.abs(xPercent) > Math.abs(yPercent)) {
                    // Horizontal movement
                    if (xPercent < -0.5f) {
                        direction = 2; // Left
                    } else if (xPercent > 0.5f) {
                        direction = 3; // Right
                    }
                } else {
                    // Vertical movement
                    if (yPercent < -0.5f) {
                        direction = 0; // Forward
                    } else if (yPercent > 0.5f) {
                        direction = 1; // Backward
                    }
                }
            }

            if (direction != lastDirection) {
                lastDirection = direction;
                if (direction != -1) {
                    switch (direction) {
                        case 0:
                            handler.onSendCommandBT("%A#");
                            break;
                        case 1:
                            handler.onSendCommandBT("%B#");
                            break;
                        case 2:
                            handler.onSendCommandBT("%C#");
                            break;
                        case 3:
                            handler.onSendCommandBT("%D#");
                            break;
                    }
                }
            }
        });
    }

    @Override
    public void onAttach(@NonNull Context context) {
        super.onAttach(context);
        if (context instanceof FragmentHandler) {
            handler = (FragmentHandler) context;
        } else {
            throw new ClassCastException(context.toString() + " must implement FragmentHandler");
        }
    }
}
