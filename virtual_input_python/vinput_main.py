import netifaces
import os
import socket
import subprocess
import time
from multiprocessing import Process, Queue, Pipe
from threading import Thread

os.system('xhost +')  # solution for python xlib error

from pykeyboard import PyKeyboardEvent
from pymouse import PyMouseEvent, x11, PyMouse

# mapping from mapping.txt and mapped1.txt for mapping from linux keymap to android keymap
mappings = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
            23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
            50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76,
            77, 78, 79, 80, 81, 82, 83, 0, 0, 0, 87, 88, 0, 0, 0, 0, 0, 0, 0, 96, 97, 98, 0, 100, 0, 102, 103, 104, 105,
            106, 107, 108, 109, 110, 111, 0, 113, 114, 115, 116, 117, 0, 119, 0, 0, 0, 0, 0, 0, 0, 0, 128, 129, 130,
            131, 132, 133, 134, 135, 136, 137, 138, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 163, 164, 165, 166]

sign = lambda x: (1, -1)[x < 0]


# this below belongs to seperate process multiprocessing

class Clicker(PyMouseEvent):
    def __init__(self, capture=False):
        PyMouseEvent.__init__(self, capture=capture)
        self.mclicked = 0
        self.MyMouse = None
        if capture: #if capture .. make mouse stay at same place
            self.MyMouse = PyMouse()

    def click(self, x, y, button, press):
        if button == 3:
            self.mclicked += 1
            if self.mclicked > 5:  # if middle clicked 5 times stop capture
                self.stop()

        print('clicked', x, y, button, press)
        if self.capture:  # if mouse has been captured
            sendit = ''
            if press:
                sendit += '3'
            else:
                sendit += '4'
            sendit += chr(button)
            try:
                global currentClient    # socket client
                currentClient.send(sendit.encode())
            except (IndexError, OSError, AttributeError) as e:
                print('sending mouse click failed')
                print(e)

    def move(self, x, y):
        global mouseX, mouseY

        if self.capture:
            if mouseX == -1:
                mouseX = x
                mouseY = y
            self.MyMouse.move(mouseX, mouseY)
            pass
        else:
            mouseX = x
            mouseY = y

    def scroll(self, x, y, vertical, horizontal):
        # print('scroll', x, y, vertical, horizontal)
        if self.capture:
            sendit = '5'
            sendit += chr(vertical + 2)
            try:
                global currentClient
                currentClient.send(sendit.encode())
            except (IndexError, OSError, AttributeError) as e:
                print('sending mouse scroll failed')
                print(e)


def mouseRelative(dx, dy):
    global dispX, dispY, mouseX, mouseY, Mouse, lockKM, currentClient, global_capt, flag1

    if global_capt:

        # print('display={}, {}  :mouse={}, {}'.format(dispX, dispY, mouseX, mouseY))
        # Mouse.move(mouseX, mouseY)
        # print('other window --- >>> ', dx, dy, mouseX, mouseY)
        # sendit = '2' #2678
        if sign(dx) == 1:
            if sign(dy) == 1:
                sendit = '2'
            else:
                sendit = '6'
        else:
            if sign(dy) == 1:
                sendit = '7'
            else:
                sendit = '8'
        sendit += chr(abs(dx)) + chr(abs(dy))
        try:
            currentClient.send(sendit.encode())
        except (IndexError, OSError, AttributeError) as e:
            print('sending mouse move failed')
            print(e)
            pass
    else:
        if mouseX >= dispX - 1:
            print('relative --- >>> ', dx, dy, mouseX, mouseY)
            if dx >= 20:
                print("\n\n--> gone to another side\nmouse stuck\n")
                flag1 = True

    pass


class Typer(PyKeyboardEvent):
    def __init__(self, capture=False):
        PyKeyboardEvent.__init__(self, capture=capture)
        self.escaped = 0
        self.ended = 0

    def tap(self, keycode, character, press):
        if self.capture:
            if character == 'End':
                self.ended += 1
                if self.ended >= 5:  # if end is pressed 5 times release
                    self.stop()

            try:
                if mappings[keycode] is 0:
                    print('no mapping found for ', keycode)
                    return
            except IndexError:
                print('no mapping found for ', keycode)
                return

            sendit = ''
            if press:
                sendit = '1' + chr(mappings[keycode])
            else:
                sendit = '0' + chr(mappings[keycode])
            print('tosend', sendit)
            try:
                global currentClient
                currentClient.send(sendit.encode())
            except (IndexError, OSError, AttributeError) as e:
                print('sending key press failed')
                print(e)
        pass

    def escape(self, event):
        if event.detail == self.lookup_character_keycode('Escape'):
            self.escaped += 1
            if self.escaped >= 5:
                return True
        return False


def check_stop(Q):
    global stopped
    times = time.time()
    while not stopped:
        print('checking for overtime stop')
        if time.time() - times > 0.1:
            print('__________its a overtime so exiting_____')
            Q.put("terminate")
        time.sleep(0.001)
    pass


def clientThreads(client):
    global release
    print("Got a connection")
    msg = 'PSv:Thank you for connecting' + "\r\n"
    client.send(msg.encode())
    try:
        while True:
            msg = client.recv(1024)
            if not msg: break
            msg = str(msg)
            print(address, ' >> ', msg)
            if 'release' in msg:
                release = True
                pass
            msg = 'PSv:received'
            client.sendall(msg.encode())
            time.sleep(0.01)
    except OSError as e:
        print(e)
        pass
    print('closing client', address)
    client.close()
    pass


def main_keyboard(queue, capt, client, selector):
    global currentClient, stopped, mouseX, mouseY, global_capt, flag1
    mouseX = mouseY = -1
    global_capt = capt
    flag1 = False
    stopped = False
    currentClient = client
    C = Typer(capture=capt)
    B = Clicker(capture=capt)

    # import virtual_share_beta_2.connect_manager as connectManager
    import connect_manager as connectManager
    connectManager.set_selector(selector)
    connectManager.set_handler_and_start(relMouse=mouseRelative)

    try:
        C.start()
        B.start()

        if capt:
            while True:
                msg = client.recv(1024)
                if not msg: break
                msg = str(msg)
                print(address, ' >> ', msg)
                if 'release' in msg:
                    break
                msg = 'PSv:received'
                client.sendall(msg.encode())
                time.sleep(0.01)
        else:
            while not flag1:
                time.sleep(0.01)
    except (KeyboardInterrupt, OSError) as e:
        print(e)
    finally:
        thrd = Thread(target=check_stop, args=(queue,), daemon=True)
        thrd.start()
        C.stop()
        try:
            B.stop()
        except x11.X11Error as e:
            print('cant stop mouse')
            print(e)
        stopped = True
        print('closing client')
        client.close()
        connectManager.exit_listener()
        thrd.join()
        queue.put("join")


# multiprocessing upto here

class PrintStuff:
    def __init__(self):
        self.counter = 0

    def print_line(self):
        print('this is in different process')

    def increase_counter(self):
        print('counted to = ', self.counter)
        self.counter += 1


def get_screen_resolution():
    output = subprocess.Popen('xrandr | grep "\*" | cut -d" " -f4', shell=True, stdout=subprocess.PIPE).communicate()[0]
    resolution = output.split()[0].split(b'x')
    return int(resolution[0]), int(resolution[1])


def socket_starter():
    global serverSocket, dispX, dispY, buffer_str, mt, kt, lastkey, selector
    lastkey = buffer_str = ''
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    netifaces.ifaddresses('enp7s0')
    ip = netifaces.ifaddresses('enp7s0')[netifaces.AF_INET][0]['addr']
    # netifaces.ifaddresses('wlp6s0')
    # ip = netifaces.ifaddresses('wlp6s0')[netifaces.AF_INET][0]['addr']
    host = str(ip)
    print('connect clients to', host)
    port = 9818
    serverSocket.bind((host, port))
    serverSocket.listen(21)
    dispX, dispY = get_screen_resolution()
    print('resolution', get_screen_resolution())

    # import virtual_share_beta_2.connect_manager as connectManager
    import connect_manager as connectManager
    connectManager.initialize()
    selector = connectManager.get_selector()
    return


if __name__ == '__main__':
    cwd = os.getcwd()
    socket_starter()
    global serverSocket, selector

    client, address = serverSocket.accept()
    print("Got a connection from %s" % str(address))
    msg = 'PSv:Thank you for connecting' + "\r\n"
    client.send(msg.encode())

    queue = Queue()
    while True:
        cpn = Process(target=main_keyboard, args=(queue, False, client, selector))
        cpn.start()
        got = queue.get()
        print(got)
        if got == "terminate":
            cpn.terminate()
        elif got == "join":
            pass
        cpn.join()
        print('_1-finished_____')

        cpy = Process(target=main_keyboard, args=(queue, True, client, selector))
        cpy.start()
        got = queue.get()
        print(got)
        if got == "terminate":
            cpy.terminate()
        elif got == "join":
            pass
        cpy.join()
        print('_2-finished_____')

# import netifaces
# import os
# import socket
# import subprocess
# import time
# from multiprocessing import Process, Queue, Pipe
# from threading import Thread
#
# os.system('xhost +')  # solution for python xlib error
# from pykeyboard import PyKeyboardEvent
# from pymouse import PyMouseEvent, x11, PyMouse
#
# mappings = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
#             23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49,
#             50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76,
#             77, 78, 79, 80, 81, 82, 83, 0, 0, 0, 87, 88, 0, 0, 0, 0, 0, 0, 0, 96, 97, 98, 0, 100, 0, 102, 103, 104, 105,
#             106, 107, 108, 109, 110, 111, 0, 113, 114, 115, 116, 117, 0, 119, 0, 0, 0, 0, 0, 0, 0, 0, 128, 129, 130,
#             131, 132, 133, 134, 135, 136, 137, 138, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
#             0, 163, 164, 165, 166]
#
# sign = lambda x: (1, -1)[x < 0]
#
#
# # this below belongs to seperate process multiprocessing
#
# class Clicker(PyMouseEvent):
#     def __init__(self, capture=False):
#         PyMouseEvent.__init__(self, capture=capture)
#         self.mclicked = 0
#         self.MyMouse = None
#         if capture:
#             self.MyMouse = PyMouse()
#
#     def click(self, x, y, button, press):
#         if button == 3:
#             self.mclicked += 1
#             if self.mclicked > 5:  # if middle clicked 5 times stop capture
#                 self.stop()
#
#         print('clicked', x, y, button, press)
#         if self.capture:  # if mouse has been captured
#             sendit = ''
#             # sendit = ('3','4')[press]
#             if press:
#                 sendit += '3'
#             else:
#                 sendit += '4'
#             sendit += chr(button)
#             try:
#                 global currentClient
#                 currentClient.send(sendit.encode())
#             except (IndexError, OSError, AttributeError) as e:
#                 print('sending mouse click failed')
#                 print(e)
#
#     def move(self, x, y):
#         global mouseX, mouseY
#
#         if self.capture:
#             if mouseX == -1:
#                 mouseX = x
#                 mouseY = y
#             self.MyMouse.move(mouseX, mouseY)
#             pass
#         else:
#             mouseX = x
#             mouseY = y
#
#     def scroll(self, x, y, vertical, horizontal):
#         # print('scroll', x, y, vertical, horizontal)
#         if self.capture:
#             sendit = '5'
#             sendit += chr(vertical + 2)
#             try:
#                 global currentClient
#                 currentClient.send(sendit.encode())
#             except (IndexError, OSError, AttributeError) as e:
#                 print('sending mouse scroll failed')
#                 print(e)
#
#
# def mouseRelative(dx, dy):
#     global dispX, dispY, mouseX, mouseY, Mouse, lockKM, currentClient, global_capt, flag1
#
#     if global_capt:
#
#         # print('display={}, {}  :mouse={}, {}'.format(dispX, dispY, mouseX, mouseY))
#         # Mouse.move(mouseX, mouseY)
#         # print('other window --- >>> ', dx, dy, mouseX, mouseY)
#         # sendit = '2' #2678
#         if sign(dx) == 1:
#             if sign(dy) == 1:
#                 sendit = '2'
#             else:
#                 sendit = '6'
#         else:
#             if sign(dy) == 1:
#                 sendit = '7'
#             else:
#                 sendit = '8'
#         sendit += chr(abs(dx)) + chr(abs(dy))
#         try:
#             currentClient.send(sendit.encode())
#         except (IndexError, OSError, AttributeError) as e:
#             print('sending mouse move failed')
#             print(e)
#             pass
#     else:
#         if mouseX >= dispX - 1:
#             print('relative --- >>> ', dx, dy, mouseX, mouseY)
#             if dx >= 20:
#                 print("\n\n--> gone to another side\nmouse stuck\n")
#                 flag1 = True
#
#     pass
#
#
# class Typer(PyKeyboardEvent):
#     def __init__(self, capture=False):
#         PyKeyboardEvent.__init__(self, capture=capture)
#         self.escaped = 0
#         self.ended = 0
#
#     def tap(self, keycode, character, press):
#         if self.capture:
#             if character == 'End':
#                 self.ended += 1
#                 if self.ended >= 5:  # if end is pressed 5 times release
#                     self.stop()
#
#             try:
#                 if mappings[keycode] is 0:
#                     print('no mapping found for ', keycode)
#                     return
#             except IndexError:
#                 print('no mapping found for ', keycode)
#                 return
#
#             sendit = ''
#             if press:
#                 sendit = '1' + chr(mappings[keycode])
#             else:
#                 sendit = '0' + chr(mappings[keycode])
#             print('tosend', sendit)
#             try:
#                 global currentClient
#                 currentClient.send(sendit.encode())
#             except (IndexError, OSError, AttributeError) as e:
#                 print('sending key press failed')
#                 print(e)
#         pass
#
#     def escape(self, event):
#         if event.detail == self.lookup_character_keycode('Escape'):
#             self.escaped += 1
#             if self.escaped >= 5:
#                 return True
#         return False
#
#
# def check_stop(Q):
#     global stopped
#     times = time.time()
#     while not stopped:
#         print('checking for overtime stop')
#         if time.time() - times > 0.1:
#             print('__________its a overtime so exiting_____')
#             Q.put("terminate")
#         time.sleep(0.001)
#     pass
#
#
# def clientThreads(client):
#     global release
#     print("Got a connection")
#     msg = 'PSv:Thank you for connecting' + "\r\n"
#     client.send(msg.encode())
#     try:
#         while True:
#             msg = client.recv(1024)
#             if not msg: break
#             msg = str(msg)
#             print(address, ' >> ', msg)
#             if 'release' in msg:
#                 release = True
#                 pass
#             msg = 'PSv:received'
#             client.sendall(msg.encode())
#             time.sleep(0.01)
#     except OSError as e:
#         print(e)
#         pass
#     print('closing client', address)
#     client.close()
#     pass
#
#
# def main_keyboard(queue, capt, client, selector):
#     global currentClient, stopped, mouseX, mouseY, global_capt, flag1
#     mouseX = mouseY = -1
#     global_capt = capt
#     flag1 =False
#     stopped = False
#     currentClient = client
#     C = Typer(capture=capt)
#     B = Clicker(capture=capt)
#
#     # import virtual_share_beta_2.connect_manager as connectManager
#     import connect_manager as connectManager
#     connectManager.set_selector(selector)
#     connectManager.set_handler_and_start(relMouse=mouseRelative)
#
#     try:
#         C.start()
#         B.start()
#
#         if capt:
#             while True:
#                 msg = client.recv(1024)
#                 if not msg: break
#                 msg = str(msg)
#                 print(address, ' >> ', msg)
#                 if 'release' in msg:
#                     break
#                 msg = 'PSv:received'
#                 client.sendall(msg.encode())
#                 time.sleep(0.01)
#         else:
#             while not flag1:
#                 time.sleep(0.01)
#     except (KeyboardInterrupt, OSError) as e:
#         print(e)
#     finally:
#         thrd = Thread(target=check_stop, args=(queue,), daemon=True)
#         thrd.start()
#         C.stop()
#         try:
#             B.stop()
#         except x11.X11Error as e:
#             print('cant stop mouse')
#             print(e)
#         stopped = True
#         print('closing client')
#         client.close()
#         thrd.join()
#         queue.put("join")
#
#
# # multiprocessing upto here
#
# class PrintStuff:
#     def __init__(self):
#         self.counter = 0
#
#     def print_line(self):
#         print('this is in different process')
#
#     def increase_counter(self):
#         print('counted to = ', self.counter)
#         self.counter += 1
#
#
# def get_screen_resolution():
#     output = subprocess.Popen('xrandr | grep "\*" | cut -d" " -f4', shell=True, stdout=subprocess.PIPE).communicate()[0]
#     resolution = output.split()[0].split(b'x')
#     return int(resolution[0]), int(resolution[1])
#
#
# def socket_starter():
#     global serverSocket, dispX, dispY, buffer_str, mt, kt, lastkey, selector
#     lastkey = buffer_str = ''
#     serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     netifaces.ifaddresses('enp7s0')
#     ip = netifaces.ifaddresses('enp7s0')[netifaces.AF_INET][0]['addr']
#     # netifaces.ifaddresses('wlp6s0')
#     # ip = netifaces.ifaddresses('wlp6s0')[netifaces.AF_INET][0]['addr']
#     host = str(ip)
#     print('connect clients to', host)
#     port = 9818
#     serverSocket.bind((host, port))
#     serverSocket.listen(21)
#     dispX, dispY = get_screen_resolution()
#     print('resolution', get_screen_resolution())
#
#     # import virtual_share_beta_2.connect_manager as connectManager
#     import connect_manager as connectManager
#     connectManager.initialize()
#     selector = connectManager.get_selector()
#     return
#
#
# if __name__ == '__main__':
#     cwd = os.getcwd()
#
#     socket_starter()
#     # global serverSocket, selector
#
#     client, address = serverSocket.accept()
#     print("Got a connection from %s" % str(address))
#     msg = 'PSv:Thank you for connecting' + "\r\n"
#     client.send(msg.encode())
#
#     queue = Queue()
#     while True:
#         cpn = Process(target=main_keyboard, args=(queue, False, client, selector))
#         cpn.start()
#         got = queue.get()
#         print(got)
#         if got == "terminate":
#             cpn.terminate()
#         elif got == "join":
#             pass
#         cpn.join()
#         print('_1-finished_____')
#
#         cpy = Process(target=main_keyboard, args=(queue, True, client, selector))
#         cpy.start()
#         got = queue.get()
#         print(got)
#         if got == "terminate":
#             cpy.terminate()
#         elif got == "join":
#             pass
#         cpy.join()
#         print('_2-finished_____')
