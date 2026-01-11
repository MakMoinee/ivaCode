package com.thesis.ivamobileapp.uifragments;

import android.content.Context;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.thesis.ivamobileapp.databinding.FragmentHomeBinding;
import com.thesis.ivamobileapp.interfaces.FragmentHandler;

public class HomeFragment extends Fragment {

    FragmentHomeBinding binding;
    FragmentHandler handler;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentHomeBinding.inflate(LayoutInflater.from(requireContext()), container, false);
        setListeners();
        return binding.getRoot();
    }

    private void setListeners() {
        binding.btnTop.setOnClickListener(v -> {
            handler.onSendCommandBT("%A#");
            Toast.makeText(requireContext(), "Successfully sent forward command to iva", Toast.LENGTH_SHORT).show();
        });
        binding.btnDown.setOnClickListener(v -> {
            handler.onSendCommandBT("%B#");
            Toast.makeText(requireContext(), "Successfully sent backward command to iva", Toast.LENGTH_SHORT).show();
        });
        binding.btnLeft.setOnClickListener(v -> {
            handler.onSendCommandBT("%C#");
            Toast.makeText(requireContext(), "Successfully sent left command to iva", Toast.LENGTH_SHORT).show();
        });
        binding.btnRight.setOnClickListener(v -> {
            handler.onSendCommandBT("%D#");
            Toast.makeText(requireContext(), "Successfully sent right command to iva", Toast.LENGTH_SHORT).show();
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
