#!/usr/bin/env python3
"""
example1.py

Minimal simple example demonstrating the cursor classes helping with layout
"""
import sys, os
import datetime

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

class MyApp:

    def __init__(self):

        # origin of window on the screen
        winOrg = FLPoint(100, 50)

        # size of the window
        winSize = FLPoint(300, 140)

        # standard size of buttons we wish to place
        btnSize = FLPoint(80, 20)

        # now place the window on the screen
        self.win, right, down = winOrg.Fl_Window(winSize, "example1.py")

        # now create first 'cursor' object to start the layout within this window
        # and apply an offset to provide room for text field label and some vertical pad
        fldOrg = winOrg.topLeft() + (80, 20)

        # place a write-only field, plus a button
        self.outTime, right, down = fldOrg.Fl_Output((180, 20), "Datetime:")
        self.btnGetTime, right, down = down.Fl_Button(btnSize, "Update")
        self.btnGetTime.callback(self.on_btnUpdate)

        # get a cursor for adding n widgets of given height to bottom row of window
        bottomOrg = winSize.bottomCentre(btnSize, 1)

        # now we can place that bottom button
        self.btnQuit, _, _ = bottomOrg.Fl_Button(btnSize, "Quit")
        self.btnQuit.callback(self.on_btnQuit)

        self.win.show()
        self.win.end()

    def on_btnUpdate(self, *args):
        """
        callback for when user clicks the 'Update' button
        """
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.outTime.value(now)

    def on_btnQuit(self, *args):
        """
        callback for when user clicks the 'Quit' button
        """
        self.win.hide()

    def run(self):
        fltk.Fl.run()

def main():
    app = MyApp()
    app.run()

if __name__ == '__main__':
    main()

