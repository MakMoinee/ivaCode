package com.thesis.ivamobileapp.models;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class SettingItems {
    private String settingName;
    private int settingImg;


    public SettingItems(SettingItemBuilder builder) {
        this.settingName = builder.settingName;
        this.settingImg = builder.settingImg;
    }

    public static class SettingItemBuilder {

        private String settingName;
        private int settingImg;

        public SettingItemBuilder setSettingName(String settingName) {
            this.settingName = settingName;
            return this;
        }

        public SettingItemBuilder setSettingImg(int settingImg) {
            this.settingImg = settingImg;
            return this;
        }

        public SettingItems build() {
            return new SettingItems(this);
        }
    }
}
