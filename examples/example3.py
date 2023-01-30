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

from fltkHelpers.cursor import FLCursor
from fltkHelpers.constants import lookupConstant, lookupEvent

winOrg = FLCursor(100, 50)
winSize = FLCursor(300, 140)
btnSize = FLCursor(80, 20)

class QuitException(Exception):
    pass

class Server:

    def __init__(self, pipe):
        self.pipe = pipe
        pass

    async def task_listenToGUI(self):
        self.isRunning = True
        self.threadPool = ThreadPoolExecutor()
        self.loop = asyncio.get_running_loop()
        print("Server: starting")
        while self.isRunning:
            item = await self.readFromGUI()
            try:
                await self.on_msgFromGUI(item)
            except QuitException:
                break

    async def on_msgFromGUI(self, item):

        if item is None:
            self.isRunning = False
            print("Server: got None from GUI, so quitting")
            await self.qQuit.put(None)
            self.task_ticker.cancel()
            raise QuitException

        elif item['input'] == 'quit':
            # this demonstrates the server telling the GUI to quit
            print("Got 'quit' from GUI, telling GUI to close")
            await self.writeToGUI(None)
            await self.qQuit.put(None)
            raise QuitException

        print("Server: got %s" % str(item))
        reply = {'type': 'ack', 'data': item}
        print("Server: replying with %s" % str(reply))
        await self.writeToGUI(reply)
        print("Server: reply sent")

    async def task_ticker(self):
        """
        This tiny task is there to show the event loop is still running
        :return:
        """
        while self.isRunning:
            print("Server: task_ticker: event loop is live")
            await asyncio.sleep(5)
        print("Server: task_ticker: finished because isRunning=False")

    async def readFromGUI(self):
        """
        Receive an object sent by the GUI, by calling the blocking Pipe reader method in a separate thread
        :return:
        """
        item = await (self.loop.run_in_executor(self.threadPool, self.pipe.recv))
        return item

    async def writeToGUI(self, item):
        """
        Send an object to the GUI, by calling the blocking Pipe writer method in a separate thread
        :return:
        """
        await (self.loop.run_in_executor(self.threadPool, self.pipe.send, item))

    async def arun(self):
        self.qQuit = asyncio.Queue()
        self.task_listenToGUI = asyncio.create_task(self.task_listenToGUI())
        self.task_ticker = asyncio.create_task(self.task_ticker())
        await self.qQuit.get()

    @classmethod
    def run(cls, conn):
        print("Server.run: creating server instance")
        inst = cls(conn)
        try:
            asyncio.run(inst.arun())
            print("Server.run: server terminated normally")
        except:
            traceback.print_exc()
            print("Server.run: server crashed")

class GUI:
    """
    Implement a view-only FLTK GUI, as lean as possible. No
    model or controller. This sends user events to the Server,
    and receives display update commands from the Server, via
    an inter-process Pipe connected between them.
    """
    def __init__(self, pipe):
        """
        Set up this GUI
        :param pipe: an inter-process Pipe
        """
        self.pipe = pipe
        self.createGUI()

    def createGUI(self):
        """
        Construct the FLTK GUI
        :return:
        """
        winOrg = FLCursor(100, 50)           # origin of window on the screen
        winSize = FLCursor(400, 300)         # size of the window
        btnSize = FLCursor(80, 20)           # standard size of buttons we wish to place

        # now place the window on the screen
        self.win, right, down = winOrg.Fl_Window(winSize, "example3.py")

        # now create first 'cursor' object to start the layout within this window
        # and apply an offset to provide room for text field label and some vertical pad
        fldOrg = winOrg.topLeft() + (80, 20)

        # place a write-only field, plus a button
        self.fldIn, right, down = fldOrg.Fl_Input((180, 20), "Input:")
        self.btnSend, right, _ = right.Fl_Return_Button(btnSize, "Send")

        self.fldOutBuf = fltk.Fl_Text_Buffer()
        self.fldOut, right, down = (down + 40).Fl_Text_Display((250, 150), "Output:")
        self.fldOut.buffer(self.fldOutBuf)
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

class ProcessPair:
    """
    Class to create and run a pair of processes which interact with each other
    over an inter-process Pipe connection
    """
    def __init__(self, parentRunner, childRunner):
        """
        Create the ProcessPair object.
        :param parentRunner: a sync callable function which accepts a single argument, the parent
        side of the pipe
        :param childRunner: a sync callable function which accepts a single argument, the child
        side of the pipe
        """
        self.parentRunner = parentRunner
        self.childRunner = childRunner

    def run(self):
        """
        Launch both the parent and child runners, and connect a Pipe between them
        :return:
        """
        # create inter-process pipe
        parent_conn, child_conn = Pipe()

        # spawn the GUI to run in a separate process and communicate over the pipe
        print("ProcessPair.run: create and launch child process")
        p = Process(target=self.childRunner, args=(child_conn,))
        p.start()

        print("ProcessPair.run: create and run parent in current process")
        self.parentRunner(parent_conn)
        print("ProcessPair.run: parent terminated")


def main():
    procPair = ProcessPair(Server.run, GUI.run)
    procPair.run()

if __name__ == '__main__':
    main()

