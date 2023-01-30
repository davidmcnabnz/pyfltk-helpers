"""
fltkHelpers.py - materials to ease PyFLTK GUI development
"""
import fltk

class FLCursor:
    """
    Utility class for helping with layout of FLTK widgets. Provides a system for
    'relative' rather than 'absolute' placement, so that new widgets can be
    placed 'below' or to the 'right' of certain earlier widgets.
    """
    # sets the default spacing between widgets
    defaultSpacing = 5

    def __init__(self, x, y=None, spacing=None):
        """
        Represents an absolute location on an FLTK widget, for the placement
        of other widgets
        :param x: absolute x co-ordinate
        :param y: absolute y co-ordinate
        :param spacing: when using this point to place a widget, use this value to
        determine the new 'right of' and 'below' locations of subsequent widgets.
        """
        if isinstance(x, FLCursor):
            # if given an FLCursor object, just harvest its values
            self.x = x.x
            self.y = x.y
            self.spacing = spacing if spacing is not None else x.spacing
        elif isinstance(x, (tuple, list)):
            # alsp permit single point as first arg
            self.x = x[0]
            self.y = x[1]
            self.spacing = x[2] if len(x) > 2 else (spacing or self.defaultSpacing)
        else:
            # also accept separate x,y
            self.x = x
            self.y = y
            self.spacing = spacing or self.defaultSpacing

    def __sub__(self, offset):
        """
        Subtract from our present position, without spacing.

        :param offset: can be another FLCursor, or a list/tuple. This base class cannot
        support single-value int, and if given one, will raise a TypeError
        :return: a new object of the same class with the offset applied
        """
        if isinstance(offset, (list, tuple)):
            return self.__class__(self.x - offset[0], self.y - offset[1])
        elif isinstance(offset, FLCursor):
            return self.__class__(self.x - offset.x, self.y - offset.y)
        else:
            raise TypeError("Don't know how to add offset %s" % offset)

    def __add__(self, offset):
        """
        Add to our present position, without spacing.

        :param offset: can be another FLCursor, or a list/tuple. This base class cannot
        support single-value int, and if given one, will raise a TypeError
        :return: a new object of the same class with the offset applied
        """
        if isinstance(offset, (list, tuple)):
            return self.__class__(self.x + offset[0], self.y + offset[1])
        elif isinstance(offset, FLCursor):
            return self.__class__(self.x + offset.x, self.y + offset.y)
        else:
            raise TypeError("Don't know how to add offset %s" % offset)

    def __repr__(self):
        return "%s(%s,%s)" % (self.__class__.__name__, self.x, self.y)

    def __getattr__(self, attr):
        """
        Syntactic sugar for .add(), which allows dereferencing on the name of an FLTK widget class
        """
        # sanity checks to make sure widget exists, is a class, and is a subclass of Fl_Widget
        widCls = getattr(fltk, attr, None)
        if widCls is None:
            raise AttributeError("Unknown attribute: %s" % attr)
        return self.add(widCls)

    def add(self, widCls, size=None, *args):
        """
        This provies support for a vastly simpler programming pattern for laying
        out the widgets relative to other widgets. It does this by providing
        'proxy' or 'factory' functions for each widget type, which can be called and
        passed just the widget's size, plus specific extra arguments the widget needs.

        The pattern used to create/place a widget in this style is:

          btnWidget, right, below = point.Fl_Button((80, 20), "Click Me")

          # place another button to the right
          btnWiget1, right, _ = right.Fl_Button((80, 20), "Click Me Too")

          # now place a widget underneath the first one
          btnWidget2, right, below = below.Fl_Button((80, 20), "Click Me Now")

        :param attr: name of FLTK widget class to instantiate
        :return: a factory function which instantiates and places the widget, and returns the
        widget object plus "right of" and "beneath' points to use for placing subsequent ones
        """
        if not isinstance(widCls, type):
            raise AttributeError("Attribute %s is not a class" % widCls)
        if not issubclass(widCls, fltk.Fl_Widget):
            raise AttributeError("Attribute %s is not a Fl_Widget subclass" % widCls)

        # now within this closure, create a factory function which instantiates and places
        # the desired widget type, at the deired location, and returns a 3-tuple
        # (widgetObj, rightOf, below)
        def placeWidget(size1, *args1, **kw):

            if isinstance(size1, (list, tuple)):
                size1 = FLCursor(size1)
            if not isinstance(size1, FLCursor):
                raise TypeError("size should be a FLCursor or tuple/list, got %s" % str(size1))

            rightOf = FLCursorRight(self.x + size1.x, self.y, self.spacing) + self.spacing
            below = FLCursorDown(self.x, self.y + size1.y, self.spacing) + self.spacing
            widObj = widCls(self.x, self.y, size1.x, size1.y, *args1, **kw)
            return widObj, rightOf, below

        if size is not None:
            wid = placeWidget(size, *args)
            return wid
        else:
            return placeWidget

    def bottom(self, height):
        """
        Return a point cursor for starting placement of widgets of a given height from the bottom
        of this cursor
        :param height:
        :return:
        """
        if isinstance(height, (int, float)):
            height = FLCursor(height)
        return self.__class__(self.spacing, self.y - height.y - self.spacing)

    def bottomCentre(self, size, num):
        if not isinstance(size, FLCursor):
            size = FLCursor(size)
        xOffset = noffset(self.x, num, self.spacing, size.x)
        bottom = self.bottom(size)
        bottom.x = xOffset
        return bottom

    def centre(self, size, num):
        """
        Return a cursor which starts the placement of n widgets of same size
        :param size:
        :param num:
        :return:
        """
        if not isinstance(size, FLCursor):
            size = FLCursor(size)
        xOffset = noffset(self.x, num, self.spacing, size.x)
        return self.__class__(xOffset, self.y)

    def topLeft(self):
        return self.__class__(self.spacing, self.spacing)

    def fillWidth(self, n):
        """
        return a width in pixels which can place n uniform-width pixels
        """
        return nsize(self.x, n, self.spacing)

class FLCursorRight(FLCursor):
    """
    Subclass to allow single int values to be passed and taken as dx for the '+' and '-' overloads
    """
    def __add__(self, offset):
        if isinstance(offset, (int, float)):
            # treat offset as a dx value
            return self.__class__(self.x + offset, self.y, self.spacing)
        else:
            return super().__add__(offset)

    def __sub__(self, offset):
        if isinstance(offset, (int, float)):
            # treat offset as a dx value
            return self.__class__(self.x - offset, self.y)
        else:
            return super().__add__(offset)

class FLCursorDown(FLCursor):
    """
    Subclass to allow single int values to be passed and taken as dy for the '+' and '-' overloads
    """
    def __add__(self, offset):
        if isinstance(offset, (int, float)):
            # treat offset as a dy value
            return self.__class__(self.x, self.y + offset)
        else:
            return super().__add__(offset)

    def __sub__(self, offset):
        if isinstance(offset, (int, float)):
            # treat offset as a dy value
            return self.__class__(self.x, self.y - offset)
        else:
            return super().__sub__(offset)

def nsize(total, num, spacing):
    """
    for laying out a number of identically sized widgets in a given
    limit of total pixels, with a given spacing between each widget and
    between end widgets and borders, determine the size available for
    each instance of the widget

    :param total: total size available, in pixels
    :param num: number of widget instances needed
    :param spacing: spacing between widgets, and end widgets and edges
    :return: size in pixels available to each widget
    """
    totalSpacing = num * (spacing + 1)
    netAvailable = total - totalSpacing
    perInstance = netAvailable / num
    return int(perInstance)

def noffset(total, num, spacing, size):
    """
    For laying out n instances of a widget of a given size in a given space, centred
    :param total:
    :param num:
    :param spacing:
    :param size:
    :return:
    """
    # calculate the total space used by instances plus spacing in between
    used = size * num + spacing * (num - 1)

    # now how much is left?
    left = total - used

    offset = left / 2
    return int(offset)

