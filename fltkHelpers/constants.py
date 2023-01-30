import fltk

_table = {}

_evNames = [
    'FL_NO_EVENT',
    'FL_PUSH',
    'FL_DRAG',
    'FL_RELEASE',
    'FL_MOVE',
    'FL_MOUSEWHEEL',
    'FL_ENTER',
    'FL_LEAVE',
    'FL_FOCUS',
    'FL_UNFOCUS',
    'FL_KEYDOWN',
    'FL_KEYUP',
    'FL_SHORTCUT',
    'FL_DEACTIVATE',
    'FL_ACTIVATE',
    'FL_HIDE',
    'FL_SHOW',
    'FL_PASTE',
    'FL_SELECTIONCLEAR',
    'FL_DND_ENTER',
    'FL_DND_DRAG',
    'FL_DND_LEAVE',
    'FL_DND_RELEASE',
]

_events = {}
for _evName in _evNames:
    _evVal = getattr(fltk, _evName)
    _events[_evVal] = _evName

for attr in dir(fltk):
    val = getattr(fltk, attr)
    if attr.startswith("FL_") and isinstance(val, int):
        if val in _table:
            attr1 = _table[val]
            if isinstance(attr1, str):
                attr1 = [attr1]
            attr1.append(attr)
            _table[val] = attr1
        else:
            _table[val] = attr

def lookupConstant(n):
    return _table.get(n, None)

def lookupEvent(n):
    return _events.get(n, _table.get(n, '??(%d)' % n))


