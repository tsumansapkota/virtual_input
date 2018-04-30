import threading

from evdev import InputDevice, categorize, ecodes
from selectors import DefaultSelector, EVENT_READ

dx = 0
dy = 0
handlerFunc = None
global runLooper
runLooper = True

def initialize():
    global selector
    import glob
    devices = []
    events = glob.glob("/dev/input/event*")
    for eventDev in events:
        dev = InputDevice(eventDev)
        print(dev)
        if 'mouse' in dev.name.lower() or 'touchpad' in dev.name.lower():
            devices.append(dev)

    print(devices)
    selector = DefaultSelector()

    # mouse = InputDevice('/dev/input/event8')
    # keybd = InputDevice('/dev/input/event18')
    for dev in devices:
        selector.register(dev, EVENT_READ)


def get_selector():
    global selector
    return selector


def set_selector(_selector):
    global selector
    selector = _selector


def set_handler(relMouse):
    global handlerFunc
    handlerFunc = relMouse

def exit_listener():
    global runLooper, thisThrd
    runLooper=False
    thisThrd.join()




def looper():
    global dx, dy, runLooper
    while runLooper:
        for key, mask in selector.select():
            device = key.fileobj
            for event in device.read():
                # print(event)
                # print(categorize(event))
                if event.type == 2:
                    if event.code == 0:
                        dx = event.value
                    elif event.code == 1:
                        dy = event.value
                if event.type == 0 and event.code == 0:
                    handlerFunc(dx, dy)
                    dx = dy = 0
                '''
                relativex code=0 ,type=2, val
                rely      code=1 ,type=2, val
                '''


def start():
    global  thisThrd
    thisThrd = threading.Thread(target=looper)
    thisThrd.start()


def set_handler_and_start(relMouse):
    global handlerFunc, thisThrd
    handlerFunc = relMouse
    thisThrd = threading.Thread(target=looper)
    thisThrd.start()