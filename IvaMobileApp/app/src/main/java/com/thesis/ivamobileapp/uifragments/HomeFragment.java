package com.thesis.ivamobileapp.uifragments;

import android.content.Context;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AlertDialog;
import androidx.fragment.app.Fragment;

import com.thesis.ivamobileapp.databinding.DialogAddCamIpBinding;
import com.thesis.ivamobileapp.databinding.FragmentHomeBinding;
import com.thesis.ivamobileapp.interfaces.FragmentHandler;
import com.thesis.ivamobileapp.preference.CameraPref;
import com.thesis.ivamobileapp.views.JoyStickView;

public class HomeFragment extends Fragment {

    FragmentHomeBinding binding;
    FragmentHandler handler;
    private int lastDirection = -1; // -1: none, 0: forward, 1: backward, 2: left, 3: right
    private boolean isConnected = false; // Mock connection state
    private boolean isFollowMode = false;

    DialogAddCamIpBinding dialogAddCamIpBinding;
    AlertDialog mDialog;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentHomeBinding.inflate(LayoutInflater.from(requireContext()), container, false);
        setListeners();
        checkCameraEnable();
        return binding.getRoot();
    }

    private void checkCameraEnable() {
        String ip = new CameraPref(requireContext()).getStringItem("ip");
        if (ip != null && !ip.isEmpty()) {
            binding.btnCamera.setEnabled(true);
            binding.btnCamera.setAlpha(1);
        } else {
            binding.btnCamera.setEnabled(false);
            binding.btnCamera.setAlpha(0.5F);

        }
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

        binding.btnSetIP.setOnClickListener(view -> {
            AlertDialog.Builder mBuilder = new AlertDialog.Builder(requireContext());
            dialogAddCamIpBinding = DialogAddCamIpBinding.inflate(LayoutInflater.from(requireContext()), null, false);
            mBuilder.setView(dialogAddCamIpBinding.getRoot());
            setDialogListeners();
            mDialog = mBuilder.create();
            mDialog.show();
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

    private void setDialogListeners() {
        dialogAddCamIpBinding.btnSave.setOnClickListener(v -> {
            String ip = dialogAddCamIpBinding.editIP.getText().toString().trim();
            String serverIP = dialogAddCamIpBinding.editServerIP.getText().toString().trim();
            if (serverIP.isEmpty() || ip.isEmpty()) {
                Toast.makeText(requireContext(), "Please Don't Leave Empty Fields", Toast.LENGTH_SHORT).show();
            } else {
                handler.saveCameraIP(ip, serverIP);
                Toast.makeText(requireContext(), "Successfully Saved Camera IP", Toast.LENGTH_SHORT).show();
                binding.btnCamera.setEnabled(true);
                binding.btnCamera.setAlpha(1);
                mDialog.dismiss();
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
