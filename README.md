# pyfltk-helpers

Resources to simplify programming with the PyFLTK GUI framework.

Copyright (c) 2023 by David McNab 

## Introduction

This package offers classes and functions to reduce much of the
repetitive and error-prone work of managing widgets on FLTK GUIs.

## Background

PyFLTK is a SWIG wrapper on top of the long-famed FLTK GUI 
framework. For decades, FLTK has been a popular framework
choice for GUIs which need to be simple, light on resources,
easy to learn. Howerver, FLTK does have some downsides.

As a low-level GUI framework, FLTK (and PyFLTK) gives the programmer all the
responsibility for managing widget sizes and locations. 

The example programs with both FLTK and PyFLTK typically 
feature widgets being placed into their parent containers
with absolute (x,y) locations and with absolute (width, height)
sizes.

This is not so much a problem when first creating a GUI
layout programmatically. But when maintaining this layout
later, to add, remove, move and reorganise widgets, the 
programmer has to recalculate all the (x,y) locations of
all the widgets which can become very distracting, tiring and
often, a source of errors.

## Placement Cursors

The `fltkHelpers.cursor` module provides classes which act as
GUI widget placement 'cursors', which allows widgets to be
placed in their containers at positions which are relative to
prior widgets. As such, it automatically calculates the required
(x, y) locations for each added widget.

## Example Program

Here is a small demo (extracted from `examples/example1.py`) which shows widgets being placed at 
relative
locations:

```
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
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.outTime.value(now)

    def on_btnQuit(self, *args):
        self.win.hide()

    def run(self):
        fltk.Fl.run()

def main():
    app = MyApp()
    app.run()

```
