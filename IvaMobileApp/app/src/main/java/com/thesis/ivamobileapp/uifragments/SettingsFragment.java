package com.thesis.ivamobileapp.uifragments;

import android.content.Context;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.thesis.ivamobileapp.R;
import com.thesis.ivamobileapp.adapters.SettingsAdapter;
import com.thesis.ivamobileapp.databinding.FragmentSettingsBinding;
import com.thesis.ivamobileapp.interfaces.FragmentHandler;
import com.thesis.ivamobileapp.models.SettingItems;

import java.util.ArrayList;
import java.util.List;

public class SettingsFragment extends Fragment {
    FragmentSettingsBinding binding;
    SettingsAdapter adapter;
    List<SettingItems> settingItemList = new ArrayList<>();
    FragmentHandler handler;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentSettingsBinding.inflate(LayoutInflater.from(requireContext()), container, false);
        buildSettings();
        updateAdapter();
        return binding.getRoot();
    }

    private void updateAdapter() {
        if (settingItemList.size() > 0) {
            adapter = new SettingsAdapter(requireContext(), settingItemList, settingName -> {
                if (settingName != null) {
                    switch (settingName) {
                        case "Connect Bluetooth":
                            handler.onConnectBT();
                            break;
                    }
                }
            });
        }
    }

    private void buildSettings() {
        String settingItem1 = "Connect Bluetooth";
        SettingItems items = new SettingItems.SettingItemBuilder()
                .setSettingName(settingItem1)
                .setSettingImg(R.drawable.ic_bt)
                .build();
        settingItemList.add(items);
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
