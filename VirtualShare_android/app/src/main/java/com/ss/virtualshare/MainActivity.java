package com.ss.virtualshare;

import android.app.Activity;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.util.DisplayMetrics;
import android.view.Display;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Socket;

public class MainActivity extends Activity implements View.OnClickListener {

    final static int KEYUP = 0;
    final static int KEYDOWN = 1;
    final static int MOUSEMOVE = 2;
    final static int MOUSEDOWN = 3;
    final static int MOUSEUP = 4;
    final static int MOUSEWHEEL = 5;

    String ip = "192.168.1.50";

    OutputStream output;
    InputStream input;
    Socket socket = null;
    String temp, temp1, temp2;
    int nullRevc = 0, inputLen = 0, height, width, xx = 0, yy = 0, big = 0, small = 0;


    Button clearbt, keyPress, ipButton;
    EditText text, ipAddress;
    TextView textView;
    ScrollView scrollView;
    HandleInject handler;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        text = (EditText) findViewById(R.id.editText2);
        ipAddress = (EditText) findViewById(R.id.serverIP);
        clearbt = (Button) findViewById(R.id.button);
        ipButton = (Button) findViewById(R.id.ipbutton);
        keyPress = (Button) findViewById(R.id.button2);
        textView = (TextView) findViewById(R.id.textView);
        scrollView = (ScrollView) findViewById(R.id.scrollv);


//        Injection.setPermissionsForInputDevice();
        clearbt.setOnClickListener(this);
        keyPress.setOnClickListener(this);
        ipButton.setOnClickListener(this);

        new Thread(receiverThread).start();

        DisplayMetrics displayMetrics = new DisplayMetrics();
        getWindowManager().getDefaultDisplay().getMetrics(displayMetrics);
        height = displayMetrics.heightPixels;
        width = displayMetrics.widthPixels;
        big = width;
        small = height;

        handler = new HandleInject(getWindowManager().getDefaultDisplay());
//        LogMe("H: "+height+ " W: "+width);




        SharedPreferences sp = getSharedPreferences("my_storage", Activity.MODE_PRIVATE);
        ip = sp.getString("storedIP", ip);
        ipAddress.setText(ip);

    }


    @Override
    public void onClick(View v) {
        if (v.getId() == clearbt.getId()) {
            text.setText("");
            textView.setText("");
        } else if (v.getId() == keyPress.getId()) {
            new Thread(new Runnable() {
                @Override
                public void run() {

                    for (int i = 0; i < 10; i++) {
                        runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                handler.mouseMove(50, 50);
                            }
                        });

                        try {
                            Thread.sleep(1000);
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                    }
                }
            }).start();
        } else if (v.getId() == ipButton.getId()) {
            SharedPreferences sp = getSharedPreferences("my_storage", Activity.MODE_PRIVATE);
            SharedPreferences.Editor editor = sp.edit();
            ip = ipAddress.getText().toString();
            editor.putString("storedIP", ip);
            editor.commit();

        }
    }

    void LogMe(final String string) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                textView.append(string);
            }
        });
    }

    Runnable receiverThread = new Runnable() {
        @Override
        public void run() {
            while (true) {
                try {
                    socket = new Socket(ip, 9818);
                    LogMe("->" + "connected to: " + ip + "\n");
                    input = socket.getInputStream();
                    output = socket.getOutputStream();
                    nullRevc = 0;
                    output.write(9818);
                    while (socket.isConnected() && nullRevc < 10) {
                        byte[] bts = new byte[256];
                        inputLen = input.read(bts);
                        temp = new String(bts).trim();
                        for (int i = 0; i < inputLen; ) {
                            switch (bts[i++]) {
                                case '0':
                                    handler.keyUp((int) bts[i++]);
                                    break;
                                case '1':
                                    handler.keyDown((int) bts[i++]);
                                    break;
                                case '2':
//                                    LogMe("MouseMove detected "+(char)bts[i-1]+"with codes"+bts[i]+" "+ bts[i+1]+"\n");
                                    handler.mouseMove((int) bts[i], (int) bts[i + 1]);
                                    i += 2;
                                    break;
                                case '6':
                                    handler.mouseMove((int) bts[i], -(int) bts[i + 1]);
                                    i += 2;
                                    break;
                                case '7':
                                    handler.mouseMove(-(int) bts[i], (int) bts[i + 1]);
                                    i += 2;
                                    break;
                                case '8':
                                    handler.mouseMove(-(int) bts[i], -(int) bts[i + 1]);
                                    i += 2;
                                    break;
                                case '3':
                                    handler.mouseDown((int) bts[i++]);
                                    break;
                                case '4':
                                    handler.mouseUp((int) bts[i++]);
                                    break;
                                case '5':
                                    if ((int) bts[i++] == 1)
                                        handler.mouseWheel(-1);
                                    else handler.mouseWheel(1);
                                    break;
                                default:
                                    if (temp.startsWith("PSv:")) {
                                        inputLen = 0;
                                        LogMe(temp + "\n");
                                        break;
                                    }
                                    LogMe("command not recognised : " + (int) bts[i - 1] + "=" + (char) bts[i - 1] + "\n");
                                    break;
                            }
                        }

//                        System.out.println("->R :" + inputLen + " " + temp);
//                        if (!temp.equals(""))
//                            LogMe("->[" + inputLen + "|" + temp + "]  ");
//                        else nullRevc++;
                        if (temp.equals("")) nullRevc++;


                    }
                    socket.close();
                    socket = null;
                    LogMe("disconnected from server\n");
                } catch (ClassCastException | NullPointerException | IOException e) {
                    e.printStackTrace();
                }


                try {
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        }
    };


    class HandleInject {

        private int injectCode = 99, tmp1, tmp2, tmp3, tmp4, tmp5, tmp6, prevRot = 1;
        private boolean run = true, wait = true, waitM = true;
        Display display;
        private Runnable runMe = new Runnable() {
            @Override
            public void run() {
                Injection.setPermissionsForInputDevice();
                injectEnable();
                while (run) {
                    switch (injectCode) {
                        case KEYUP:
//                            Random random = new Random();
//                            char a = 'a';
//                            Injection.keydown((int) a, 1);
//                            Injection.keyup((int) a, 0);
//                            Injection.movemouse(tmp1, tmp2);
//                            tmp1 = random.nextInt() % 30;
//                            tmp2 = random.nextInt() % 30;
//                            random.nextInt();
                            Injection.keyup2(tmp1);
                            break;
                        case KEYDOWN:
                            Injection.keydown2(tmp1);
                            break;
                        case MOUSEMOVE:
                            Injection.movemouse(tmp1, tmp2);
                            break;
                        case MOUSEDOWN:
                            Injection.mousedown(tmp1);
                            break;
                        case MOUSEUP:
                            Injection.mouseup(tmp1);
                            break;
                        case MOUSEWHEEL:
                            Injection.mousewheel(0, tmp1);
                            break;
                        default:
                            break;
                    }
                    wait = true;
                    while (wait) {
                        try {
                            Thread.sleep(0, 10000);
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                    }

                }
                injectDisable();
            }
        };
        private Runnable mouseManager = new Runnable() {
            @Override
            public void run() {
                while (run) {
                    tmp3 = display.getRotation();

                    if (tmp3 != prevRot) { // if rotation has changed
                        if (tmp3 == 0 || tmp3 == 2) { // set appropriate height and width
                            height = big;
                            width = small;
                        } else if (tmp3 == 1 || tmp3 == 3) {
                            height = small;
                            width = big;
                        }

                        if (prevRot == (tmp3 + 1) % 4) { //keep the position of mouse constant
                            tmp4 = xx;
                            xx = width - yy;
                            yy = tmp4;
                        } else if (prevRot == (tmp3 + 2) % 4) {
                            tmp4 = xx;
                            xx = width - tmp4;
                            tmp4 = yy;
                            yy = height - tmp4;
                        } else if (prevRot == (tmp3 + 3) % 4) {
                            tmp4 = yy;
                            yy = height - xx;
                            xx = tmp4;
                        }

                    }
                    prevRot = tmp3;

                    if (xx == 0 && tmp5 <= -20) {
                        try {
                            LogMe(String.format("Releasing mouse as x=%d y=%d dx=%d, dy=%d\n", xx, yy, tmp5, tmp6));
                            output.write("release".getBytes());
                        } catch (IOException e) {
                            LogMe("Could not release Keyboard and Mouse");
                            e.printStackTrace();
                        }
                    }
                    xx += tmp5;
                    yy += tmp6;
                    tmp5 = tmp6 = 0;
                    if (xx > width) xx = width;
                    else if (xx < 0) xx = 0;
                    if (yy > height) yy = height;
                    else if (yy < 0) yy = 0;

//                    LogMe("X: " + xx + " Y:" + yy+ " Rot:"+tmp3+" ");

                    waitM = true;
                    while (waitM) {
                        try {
                            Thread.sleep(0, 10000);
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                    }
                }
            }
        };

        private Thread injectThread = new Thread(runMe);
        private Thread mouseThread = new Thread(mouseManager);


        public HandleInject(Display defaultDisplay) {
            this.display = defaultDisplay;
            injectThread.start();
            mouseThread.start();
        }

        public void injectEnable() {
            Injection.startInjection("VsendDev");
            Injection.movemouse(-2000, -2000);
        }

        public void injectDisable() {
            Injection.stopInjection();
        }

        public void keyUp(int key) {
            while (!wait) ;
            injectCode = KEYUP;
            tmp1 = key;
            wait = false;

        }

        public void keyDown(int key) {
            while (!wait) ;
            injectCode = KEYDOWN;
            tmp1 = key;
            wait = false;
        }

        public void mouseMove(int x, int y) {
            while (!wait) ;
            injectCode = MOUSEMOVE;
            tmp5 = tmp1 = x;
            tmp6 = tmp2 = y;
            waitM = wait = false;

        }

        public void mouseDown(int buttonNo) {
            while (!wait) ;
            injectCode = MOUSEDOWN;
            tmp1 = buttonNo;
            wait = false;
        }

        public void mouseUp(int buttonNo) {
            while (!wait) ;
            injectCode = MOUSEUP;
            tmp1 = buttonNo;
            wait = false;
        }

        public void mouseWheel(int upDirection) {
            while (!wait) ;
            injectCode = MOUSEWHEEL;
            tmp1 = upDirection;
            wait = false;
        }

    }
}
