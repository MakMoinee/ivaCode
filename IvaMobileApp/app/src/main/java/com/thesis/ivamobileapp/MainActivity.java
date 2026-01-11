package com.thesis.ivamobileapp;

import android.annotation.SuppressLint;
import android.app.ProgressDialog;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.view.MenuItem;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentTransaction;
import androidx.navigation.NavController;
import androidx.navigation.Navigation;
import androidx.navigation.ui.NavigationUI;

import com.google.android.material.navigation.NavigationBarView;
import com.thesis.ivamobileapp.databinding.ActivityMainBinding;
import com.thesis.ivamobileapp.interfaces.FragmentHandler;

import java.io.IOException;
import java.io.OutputStream;
import java.util.Set;
import java.util.UUID;

public class MainActivity extends AppCompatActivity implements FragmentHandler {

    ActivityMainBinding binding;
    private NavController navController;
    BluetoothAdapter bluetoothAdapter;
    BluetoothSocket bluetoothSocket;
    BluetoothDevice ivaCarDevice;
    ProgressDialog progressDialog;
    OutputStream outputStream;

    private static final UUID UUID_SERIAL_PORT = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");
    private static final String DEVICE_NAME = "HC-06";  // Replace with your module's Bluetooth name


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());
        navController = Navigation.findNavController(MainActivity.this, R.id.mainFragment);
        NavigationUI.setupWithNavController(binding.bottomNav, navController);
        bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        if (bluetoothAdapter == null) {
            Toast.makeText(this, "Bluetooth not supported on this device", Toast.LENGTH_LONG).show();
            finish();
        }
        setListeners();
    }

    private void setListeners() {
        binding.bottomNav.setOnItemSelectedListener(new NavigationBarView.OnItemSelectedListener() {
            @SuppressLint("NonConstantResourceId")
            @Override
            public boolean onNavigationItemSelected(@NonNull MenuItem item) {
                if (item.getItemId() == R.id.nav_home) {
                    navController.navigate(R.id.nav_home);
                } else if (item.getItemId() == R.id.nav_settings) {
                    navController.navigate(R.id.nav_settings);
                }
                return false;
            }
        });
    }


    private void connectToRobotCar() {
        progressDialog = ProgressDialog.show(MainActivity.this, "Connecting", "Please wait...", true);

        new Handler().postDelayed(new Runnable() {
            @Override
            public void run() {
                if (ActivityCompat.checkSelfPermission(MainActivity.this, android.Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
                    // Permission not granted, request it
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                        // Android 12 and above require runtime permission check for Bluetooth
                        ActivityCompat.requestPermissions(MainActivity.this,
                                new String[]{android.Manifest.permission.BLUETOOTH_CONNECT},
                                1);
                    }
                } else {
                }
                Set<BluetoothDevice> pairedDevices = bluetoothAdapter.getBondedDevices();

                if (pairedDevices.size() > 0) {
                    for (BluetoothDevice device : pairedDevices) {
                        if (DEVICE_NAME.equals(device.getName())) {
                            ivaCarDevice = device;
                            break;
                        }
                    }
                }

                if (ivaCarDevice != null) {
                    try {
                        bluetoothSocket = ivaCarDevice.createRfcommSocketToServiceRecord(UUID_SERIAL_PORT);
                        bluetoothSocket.connect();
                        outputStream = bluetoothSocket.getOutputStream();
                        Toast.makeText(MainActivity.this, "Connected to IVA", Toast.LENGTH_SHORT).show();

                        sendCommand("%Z#");
                    } catch (IOException e) {
                        Toast.makeText(MainActivity.this, "Failed to connect to IVA", Toast.LENGTH_SHORT).show();
                    }
                } else {
                    Toast.makeText(MainActivity.this, "IVA not found. Make sure it is paired.", Toast.LENGTH_SHORT).show();
                }

                progressDialog.dismiss();
            }
        }, 2000);  // Delay for 2 seconds to simulate connection time
    }

    private void sendCommand(String command) {
        if (outputStream != null) {
            try {
                outputStream.write(command.getBytes());
//                Toast.makeText(this, "Command sent: " + command, Toast.LENGTH_SHORT).show();
            } catch (IOException e) {
                e.printStackTrace();
                Toast.makeText(this, "Failed to send command", Toast.LENGTH_SHORT).show();
            }
        } else {
            Toast.makeText(this, "Not connected to IVA", Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    public void onHome() {
        navController.navigate(R.id.nav_home);
    }

    @Override
    public void onSettings() {
        navController.navigate(R.id.nav_settings);
    }

    @Override
    public void onConnectBT() {
        connectToRobotCar();
    }
}