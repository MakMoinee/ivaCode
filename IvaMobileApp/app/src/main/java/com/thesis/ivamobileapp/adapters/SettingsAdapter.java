package com.thesis.ivamobileapp.adapters;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.thesis.ivamobileapp.R;
import com.thesis.ivamobileapp.interfaces.SettingsListener;
import com.thesis.ivamobileapp.models.SettingItems;

import java.util.List;

public class SettingsAdapter extends RecyclerView.Adapter<SettingsAdapter.ViewHolder> {
    Context mContext;
    List<SettingItems> list;
    SettingsListener listener;


    public SettingsAdapter(Context mContext, List<SettingItems> list, SettingsListener l) {
        this.mContext = mContext;
        this.list = list;
        this.listener = l;
    }

    @NonNull
    @Override
    public SettingsAdapter.ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View mView = LayoutInflater.from(mContext).inflate(R.layout.item_settings, parent, false);
        return new ViewHolder(mView);
    }

    @Override
    public void onBindViewHolder(@NonNull SettingsAdapter.ViewHolder holder, int position) {
        SettingItems item = list.get(position);
        holder.settingName.setText(item.getSettingName());
        holder.imgSettings.setImageResource(item.getSettingImg());
        holder.itemView.setOnClickListener(v -> listener.onClick(item.getSettingName()));
    }

    @Override
    public int getItemCount() {
        return list.size();
    }

    public class ViewHolder extends RecyclerView.ViewHolder {
        TextView settingName;
        ImageView imgSettings;

        public ViewHolder(@NonNull View itemView) {
            super(itemView);
            settingName = itemView.findViewById(R.id.txtSettingName);
            imgSettings = itemView.findViewById(R.id.imgSettings);
        }
    }
}
