# virtual_input
Share Linux PC mouse and keyboard input to android device

Anyone intrested (and doesnt understand the code) can create a issue,
I will document the code for your understanding.


## About
This program is built using python(Ubuntu) on desktop side
and Java & C++ (Android) on smartphone side

### Python usage:- 
1. record mouse and keyboard events
2. communicate with android client via socket
3. block mouse and keyboard input while they are being shared

### Java/C++ usage:-
1. Java - communicate with desktop and receive input events
2. C++ - create virtual input device (requres root permission) and execute received events natively.
