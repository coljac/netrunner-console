import curses
import glob

class FileChooser(object):
    def __init__(self, stdscr,  directory):
        self.stdscr = stdscr
        self.directory = directory
        
    def choose(self):
        y, x = self.stdscr.getmaxyx()
        files = glob.glob(self.directory + "/*.txt")
        win = curses.newwin(20, 40, 10, int((x/2)-20))
        self.files = files
        self.selected = 0
        self.draw_win(win, files)

        while True:
            c = self.stdscr.getch()
            if c == 10:
                break
            elif c == 27:
                self.selected = -1
                break
            elif c == curses.KEY_DOWN:
                self.selected = min(len(files) - 1, self.selected + 1)
            elif c == curses.KEY_UP:
                self.selected = max(0, self.selected - 1)
            self.draw_win(win, files)

        filename = files[self.selected] if self.selected >= 0 else None
        del win
        return filename

    def draw_win(self, win, files):
        win.erase()
        win.addstr(1, 1, ("Choose file from " + self.directory + ":").ljust(win.getmaxyx()[1]-2), curses.A_REVERSE)

        for i, f in enumerate(files):
            attr = curses.A_REVERSE if self.selected == i else 0
            win.addstr(i + 3, 1, f, attr)

        win.box()
        win.refresh()
        curses.doupdate()
