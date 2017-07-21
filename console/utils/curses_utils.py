import curses
from curses import panel
import os
import textwrap


# Can you believe how lame curses.textpad is? It has emacs bindings so the user needs to know ^G to use it.
#  Re-engineering the wheel it is.
class InputWindow(object):
    def __init__(self, stdscr, prompt="Enter text:"):
        self.stdscr = stdscr
        self.prompt = prompt
        self.string = ""
        self.panel = None
        self.width = 0

    def key_loop(self):
        while True:
            c = self.stdscr.getch()
            if c == 27: # ESC
                return None
            elif c == 10: # Enter
                return self.string
            elif c == curses.KEY_BACKSPACE or c == 127:
                if len(self.string) > 0:
                    self.string = self.string[:-1]
            elif c == curses.KEY_HOME:
                pass
            elif c == curses.KEY_END:
                pass
            elif c == curses.KEY_RIGHT:
                pass
            elif c == curses.KEY_LEFT:
                pass
            else:
                self.string += chr(c)
            self.update()

    def update(self):

        to_draw = self.string
        if len(self.string) > self.width - 5:
            to_draw = "..." + self.string[-(self.width - 7):]

        self.panel.window().erase()
        self.panel.window().box()
        self.panel.window().addstr(0, 1, self.prompt)
        self.panel.window().addstr(1, 2, to_draw)
        panel.update_panels()
        curses.doupdate()

    def get_string(self):
        maxy, maxx = self.stdscr.getmaxyx()

        # win.addstr(1, 1, self.message.ljust(width-2), curses.A_REVERSE)
        height = 3
        width = min(40, maxx - 2)
        win = curses.newwin(height, width, int((maxy - height)/2), int((maxx - width)/2))
        self.width = width
        self.panel = panel.new_panel(win)
        win.box()
        self.panel.top()
        # win.addstr(1, 1, "")
        curses.curs_set(True)
        # panel.update_panels()
        # curses.doupdate()
        self.update()
        string = self.key_loop()
        curses.curs_set(False)
        self.panel.bottom()
        panel.update_panels()
        curses.doupdate()
        del win
        return string

class ScrollableSelector(object):
    def __init__(self, stdscr, items, message="Choose:", return_values=True):
        self.stdscr = stdscr
        self.top = 0
        self.selected = 0
        self.selected_before = 0
        self.items = items
        self.win = None
        self.pad = None
        self.message = message
        self.search = ""
        self.searching = False
        self.panel = None
        self.return_values = return_values

    def handle_key(self, c):
        return False

    def render_item(self, win, item, line, index):
        width = win.getmaxyx()[1]
        attr = curses.A_NORMAL
        if index == self.selected:
            attr = curses.A_REVERSE
        win.addstr(line, 1, str(item).ljust(width - 2), attr)

    def key_loop(self):
        while True:
            c = self.stdscr.getch()
            # c = self.win.getch() # Buggy
            if not self.searching and self.handle_key(c):
                continue

            if self.searching:
                if c == 10:
                    self.searching = False
                elif c == 27:
                    self.searching = False
                    self.selected = self.selected_before
                else:
                    if c == curses.KEY_BACKSPACE or c == 127:
                        self.search = self.search[:-1]
                    else:
                        self.search += chr(c)
                    start, end, inc = self.selected_before, len(self.items), 1
                    if self.search_backward:
                        start, end, inc = self.selected_before, -1, -1
                    for i in range(start, end, inc):
                        if self.search.lower() in str(self.items[i]).lower():
                            self.selected = i
                            break
            else:

                if c == ord('j') or c == curses.KEY_DOWN:
                    self.selected = min(self.selected + 1, len(self.items) - 1)
                elif c == ord('k') or c == curses.KEY_UP:
                    self.selected = max(self.selected - 1, 0)
                elif c == curses.KEY_HOME or c == ord("g") or c == ord("K"):
                    self.selected = 0
                elif c == curses.KEY_END or c == ord("J") or c == ord("G"):
                    self.selected = len(self.items) - 1
                elif c == curses.KEY_NPAGE:
                    self.selected = min(self.selected + 10, len(self.items) - 1)
                elif c == curses.KEY_PPAGE:
                    self.selected = max(self.selected - 10, 0)
                elif c == ord('/') or c == ord('?'):
                   self.searching = True
                   self.search = ""
                   self.search_backward = (c == ord('?'))
                elif c == 27: # Esc
                    self.selected = -1
                    break
                elif c == 10: # Enter
                    break

                self.selected_before = self.selected
            if self.selected < self.top:
                self.top = self.selected
            elif self.selected - self.top >= self.win.getmaxyx()[0] - 6:
                self.top = self.selected - (self.win.getmaxyx()[0] - 6)

            self.update()

    def update(self):
        win = self.win
        height, width = win.getmaxyx()
        win.addstr(1, 1, self.message.ljust(width-2), curses.A_REVERSE)
        j = self.top
        for i in range(3, height - 2):
            if i == 3 and self.top > 0:
                win.addstr(i, 1, ("...".ljust(width - 2)))
                j += 1
                continue
            if j < len(self.items):
                item = self.items[j]
                attr = 0
                self.render_item(win, item, i, j)
                j += 1
            else:
                break
        if self.searching:
            s = "?" if self.search_backward else "/"
            win.addstr(height - 2, 1, (s + self.search).ljust(width - 2), curses.A_REVERSE)
        elif j < len(self.items):
            win.addstr(height - 2, 1, ("...".ljust(width - 2)))
        else:
            win.addstr(height - 2, 1, " "*(width - 2))
        win.box()
        win.refresh()

    def choose(self):
        curses.noecho()
        y, x = self.stdscr.getmaxyx()
        height = min(len(self.items) + 5, y - 2)
        if len(self.items) > 0:
            width = min(max([len(str(s)) + 5 for s in self.items]) + 2, x - 2)
        else: 
            width = 10
        width = max(len(self.message), width)
        self.win = curses.newwin(height, width, int((y - height)/2), int((x - width)/2))
        self.panel = panel.new_panel(self.win)
        self.panel.top()
        self.update()
        panel.update_panels()
        curses.doupdate()
        self.key_loop()
        self.panel.bottom()
        panel.update_panels()
        curses.doupdate()
        del self.win
        del self.panel
        if self.selected < 0:
            return None
        else:
            return self.get_chosen()

    def get_chosen(self):
        if self.return_values:
            return self.items[self.selected]
        else:
            return self.selected

class FileChooser(ScrollableSelector):

    def __init__(self, stdscr, directory, extensions, locked=False):
        self.directory = directory
        directories = []
        files = []
        self.locked = locked
        self.extensions = extensions
        for root, dirs, files_ in os.walk(directory):
            directories.extend(sorted(dirs))
            if len(files_) > 0:
                files = [f for f in files_ if any([f.endswith(ext) for ext in extensions])]
            break

        files = sorted(files)
        ScrollableSelector.__init__(self, stdscr, ([] if locked else [".."]) +  directories + files, "Choose file: ")

    # TODO: Enable enter path
    def handle_key(self, c):
        # if c == ord('o'): # Open file or directory
           # Pop up a new window to ask for the path
           #  return True
        return False


    def get_chosen(self):
        chosen = self.directory + os.sep + self.items[self.selected]
        if os.path.isdir(chosen):
            return FileChooser(self.stdscr, chosen, self.extensions).choose()
        else:
            return chosen


class MultipleSelector(ScrollableSelector):
    def __init__(self, stdscr, items, message, chosen=None, return_values=True):
        ScrollableSelector.__init__(self, stdscr, items, message, return_values=return_values)
        self.items = ["-None-", "-All-"] + self.items
        self.chosen = []
        if chosen is not None:
            self.chosen.extend([c + 2 for c in chosen]) # All, none exclude

    def handle_key(self, c):
        if c == 32: # Space
            if self.selected == 0: # None
                self.chosen = []
            elif self.selected == 1: # All
                self.chosen = [i for i in range(2, len(self.items))]
            elif self.selected in self.chosen:
                self.chosen.remove(self.selected)
            else:
                self.chosen.append(self.selected)
            self.update()
            return True
        return False

    def render_item(self, win, item, line, index):
        width = win.getmaxyx()[1]
        attr = curses.A_NORMAL
        if index == self.selected:
            attr = curses.A_REVERSE
        if index > 1:
            if index in self.chosen:
                attr += curses.COLOR_RED
                win.addstr(line, 1, "(*) ", attr)
            else:
                win.addstr(line, 1, "( ) ", attr)
            win.addstr(str(item).ljust(width - 2), attr)
        else:
            win.addstr(line, 1, item.center(width -2, "-"), attr)
            

    def get_chosen(self):
        if self.return_values:
            return [self.items[i] for i in self.chosen if i>1]
        else:
            return [i-2 for i in self.chosen if i>1]

class TextPager(object):
    
    def __init__(self, stdscr, pages, optsize=(20, 30), firstpage=None):
        """ Pages are tuples of (title, text). Text will be wrapped
        but pre-existing whitespace respected where possible.
        optsize specifies the desired size, may be changed due to
        screen constraints.
        """
        self.pages = pages
        self.stdscr = stdscr
        self.optsize = optsize
        self.current_page = firstpage if firstpage else 0
        self.win = None

    def show(self):
        if len(self.pages) == 0:
            return

        maxy, maxx = self.stdscr.getmaxyx()
        if maxy >= self.optsize[0] and maxx >= self.optsize[1]:
            height, width = self.optsize
        else:
            if maxy < self.optsize[0]:
                height = maxy
                width = min(maxx, self.optsize[1] + 10)
            else:
                width = maxx
                height = min(maxy, self.optsize[0] + 10)

        # Centre on screen
        y = int((maxy - height) / 2)
        x = int((maxx - width) / 2)
        self.win = curses.newwin(height, width, y, x)
        self.update()

        self.key_loop()


    def key_loop(self):
        while True:
            c = self.stdscr.getch()
            if c == 27:
                break
            elif c == 10:
                break
            elif c == curses.KEY_RIGHT:
                self.current_page += 1
                if self.current_page > len(self.pages)  - 1:
                    self.current_page = 0
            elif c == curses.KEY_LEFT:
                self.current_page -= 1
                if self.current_page < 0:
                    self.current_page = len(self.pages) - 1
            self.update()

    def update(self):
        win = self.win
        height, width = win.getmaxyx()
        win.erase()

        win.addstr(1, 0, self.pages[self.current_page][0].center(width),  curses.color_pair(1))

        lines = self.pages[self.current_page][1].split("\n")
        maxwidth = max([len(s) for s in lines])
        if maxwidth < width - 2:
            # win.addstr(3, 1, "\n".join(["  " + line for line in lines]))
            self.add_formatted_text(3, 1, "\n".join(["   " + line for line in lines]))
        else:
            wrapped = textwrap.TextWrapper(replace_whitespace=False, width=width - 2).wrap(
                self.pages[self.current_page][1])
            # win.addstr(3, 1, "\n".join(wrapped[0:height - 4]))
            self.add_formatted_text(3, 1, "\n  ".join(wrapped[0:height - 4]))

        win.addstr(height -2, 0, ("%d of %d" % (self.current_page+1, len(self.pages))).center(width),
                   curses.color_pair(3)) # TODO: Can I reserve a few color pairs for the utils?
        if self.current_page < len(self.pages) - 1:
            win.addstr(height - 2, width - 8, "Next >>>", curses.color_pair(24))
        if self.current_page > 0:
            win.addstr(height - 2, 1, "<<< Prev", curses.color_pair(24))
        self.win.box()
        self.win.refresh()
        curses.doupdate()

    def add_formatted_text(self, starty, startx, text):
        self.win.move(starty, startx)
        bold = curses.A_BOLD
        italic = curses.A_UNDERLINE
        code = curses.color_pair(2)

        attr = curses.A_NORMAL
        for i, c in enumerate(text):
            if c == '*':
                if text[i - 1] == "*":
                    continue
                if text[i+1] == "*":
                    if attr & bold != 0:
                        attr -= bold
                    else:
                        attr += bold
                else:
                    if attr & italic != 0:
                        attr -= italic
                    else:
                        attr += italic
                continue
            elif c == '`':
                if attr & code != 0:
                    attr -= code
                else:
                    attr += code
                continue
            self.win.addstr(c, attr)


class ConfirmCancel(object):
    def __init__(self, stdscr, message):
        self.stdscr = stdscr
        self.message = message
        self.selected = 0
        self.height = 4

    def show(self):
        maxy, maxx = self.stdscr.getmaxyx()
        width = 30
        wrapped = textwrap.TextWrapper(replace_whitespace=False, width=width - 2).wrap(self.message)
        self.height += len(wrapped)
        self.message = "\n ".join(wrapped)
        y = int((maxy - self.height) / 2)
        x = int((maxx - width) / 2)
        win = curses.newwin(self.height, width, y, x)

        self.update(win)

        while True:
            c = self.stdscr.getch()
            if c == 32 or c == 10:
                return (self.selected == 0)
            elif c == 27:
                return False
            elif c == 9 or c == curses.KEY_RIGHT or c == curses.KEY_LEFT:
                self.selected = 0 if self.selected == 1 else 1
                self.update(win)

        return self.selected == 0

    def update(self, win):
        height, width = win.getmaxyx()
        win.addstr(1, 1, self.message)
        attr = [curses.color_pair(28), curses.color_pair(28)]
        attr[self.selected] = curses.color_pair(26)

        win.addstr(self.height - 2, int((width - 24)/2), "OK".center(10), attr[0])
        win.addstr(self.height - 2, int((width - 24)/2) + 14, "Cancel".center(10), attr[1])
        win.box()
        win.refresh()
        # curses.doupdate()

class Dialog(object):

    def __init__(self, stdscr, message, size=None):
        self.message = message
        self.stdscr = stdscr
        self.size = size

    def show(self):
        if not self.size:
            self.size = 5, 25
        maxy, maxx = self.stdscr.getmaxyx()
        height, width = 5, 30
        y = int((maxy - height) / 2)
        x = int((maxx - width) / 2)
        wrapped = textwrap.TextWrapper(replace_whitespace=False, width=width - 2).wrap(self.message)
        height = len(wrapped) + 3

        win = curses.newwin(height, width, y, x)
        win.addstr(1, 1, "\n".join([" " + w for w in wrapped]))
        win.box()
        win.refresh()
        curses.doupdate()
        self.stdscr.getch()
        del win

