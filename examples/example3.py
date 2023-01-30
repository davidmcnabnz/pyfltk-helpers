#!/usr/bin/env python3
"""
example3.py

Splits into 2 processes, with FLTK GUI in one, and an asyncio process in the other,
and the two processes interacting over inter-process Pipe

This overcomes the issue of FLTK hogging the GIL and blocking asyncio event loops.
By running the GUI and the asyncio-based server in separate processes, talking over the Pipe,
FLTK no longer interferes with any event loops. The GUI passes user events to the server, and
the server passes events to the GUI.
"""
import sys, os
import datetime
import traceback
import pprint

import asyncio

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import Process, Pipe

import fltk

try:
    # first, attempt to import the helpers module from the python modules directory
    import fltkHelpers
except ImportError:
    # failed, so monkey-patch import paths to include the local helpers module directory
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    HELPERS_PARENT_DIR = os.path.dirname(os.path.join(os.path.dirname(THIS_DIR), "fltkHelpers"))
    if HELPERS_PARENT_DIR not in sys.path:
        sys.path.append(HELPERS_PARENT_DIR)

from fltkHelpers.cursor import FLPoint
from fltkHelpers.constants import lookupConstant, lookupEvent

winOrg = FLPoint(100, 50)
winSize = FLPoint(300, 140)
btnSize = FLPoint(80, 20)

class MyServer:

    def __init__(self, pipe):
        self.pipe = pipe
        pass

    async def arun(self):
        self.qQuit = asyncio.Queue()
        self.task_talkToGUI = asyncio.create_task(self.task_talkToGUI())
        self.task_ticker = asyncio.create_task(self.task_ticker())
        await self.qQuit.get()

    async def task_talkToGUI(self):
        self.isRunning = True
        self.threadPool = ThreadPoolExecutor()
        self.loop = asyncio.get_running_loop()
        print("MyServer: starting")
        while self.isRunning:
            item = await self.readFromGUI()
            if item is None:
                self.isRunning = False
                print("MyServer: got None from GUI, so quitting")
                await self.qQuit.put(None)
                self.task_ticker.cancel()
                break
            elif item['input'] == 'quit':
                # this demonstrates the server telling the GUI to quit
                print("Got 'quit' from GUI, telling GUI to close")
                await self.writeToGUI(None)
                await self.qQuit.put(None)
                return

            print("MyServer: got %s" % str(item))
            reply = {'type': 'ack', 'data': item}
            print("MyServer: replying with %s" % str(reply))
            await self.writeToGUI(reply)
            print("MyServer: reply sent")

    async def task_ticker(self):
        while self.isRunning:
            print("task_ticker: event loop is live")
            await asyncio.sleep(5)

    async def readFromGUI(self):
        item = await (self.loop.run_in_executor(self.threadPool, self.pipe.recv))
        return item

    async def writeToGUI(self, item):
        await (self.loop.run_in_executor(self.threadPool, self.pipe.send, item))

    def run(self):
        print("MyServer.run: running in async")
        try:
            asyncio.run(self.arun())
        except:
            traceback.print_exc()

class MyGUI:

    def __init__(self, pipe):

        self.pipe = pipe
        self.createGUI()

    def createGUI(self):

        # origin of window on the screen
        winOrg = FLPoint(100, 50)

        # size of the window
        winSize = FLPoint(400, 300)

        # standard size of buttons we wish to place
        btnSize = FLPoint(80, 20)

        # now place the window on the screen
        self.win, right, down = winOrg.Fl_Window(winSize, "example3.py")

        # now create first 'cursor' object to start the layout within this window
        # and apply an offset to provide room for text field label and some vertical pad
        fldOrg = winOrg.topLeft() + (80, 20)

        # place a write-only field, plus a button
        self.fldIn, right, down = fldOrg.Fl_Input((180, 20), "Input:")
        self.fldOutBuf = fltk.Fl_Text_Buffer()
        self.fldOut, right, down = (down + 40).Fl_Text_Display((250, 150), "Output:")
        self.fldOut.buffer(self.fldOutBuf)
        self.btnSend, right, down = down.Fl_Button(btnSize, "Send")
        self.btnSend.callback(self.on_btnSend)

        # get a cursor for adding n widgets of given height to bottom row of window
        bottomOrg = winSize.bottomCentre(btnSize, 1)

        # now we can place that bottom button
        self.btnQuit, _, _ = bottomOrg.Fl_Button(btnSize, "Quit")
        self.btnQuit.callback(self.on_btnQuit)

        fltk.Fl.add_idle(self.on_idle)

        self.win.resizable()

        self.win.show()
        self.win.end()
        self.win.callback(self.on_close)

    def on_btnSend(self, *args):
        """
        callback for when user clicks the 'Update' button
        """
        txt = self.fldIn.value()
        print("on_btnSend: got text %s" % txt)
        item = {
            'time': datetime.datetime.now().strftime("%H:%M:%S"),
            'input': txt,
            }
        print("on_btnSend: sending item %s" % str(item))
        self.pipe.send(item)
        print("on_btnSend: done")

    def on_idle(self, *args):
        while self.pipe.poll(0.1):
            item = self.pipe.recv()
            print("GUI: on_idle: got %s" % repr(item))
            self.on_msgFromServer(item)

    def on_msgFromServer(self, item):
        if item is None:
            print("GUI: got None from server, so we need to close")
            self.close()
        else:
            fmt = pprint.pformat(item, indent=2, width=30)
            pprint.pprint(item)
            self.fldOutBuf.remove(0, self.fldOutBuf.length())
            self.fldOutBuf.insert(0, fmt)

    def on_btnQuit(self, *args):
        """
        callback for when user clicks the 'Quit' button
        """
        print("on_btnQuit: quitting")
        self.on_close()

    def on_close(self, *args):
        print("on_close: quitting")
        self.close()

    def close(self):
        print("close: shutting down UI, sending None to server to make it quit")
        self.pipe.send(None)
        self.win.hide()

    @classmethod
    def run(cls, pipe):
        inst = cls(pipe)
        print("MyGUI.run(): starting")
        fltk.Fl.run()
#        inst.close()
        print("MyGUI.run(): back from fltk.Fl_run()")

def main():
    parent_conn, child_conn = Pipe()
    p = Process(target=MyGUI.run, args=(child_conn,))
    p.start()

    print("main: creating MyServer")
    app = MyServer(parent_conn)
    print("main: running MyServer instance")
    app.run()
    print("main: back from MyServer")

    #p.join()


if __name__ == '__main__':
    main()

