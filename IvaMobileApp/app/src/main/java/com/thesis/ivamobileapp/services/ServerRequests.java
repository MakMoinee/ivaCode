package com.thesis.ivamobileapp.services;

import android.content.Context;

import com.github.MakMoinee.library.interfaces.DefaultBaseListener;
import com.github.MakMoinee.library.interfaces.LocalVolleyRequestListener;
import com.github.MakMoinee.library.models.LocalVolleyRequestBody;
import com.github.MakMoinee.library.services.LocalVolleyRequest;

public class ServerRequests extends LocalVolleyRequest {
    String serverIP;

    public ServerRequests(Context mContext, String s) {
        super(mContext);
        this.serverIP = s;
    }

    public void sendCommand(String path, DefaultBaseListener listener) {
        LocalVolleyRequestBody body = new LocalVolleyRequestBody.LocalVolleyRequestBodyBuilder()
                .setUrl(String.format("http://%s%s", this.serverIP, path))
                .build();
        this.sendTextPlainRequest(body, new LocalVolleyRequestListener() {
            @Override
            public void onSuccessString(String response) {
                listener.onSuccess("success");
            }

            @Override
            public void onError(Error error) {
                listener.onError(error);
            }
        });
    }
}
