#!/usr/bin/env python3
"""
example2.py

Extends on example1 by implementing a custom Widget class
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
from fltkHelpers.constants import lookupConstant, lookupEvent

# origin of window on the screen
winOrg = FLPoint(100, 50)

# size of the window
winSize = FLPoint(300, 140)

# standard size of buttons we wish to place
btnSize = FLPoint(80, 20)

class MyWidget(fltk.Fl_Group):

    def __init__(self, xpos, ypos, width, height):

        super().__init__(xpos, ypos, width, height)
        orgWid = FLPoint(5, 5)
        orgTxt = orgWid + (80, 5)

        self.outTime, right, down = orgTxt.Fl_Output((180, 20), "Datetime:")
        self.btnGetTime, right, down = down.Fl_Button(btnSize, "Update")
        self.btnGetTime.callback(self.on_btnUpdate)

        self.end()

        self.box(fltk.FL_ENGRAVED_FRAME)

        self.n = 0

    def on_btnUpdate(self, *args):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.outTime.value(now)

    def handle(self, evNum):
        evLabel = lookupEvent(evNum)
        if evLabel != 'FL_NO_EVENT':
            print("handle: %s" % evLabel)
        return super().handle(evNum)

class MyApp:

    def __init__(self):

        # now place the window on the screen
        self.win, right, down = winOrg.Fl_Window(winSize, "example2.py")

        # add in our custom widget
        org = FLPoint(FLPoint.defaultSpacing, FLPoint.defaultSpacing, FLPoint.defaultSpacing)

        self.widMine, right, down = org.add(MyWidget, (270, 60))

        # get a cursor for adding n widgets of given height to bottom row of window
        bottomOrg = winSize.bottomCentre(btnSize, 1)

        # now we can place that bottom button
        self.btnQuit, _, _ = bottomOrg.Fl_Button(btnSize, "Quit")
        self.btnQuit.callback(self.on_btnQuit)

        self.win.show()
        self.win.end()

    def on_btnQuit(self, *args):
        self.win.hide()

    def run(self):
        fltk.Fl.run()

def main():
    app = MyApp()
    app.run()

if __name__ == '__main__':
    main()

