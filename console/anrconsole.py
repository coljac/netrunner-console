#!env python3

from . import cards
from .utils.curses_utils import *
from .utils.config import Config
from copy import deepcopy
import time
import webbrowser
from collections import defaultdict
import sys
import shlex
import threading

os.environ.setdefault('ESCDELAY', '15')
# BUG: Cards with apostraphes not importing Aesop Maker's eye

# BUG: Resizing card window resets selected card index, display top (of course)
# BUG: init_win doesn't preserve state properly e.g. display_top
# BUG: credit symbol in two places (see col headers)
# BUG: Shift tab
# BUG: Neutral cards
# BUG: Can crash on resize
# BUG: Hidden panels briefly visible sometimes on startup and resize (delete)
# BUG: Crash when deleting last card in a deck
# Traceback (most recent call last):
#   File "/home/coljac/anaconda3/bin/netrunner-console", line 11, in <module>
#     load_entry_point('Netrunner-Console==0.1', 'console_scripts', 'netrunner-console')()
#   File "/home/coljac/anaconda3/lib/python3.5/site-packages/Netrunner_Console-0.1-py3.5.egg/console/__init__.py", line 8, in main
#     anrconsole.startapp()
#   File "/home/coljac/anaconda3/lib/python3.5/site-packages/Netrunner_Console-0.1-py3.5.egg/console/anrconsole.py", line 1331, in startapp
#     curses.wrapper(main)
#   File "/home/coljac/anaconda3/lib/python3.5/curses/__init__.py", line 94, in wrapper
#     return func(stdscr, *args, **kwds)
#   File "/home/coljac/anaconda3/lib/python3.5/site-packages/Netrunner_Console-0.1-py3.5.egg/console/anrconsole.py", line 182, in main
#     raise e
#   File "/home/coljac/anaconda3/lib/python3.5/site-packages/Netrunner_Console-0.1-py3.5.egg/console/anrconsole.py", line 177, in main
#     cardapp.keystroke(c)
#   File "/home/coljac/anaconda3/lib/python3.5/site-packages/Netrunner_Console-0.1-py3.5.egg/console/anrconsole.py", line 628, in keystroke
#     self.keystroke_deck(c)
#   File "/home/coljac/anaconda3/lib/python3.5/site-packages/Netrunner_Console-0.1-py3.5.egg/console/anrconsole.py", line 687, in keystroke_deck
#     self.display_card = self.deck.cards[self.selected_deck_card_index]
# IndexError: list index out of range


# Wontfix: Can't set background color properly
# BUG: Cancelling filter change broken
# BUG: Some card names not rendering properly as they are too long
# BUG: Help overlaps card display bottom and is not redrawn
# BUG: forward/back search - flaky; weirdness if search hits last card
# BUG - errors out if screen too small initially


# Alpha 1 todos:
# TODO: Column headers a bit confusing; can be too narrow
# TODO: Check 256 color support
# TODO: Ascii/unicode check or config
# TODO: Black background - doesn't work?
# TODO: Initial help page depends on selected mode
# TODO: Pass in deck as argument

# Version 1 todos:
# TODO: Advanced searching (or/and, other fields)
# TODO: Nicer colors
# TODO: Layout swap with card viewer/movable card display
# TODO: Download the card images, fancy image viewer
# TODO: Refactor and document
# TODO: Deck window size # Hardcoded for now
# TODO: Check deck legality

# Later todos:
# TODO move card display window to side
# TODO: Sort column[s]
# TODO: Dynamically determine verbosity
# TODo: Check for unnecessary updates; do single lines where possible
# TODO: dynamic help at bottom
# TODO config panel, saveable layout
# TODO images - fancy style with window and caching
# TODO Help text
# todo layouts
# TODO sort or
# TODO: Themes
# TODO: Load cards in bg thread
# TODO: Cache all the cards and metrics/sqlite

# Wishlist: Run HQ; card ascii art

def error_log(string):
    if True:
        with open("/tmp/error.log", "a") as log:
            log.write(string + "\n")

app_styles = {}

def main(stdscr):
    deck_dir = deck_file = None
    symbols="unicode"
    if "-a" in sys.argv:
        symbols = "ascii"
        sys.argv.remove("-a")

    if len(sys.argv) > 1:
        if os.path.exists(sys.argv[1]):
            if os.path.isdir(sys.argv[1]):
                deck_dir = sys.argv[1]
            else:
                deck_file = sys.argv[1]

    curses.curs_set(False)
    curses.use_default_colors()

    init_app_colors()

    cardapp = Andeck(stdscr, deck_dir=deck_dir, deck_file=deck_file, symbols=symbols)
    stdscr.noutrefresh()
    cardapp.update_search()
    curses.doupdate()

    while True:
        try:
            c = stdscr.getch()
            if c == curses.KEY_RESIZE:
                cardapp.resize()
                continue
            elif c < 0:
                curses.napms(50)
                continue
                # TODO
            elif c == 27 and cardapp.mode != "F":
                if cardapp.mode == "N":
                    cardapp.search_string = ""
                    cardapp.update_search()
                cardapp.normal_mode()
            elif c == 9: # Tab
                mode = cardapp.mode
                cardapp.normal_mode()
                if mode == "N":
                    cardapp.search_mode()
                elif mode == "C":
                    if cardapp.deck_box_on:
                        cardapp.deck_mode()
                    else:
                        cardapp.search_mode()
                elif mode == "I":
                    cardapp.list_mode()
                elif mode == "D":
                    cardapp.search_mode()
            elif cardapp.mode == "N":
                if c == ord('q'):
                    break
                elif c == ord('a') or c == ord('i') or c == ord('/'):
                    cardapp.search_mode(append=(c == ord('a')))
                elif c in [ord('j'), ord('k'), curses.KEY_DOWN, curses.KEY_UP]:
                    cardapp.list_mode()
                elif c in [ord('h'), ord('?')]:
                    cardapp.help_mode()
                elif c == ord("f"):
                    cardapp.filter_mode()
                elif c == ord("D"):
                    if not cardapp.deck_box_on:
                        cardapp.deck_box_toggle()
                    cardapp.deck_mode()
                elif c == ord("C"):
                    cardapp.redownload()


                elif c == ord("t"):
                    choices = [col for col in cardapp.available_columns if col not in ['title']]
                    got_back = MultipleSelector(stdscr, [cards.attr_to_readable(c)[0] for c in choices],
                                                            "Table columns:",
                                             chosen=[i for i,v in enumerate(choices)\
                                                     if v in cardapp.card_columns],
                                             return_values=False).choose()
                    if got_back is not None:
                        cardapp.card_columns = ['title'] + [choices[i] for i in got_back]
                        if 'text' in cardapp.card_columns:
                            cardapp.card_columns.remove('text')
                            cardapp.card_columns.append('text')
                    cardapp.normal_mode()
                elif c == ord('w'):
                    cardapp.card_display_toggle()
                elif c == ord('W'):
                    cardapp.card_display_size_toggle()
                elif c == ord('c'):
                    cardapp.toggle_filter_corp()
                elif c == ord('r'):
                    cardapp.toggle_filter_runner()
                elif c == ord('d'):
                    cardapp.deck_box_toggle()
                else:
                    curses.napms(10)
            elif cardapp.mode == "F":
                cardapp.keystroke_filter(c)
            # elif cardapp.mode == "C":
            #     cardapp.keystroke_columns(c)
            elif cardapp.mode == "Z":
                cardapp.previous_mode()
                cardapp.card_zoom_panel.bottom()
            else:
                cardapp.keystroke(c)

            panel.update_panels()
            curses.doupdate()
        except Exception as e:
            raise e
            # error_log("Unexpected error:" + str(sys.exc_info()))
            # spod()
            # break

    cardapp.config.save()
    sys.exit(0)


def init_app_colors():
    if False and curses.COLORS > 8: ## WINDOWS DEBUG
        curses.init_pair(1, 228, -1)
        curses.init_pair(2, 228, -1)
        curses.init_pair(3, 228, -1)
        curses.init_pair(4, 228, -1)
        curses.init_pair(5, 228, -1)
        curses.init_pair(6, 228, -1)


        curses.init_pair(11, 228, -1)
        curses.init_pair(12, 4, -1)
        curses.init_pair(13, 1, -1)
        curses.init_pair(14, 202, -1)
        curses.init_pair(15, 226, -1)
        curses.init_pair(16, 146, -1)
        curses.init_pair(17, 151, -1)
        curses.init_pair(18, 214, -1)
        curses.init_pair(19, 76, -1)
        curses.init_pair(20, 39, -1)
        curses.init_pair(21, 11, -1)
        curses.init_pair(22, 4, 238)
        curses.init_pair(23, 236, -1)
        curses.init_pair(24, 87, -1)
        curses.init_pair(25, 227, 238)
        curses.init_pair(26, 18, 231)
        curses.init_pair(27, -1, 16)
        curses.init_pair(28, 250, -1)
        curses.init_pair(29, 12, 1)
        curses.init_pair(30, 13, -1)
        curses.init_pair(31, 47, -1)
        curses.init_pair(32, 227, -1)

    else:

        # Slots 1-10 reserved for curses_utils
        # curses.init_pair(1, 228, -1)
        # curses.init_pair(2, 228, -1)
        # curses.init_pair(3, 228, -1)
        # curses.init_pair(4, 228, -1)
        # curses.init_pair(5, 228, -1)
        # curses.init_pair(6, 228, -1)


        curses.init_pair(11, 3, -1)
        curses.init_pair(12, 4, -1)
        curses.init_pair(13, 1, -1)
        curses.init_pair(14, 1, -1)
        curses.init_pair(15, 3, -1)
        curses.init_pair(16, 4, -1)
        curses.init_pair(17, 2, -1)
        curses.init_pair(18, 9, -1)
        curses.init_pair(19, 2, -1)
        curses.init_pair(20, 4, -1)
        curses.init_pair(21, 3, -1)
        curses.init_pair(22, 4, 8)
        curses.init_pair(23, 8, -1)
        curses.init_pair(24, 6, -1)
        curses.init_pair(25, 3, 8)
        curses.init_pair(26, 4, 7)
        curses.init_pair(27, -1, 8)
        curses.init_pair(28, 7, -1)
        curses.init_pair(29, 6, 1)
        curses.init_pair(30, 5, -1)
        curses.init_pair(31, 2, -1)
        curses.init_pair(32, 3, -1)

    app_styles.update({
        "normal": curses.color_pair(0),
        "selected": curses.color_pair(11),  # + curses.A_BOLD,
        "corp": curses.color_pair(12),
        "runner": curses.color_pair(13),
        "jinteki": curses.color_pair(14),
        "nbn": curses.color_pair(15),
        "haas-bioroid": curses.color_pair(16),
        "weyland-consortium": curses.color_pair(17),
        "anarch": curses.color_pair(18),
        "shaper": curses.color_pair(19),
        "criminal": curses.color_pair(20),
        "heading": curses.color_pair(21),
        "card_header": curses.color_pair(22),
        "empty": curses.color_pair(23),
        "filled": curses.color_pair(24),
        "cost": curses.color_pair(25),
        "standout": curses.color_pair(26),
        "card_bg": curses.color_pair(27),
        "dim": curses.color_pair(28),
        "error": curses.color_pair(29),
        "hotkey": curses.color_pair(30),
        "greenscreen": curses.color_pair(31),
        "yellowscreen": curses.color_pair(32),

    })


def open_netrunnerdb(card):
    if card is None:
        return
    cardid = card.code
    url = "https://netrunnerdb.com/en/card/" + str(cardid)
    if False:
        import subprocess
        subprocess.call(["open", url])
    else:
        webbrowser.open(url) # Sierra bug not my fault


def box(window, color):
    window.attron(color)
    window.box()
    window.attroff(color)
    window.noutrefresh()

class Andeck(object):
    """ Modes:
    N = global commands
    I = entering text in search box
    C = navigating the card list
    H = Help mode
    F = Filter mode
    Z = Card zoom mode
    """

    def __init__(self, stdscr, deck_dir=None, deck_file=None, symbols="unicode"):
        self.screen = stdscr

        self.mode = "N"
        self.stdscr = stdscr
        self.windows = []
        # self.window_arrangement = 1

        self.deck_dir = deck_dir

        self.deck = None
        self.deck_box_on = False
        self.card_display_pos = "bottom"
        self.card_display_on = True
        self.deck_pad = None
        self.deck_pad_top = 0
        self.card_search = None
        self.selected_before = 0
        self.list_search = ""

        self.help_pages = None

        self.config = Config()
        if self.deck_dir is None:
            self.deck_dir = self.config.get("default-deck-dir")
        else:
            self.config.set("default-deck-dir", os.path.abspath(self.deck_dir))

        if os.environ.get("ANR_CARD_DIR", None):
            card_location = os.environ.get("ANR_CARD_DIR")
        else:
            card_location = self.config.get("card-location")

        if not os.path.exists(card_location + "/netrunner-cards-json/pack"):
            self.download_cards(fluff=True)

        self.config.set("card-location", card_location)
        cards.symb = cards.symbols[symbols]
        cards.load_cards(card_dir=card_location + "/netrunner-cards-json")

        self.filter = cards.CardFilter()
        self.old_filter = self.filter

        self.layout = {"card_display": True, "card_display_loc": "bottom", 
                "card_display_big": False}
        self.search_string = ""
        self.cardlist = cards.search("")
        self.selected_card_index = 0
        self.selected_deck_card_index = 0
        self.display_top_row = 0
        self.display_bottom_row = -1
        self.display_card = None

        self.prev_mode = []

        self.card_columns = [
            "title", "faction_code", "cost", "type_code", "faction_cost",
            "pack_code", "text"
        ]
        self.available_columns = self.card_columns + [ 'advancement_cost', 'keywords',
                                  'agenda_points', 'strength', 'trash_cost', 'memory_cost', 'base_link',
                                  'quantity', 'deck_limit', 'uniqueness', 'flavor',
                                  'minimum_deck_size', 'illustrator']
        self.column_hotkeys = {}
        for col in self.available_columns:
            for c in col:
                if c not in self.column_hotkeys:
                    self.column_hotkeys[c] = col
                    break

        self.search_fields = ["title", "text"]
        self.column_widths = defaultdict(lambda: 1)
        self.column_widths.update({
            "title": 25,
            "text": -1,  # Rest of available space
            "type_code": 4,
            "pack_code": 5,
            'illustrator': 40,
            'keywords': 35,
            'flavor': -1
        })
        if deck_file is not None and os.path.exists(deck_file):
            self.deck_box_on = True
            self.deck = cards.Deck.from_file(deck_file)

        self.init_windows()
        self.status("Loaded " + str(len(cards.cards_by_id)) + " cards.")

    def previous_mode(self):
        if len(self.prev_mode) == 0:
            self.normal_mode()
        else:
            mode = self.prev_mode.pop()
            if mode == "I":
                self.search_mode()
            elif mode == "D":
                self.deck_mode()
            elif mode == "C":
                self.list_mode()
            else:
                self.normal_mode()

    def render_top(self):
        win = self.top_panel.window()
        y, x = win.getmaxyx()
        win.addstr(1, 1, " NETRUNNER CONSOLE v0.1",
                          app_styles["heading"])
        win.addstr(1, x - 12, "? for help",
                          curses.A_DIM + app_styles["heading"])

    def render_search(self):
        win = self.search_panel.window()
        y, x = win.getmaxyx()
        win.erase()
        win.addstr(1, 2, "> ")
        win.addstr(self.search_string) # .ljust(x-4))
        if self.mode == "I":
            self.search_panel.top()
        #     self.set_cursor(win, 1, len(self.search_string) + 4)
        style = app_styles['selected' if self.mode == "I" else 'normal']
        box(win, style)

    def render_card_display(self):
        if not self.card_display_on:
            return
        win = self.card_display_panel.window()
        self.do_display_card(win, self.display_card)
        box(win, app_styles['normal'])

    def init_windows(self):
        y, x = self.stdscr.getmaxyx()
        for w in self.windows:
            del w

        # TODO sensible defaults
        card_display_height = 0
        if self.card_display_on:
            card_display_height = 10 if self.layout['card_display_big'] else 7
        deck_box_width = 40
        card_table_height = y - 6 - card_display_height
        search_width = x - 1
        results_width = x - 1

        card_display_width = results_width

        deck_box = curses.newwin(card_table_height,
                                 deck_box_width, 5, x - deck_box_width)
        self.deck_box_panel = panel.new_panel(deck_box)

        if self.deck_box_on:
            results_width -= deck_box_width
        else:
            self.deck_box_panel.bottom()

        top_window = curses.newwin(3, x, 0, 0)
        self.top_panel = panel.new_panel(top_window)
        self.render_top()
        self.windows.append(self.top_panel)

        search_box = curses.newwin(3, search_width, 2, 1)
        self.search_panel = panel.new_panel(search_box)
        search_box.addstr(1, 2, ">")
        # search_box.addstr(1, 4, "'/' to search", curses.A_DIM)
        box(search_box, app_styles['normal'])

        card_table_win = curses.newwin(card_table_height, results_width,
                                            5, 1)
        card_table_panel = panel.new_panel(card_table_win)
        card_table_subwin = card_table_win.derwin(card_table_height - 2,
                results_width - 2, 2, 1)
        box(card_table_win, app_styles['normal'])

        card_display_win = None
        card_display_panel = None
        if self.card_display_on:
            card_display_win = curses.newwin(
                card_display_height,
                card_display_width,
                y - card_display_height - 1,
                1)
            box(card_display_win, app_styles['normal'])
            card_display_panel = panel.new_panel(card_display_win)

        status_bar = self.stdscr.subwin(1, x, y - 1, 0)
        status_bar.attron(curses.A_REVERSE)

        card_window = self.card_window()
        card_zoom_panel = panel.new_panel(card_window)
        card_zoom_panel.bottom()

        filter_window = self.shape_window((20, 70))
        self.filter_panel = panel.new_panel(filter_window)
        self.filter_panel.bottom()

        help_window = None

        self.windows.extend(
            [status_bar, search_box, card_table_win])
        if card_display_win:
            self.windows.append(card_display_win) # TODO

        self.status_bar = status_bar
        self.deck_box = deck_box
        self.help_window = help_window
        self.card_table_panel = card_table_panel
        self.card_table_subwin = card_table_subwin
        self.card_display_panel = card_display_panel
        self.card_zoom_panel = card_zoom_panel

        if(self.deck_box_on):
            self.update_deck_box()
        self.update_card_table()
        self.update_search()

        self.status(" ", x)

        panel.update_panels()


    def card_display_toggle(self):
        self.card_display_on = not self.card_display_on
        self.init_windows()

    def card_display_size_toggle(self):
        self.layout['card_display_big'] = not self.layout['card_display_big']
        self.init_windows()
        self.render_card_display()

    def deck_box_toggle(self):
        self.deck_box_on = (not self.deck_box_on)
        self.init_windows()

    def update_deck_box(self):
        if self.deck_box_on:
            self.render_deck_box()

    def render_deck_box(self, pretty=True):
        deck = self.deck
        win = self.deck_box_panel.window()
        height, width = win.getmaxyx()
        y, x = win.getbegyx()
        win.erase()

        # TODO: store this, don't create each time
        if not self.deck_pad:
            self.deck_pad = curses.newpad(70, width - 2)
        deck_pad = self.deck_pad
        deck_pad.erase()

        card_count = 0
        influence = 0
        wrapper = textwrap.TextWrapper(replace_whitespace=False, width=width - 2)

        if deck is None:
            self.deck = cards.Deck(name="New deck")
            deck = self.deck
            self.status("New deck")
            # deck_pad.addstr(0, 0, "No deck".center(width-2))

        deck_pad.addstr(0, 0, deck.name.center(width-2), app_styles['card_header'])
        deck_pad.addstr(2, 0, "Identity: ",  curses.A_BOLD)
        if deck.identity:
            # deck_pad.addstr("\n".join(wrapper.wrap(deck.identity.title)))
            deck_pad.addstr("\n".join([line.strip() for line in wrapper.wrap(" "*10
                                                                             + deck.identity.title)]))
        else:
            deck_pad.addstr("(None)")
        i = deck_pad.getyx()[0] + 1
        # i = 3
        card_num = 0
        for type_ in cards.Deck.card_types[deck.side]:
            cards_in_type = sum([deck.cards_qty[c] for c in deck.cards_by_type[type_]])
            card_count += cards_in_type
            if pretty and len(deck.cards_by_type[type_]) > 0:
                deck_pad.addstr(i, 1, "\n %s: (%d)" % (
                    cards.attr_to_readable(type_)[0], cards_in_type),
                           curses.A_BOLD)
                i += 2
            for card in sorted(deck.cards_by_type[type_]):

                attr = curses.A_NORMAL
                if card_num == self.selected_deck_card_index and self.mode == "D":
                    attr = curses.A_REVERSE
                    if i > (self.deck_pad_top + height -5):
                        self.deck_pad_top = (i - (height - 5))
                    elif i < self.deck_pad_top:
                        self.deck_pad_top = i
                deck_pad.addstr(i, 0, ("%dx %s" % (deck.cards_qty[card], card.title)), attr)
                if deck.identity and deck.identity.faction_code != card.faction_code and\
                    card.d.get("faction_cost", False):
                    influence += card.faction_cost * deck.cards_qty[card]
                i += 1
                card_num += 1

            if i > self.deck_pad_top + height - 4:
                win.addstr(height - 3, 1, "(More...)")

        deck_pad.overwrite(win, self.deck_pad_top, 0, 1, 1, height - 4, width - 3)
        win.addstr(height - 2, 1, ("%d cards / %d influence" % (card_count, influence)).center(width-2),
                   curses.A_REVERSE)

        box(win, app_styles['selected' if self.mode == "D" else "normal"])
        self.deck_box_panel.top()

    def resize(self):
        self.init_windows()
        self.update_card_table()
        self.update_search()
        self.status("Resized")

    def keystroke(self, c):
        if self.mode == "C":
            self.keystroke_cards(c)
        elif self.mode == "D":
            self.keystroke_deck(c)
        elif self.mode == "I":
            self.keystroke_search(c)

    def keystroke_deck(self, c):
        if c == 10 or c == 32:
            self.zoom_mode()
        if c == ord('n'):
            self.deck = cards.Deck()
            self.deck.name = "New deck"
        elif c == ord('l'): # Load
            filename = FileChooser(self.stdscr, self.deck_dir, "txt").choose()
            if filename is not None and os.path.exists(filename):
                self.deck = cards.Deck.from_file(filename)
                self.status("Loaded " + filename)
                self.config.set("default-deck-dir", os.path.abspath(os.path.dirname(filename)))
            self.card_table_panel.window().touchwin()
        elif c == ord('r'): # Rename
            self.deck.name = InputWindow(self.stdscr, prompt="New deck name:").get_string()
        elif c == ord('s') or c == ord('S'): # Save
            if self.deck.filename is None or c == ord("S"):
                self.deck.filename = self.config.get('default-deck-dir') + os.sep +\
                                    InputWindow(self.stdscr, prompt="Enter filename:").get_string()

            if self.deck.filename is not None:
                result = self.deck.save()
                if result:
                    self.status("Deck saved to " + self.deck.filename)
                else:
                    self.status("ERROR: Couldn't save deck.", app_styles['error'])
            else:
                self.status("ERROR: No filename selected.", app_styles['error'])
        elif c == ord('a') or c == ord('+'):
            card = self.display_card
            if self.deck.add_card(card):
                self.status("Added " + card.title)
            else:
                self.status("Card not added - wrong deck type.", app_styles['error'])
        elif c == ord('x') or c == ord('-'):
            card = self.display_card
            self.deck.remove_card(card)
            self.status("Removed " + card.title)
        elif c == ord('j') or c == curses.KEY_DOWN or c == curses.KEY_NPAGE:
            increment = 10 if c == curses.KEY_NPAGE else 1
            self.selected_deck_card_index = min(
                len(self.deck.cards) - 1, self.selected_deck_card_index + increment)

        elif c == ord('k') or c == curses.KEY_UP or c == curses.KEY_PPAGE:
            increment = 10 if c == curses.KEY_PPAGE else 1
            if self.selected_card_index == 0:
                self.deck_pad_top = max(self.deck_pad_top - increment, 0)
            self.selected_deck_card_index = max(0, self.selected_deck_card_index - increment)
        elif c == ord('K') or c == ord('g') or c == curses.KEY_HOME:
            self.selected_deck_card_index = 0
            self.deck_pad_top = 0
        elif c == ord('G') or c == ord('J') or c == curses.KEY_END:
            self.selected_deck_card_index = len(self.deck.cards) - 1

        if self.deck and self.deck.cards:
            self.display_card = self.deck.cards[self.selected_deck_card_index]

        self.update_deck_box()
        self.render_card_display()

    def keystroke_cards(self, c):
        if self.card_search:
            if c == 10:
                self.card_search = False
            elif c == 27:
                self.card_search = False
                self.selected_card_index = self.selected_before
            else:
                if c == curses.KEY_BACKSPACE or c == 127:
                    self.list_search = self.list_search[:-1]
                else:
                    self.list_search += chr(c)
                start, end, inc = self.selected_before, len(self.cardlist), 1
                if self.card_search == "backwards":
                    start, end, inc = self.selected_before, 0, -1
                for i in range(start, end, inc):
                    if self.list_search.lower() in str(self.cardlist[i].title.lower())\
                            or self.list_search.lower() in str(self.cardlist[i].text.lower()):
                        self.selected_card_index = i
                        break
        else: 
            if c == 10 or c == 32:
                self.zoom_mode()
            elif c == ord('n'):
                open_netrunnerdb(self.display_card)
                return
            elif c == ord('/') or c == ord('?'):
                self.selected_before = self.selected_card_index
                self.card_search = "forwards" if c == ord('/') else "backwards"
                self.list_search = ""
            elif c == ord('I'):
                self.display_image()
                return
            elif c == ord('a') or c == ord('+'):
                card = self.display_card
                if self.deck.add_card(card):
                    self.status("Added " + card.title)
                else:
                    self.status("Card not added - wrong deck type.", app_styles['error'])
                self.update_deck_box()
            elif c == ord('x') or c == ord('-'):
                card = self.display_card
                self.deck.remove_card(card)
                self.status("Removed " + card.title)
                self.update_deck_box()
            elif c == ord('j') or c == curses.KEY_DOWN:
                self.selected_card_index = min(
                    len(self.cardlist) - 1, self.selected_card_index + 1)
            elif c == ord('k') or c == curses.KEY_UP:
                self.selected_card_index = max(0, self.selected_card_index - 1)
            elif c == ord('G') or c == ord('J') or c == curses.KEY_END:
                self.selected_card_index = len(self.cardlist) - 1
            elif c == curses.KEY_NPAGE:
                self.selected_card_index = min(
                    len(self.cardlist) - 1,
                    self.selected_card_index + self.card_table_panel.window().getmaxyx()[0] -
                    4)
            elif c == curses.KEY_PPAGE:
                self.selected_card_index = max(
                    0, self.selected_card_index - self.card_table_panel.window().getmaxyx()[0]
                    + 4)
            elif c == ord('g') or c == ord('K') or c == curses.KEY_HOME:
                self.selected_card_index = 0

        self.update_card_table()
        self.render_card_display()


    def keystroke_filter(self, c):
        if chr(c) in cards.CardFilter.key_to_filter:
            filter_type, string = cards.CardFilter.key_to_filter.get(chr(c))
            self.filter.toggle_filter(filter_type, string)
            self.render_filter()
            return
        elif c == 27:
            self.filter = self.old_filter
            # Reset filter?
            # self.filter.copy() ?
        elif c == 10:
            pass
        elif c == ord("A"):
            items = cards.values_by_key['keywords']
            chosen = [i for i, v in enumerate(cards.values_by_key['keywords']) if \
                    v in self.filter.filter_strings['keywords']]
            selected_keywords = MultipleSelector(self.stdscr, items, message="Keywords:",
                                                 chosen=chosen).choose()
            if selected_keywords is not None:
                self.filter.filter_strings['keywords'] = selected_keywords
                self.filter.update_filter('keywords')
                # for s in selected_keywords:
                #     self.filter.toggle_filter('keywords', s)
            self.render_filter()
            return
        elif c == ord("S"):
            items = [cards.packs_by_code[c] for c in cards.values_by_key['pack_code']]
            chosen = [i for i, v in enumerate(cards.values_by_key['pack_code']) if \
                      v in self.filter.filter_strings['pack_code']]
            selected_keywords = MultipleSelector(self.stdscr, items, message="Set:",
                                                 chosen=chosen).choose()
            if selected_keywords is not None:
                selected_packs = [cards.packs_by_name[n] for n in selected_keywords]
                self.filter.filter_strings['pack_code'] = selected_packs
                self.filter.update_filter('pack_code')
            self.render_filter()
            return
        elif c == ord("R"):
            self.filter.reset()
            self.render_filter()
            return
        else:
            return

        self.update_search()
        self.normal_mode()

    def keystroke_search(self, c):
        y, x = self.stdscr.getyx()
        if c < 0:
            curses.napms(10)
            return
        if c == curses.KEY_BACKSPACE or c == 127:
            if len(self.search_string) > 0:
                self.search_string = self.search_string[0:-1]
        elif c == 10: # Enter
            self.normal_mode()
            return
        elif c == 9:  # TAB
            # Do nothing
            return
        else:
            # Add a printable character to the string
            if c > 0 and c < 255:
                # self.stdscr.addch(y, x, c)
                # self.stdscr.move(y, x + 1)
                self.search_string += chr(c)
                self.status(str(c))

        self.selected_card_index = 0
        self.render_search()
        self.update_search()

    def status(self, message, attr=None):
        bar = self.status_bar
        if attr:
            bar.attron(attr)
        y, x = self.stdscr.getmaxyx()
        bar.addstr(0, 0, message.center(x - 1, " "))
        bar.refresh()
        if attr:
            bar.attroff(attr)

    def search_mode(self, append=False):
        self.mode = "I"
        if not append:
            self.search_string = ""
            self.update_search()
        curses.curs_set(True)
        self.render_search()
        self.status("Search mode")


    def filter_mode(self):
        self.mode = "F"
        self.old_filter = deepcopy(self.filter)
        self.render_filter()
        self.filter_panel.top()

    def DELETE_render_columns(self):
        win = self.columns_panel.window()

        win.addstr(2, 1, "Select table columns:", curses.A_BOLD)
        i = 0
        for col in self.available_columns:
            if col in self.card_columns:
                win.addstr(4 + (i % 9), 2 + (i//9 * 24),  col)
            else:
                pass
            i += 1

        win.addstr(16, 3, "R", curses.A_BOLD)
        win.addstr(" Reset columns")
        win.addstr("   <Enter>", curses.A_BOLD)
        win.addstr(" Apply columns")
        win.addstr("   <ESC>", curses.A_BOLD)
        win.addstr(" Cancel")

        self.columns_panel.top()

        box(win, app_styles['selected'])

    def _hotkey(self, sort_key, value):
        for k, v in cards.CardFilter.key_to_filter.items():
            if v == (sort_key, value):
                return k
        return None


    def _filter_item(self, win, line, col, key, value):
        selected = (value in self.filter.filter_strings[key])
        hk = self._hotkey(key, value)
        # if hk:
        win.addstr(line, col, hk + " ", app_styles['hotkey'])
        # else:
        #     win.addstr("  ", app_styles['hotkey'])
        if selected:
            win.addstr("(*)", curses.A_BOLD)
        else:
            win.addstr("( )", curses.A_NORMAL)
        win.addstr(" " + cards.attr_to_readable(value)[0])

    def render_filter(self):
        win = self.filter_panel.window()

        win.addstr(2, 1, "Faction", curses.A_BOLD)
        for i, faction in enumerate(["haas-bioroid", "weyland-consortium", "nbn", "jinteki",
            "neutral-corp"]):
            self._filter_item(win, i+3, 1, 'faction_code', faction)

        for i, faction in enumerate(["anarch", "criminal", "shaper", "neutral-runner"]):
            self._filter_item(win, i+3, 17, 'faction_code', faction)

        win.addstr(8, 1, "Side", curses.A_BOLD)
        for i, side in enumerate(["runner", "corp"]):
            self._filter_item(win, 9, i*15 + 1, 'side_code', side)

        win.addstr(2, 35, "Type", curses.A_BOLD)
        for i, type_ in enumerate(["agenda", "asset", "event", "hardware", "ice",
                                   "identity", "operation", "program", "resource",
                                   "upgrade"]):
            self._filter_item(win, i%5 + 3, 35 + (i//5) * 16, 'type_code', type_)

        win.addstr(9, 33, "A", app_styles['hotkey'])
        win.addstr(9, 35, "Subtype", curses.A_BOLD)
        subtype_string = "(None)" if len(self.filter.filter_strings['keywords']) == 0\
            else (",".join(self.filter.filter_strings['keywords']))
        if len(subtype_string) > 30:
            subtype_string = subtype_string[0:27] + "..."
        win.addstr(10, 35, subtype_string.ljust(30))

        win.addstr(12, 33, "S", app_styles['hotkey'])
        win.addstr(12, 35, "Card set:", curses.A_BOLD)
        pack_string = "(None)" if len(self.filter.filter_strings['pack_code']) == 0 \
            else (",".join(self.filter.filter_strings['pack_code']))
        if len(pack_string) > 30:
            pack_string = pack_string[0:27] + "..."
        win.addstr(13, 35, pack_string.ljust(30))

        win.addstr(16, 1, "R", curses.A_BOLD)
        win.addstr(" Reset filters")
        win.addstr("   <Enter>", curses.A_BOLD)
        win.addstr(" Apply filters")
        win.addstr("   <ESC>", curses.A_BOLD)
        win.addstr(" Cancel")


        self.filter_panel.top()

        box(win, app_styles['selected'])

    def normal_mode(self):
        curses.curs_set(False)
        self.mode = "N"
        self.render_search()
        self.update_card_table()
        self.update_deck_box()
        self.card_table_panel.top()
        self.filter_panel.bottom()
        self.status("")

    def zoom_mode(self):
        self.prev_mode.append(self.mode)
        self.mode = "Z"
        self.do_display_card(self.card_zoom_panel.window(),
                             self.display_card, verbose=True)
        self.card_zoom_panel.top()

    def help_mode(self):
        if self.help_pages is None:
            self.help_pages = []
            pagename = None
            pagetext = ""
            with open(os.path.dirname(__file__) + os.sep + "../help/help.txt", "r") as f:
                lines = f.readlines()
            for l in lines:
                if l.startswith("# "):
                    if pagename:
                        self.help_pages.append((pagename, pagetext))
                        pagetext = ""
                    pagename = l[2:].strip()
                else:
                    pagetext += l
        TextPager(self.stdscr, self.help_pages, (30, 60)).show()
        self.render_card_display()
        self.normal_mode()

    def shape_window(self, ideal_size):
        maxy, maxx = self.stdscr.getmaxyx()
        if maxy >= ideal_size[0] and maxx >= ideal_size[1]:
            height, width = ideal_size
        else:
            if maxy < ideal_size[0]:
                height = maxy
                width = min(maxx, ideal_size[1] + 10)
            else:
                width = maxx
                height = min(maxy, ideal_size[0] + 10)
        # Center on screen
        y = int((maxy - height) / 2)
        x = int((maxx - width) / 2)
        win = curses.newwin(height, width, y, x)
        box(win, app_styles['normal'])
        return win


    def filter_window(self):
        return self.shape_window((30, 70))


    def card_window(self):
        return self.shape_window((25, 45))

    def deck_mode(self):
        self.mode = "D"
        self.update_deck_box()

    def list_mode(self):
        self.mode = "C"
        # box(self.card_table_panel.window(), app_styles['selected'])
        self.update_card_table()
        self.render_card_display()

    def update_search(self):
        try:
            search_terms = shlex.split(self.search_string)
        except ValueError:
            try:
                search_terms = shlex.split(self.search_string.replace("'", '').replace('"', ''))
            except ValueError:
                search_terms = self.search_string
        self.cardlist = cards.search(search_terms, op="and")
        self.cardlist = self.filter.filter(self.cardlist)
        self.cardlist.sort()
        self.selected_card_index = 0

        self.update_card_table()

    def update_cardlist_display(self):
        win = self.card_table_subwin
        height, width = win.getmaxyx()
        win.erase()
        for i in range(height - 1):
            if i >= len(self.cardlist):
                break
            row = i
            cardindex = min(len(self.cardlist)-1, self.display_top_row + i)
            card = self.cardlist[cardindex]
            attr = curses.A_NORMAL
            if self.mode == "C" and cardindex == self.selected_card_index:
                attr = curses.A_REVERSE
            self.render_card(win, row, card, attr)

    def update_display_card(self):
        if len(self.cardlist) == 0:
            return
        if self.selected_card_index >= len(self.cardlist):
            self.selected_card_index = 0
        self.display_card = self.cardlist[self.selected_card_index]

    def update_card_table(self):
        # Window gets column headers
        #TODO: Not sure why this check is needed, debug
        self.update_display_card()
        window = self.card_table_panel.window()
        window.erase()
        height, width = window.getmaxyx()
        attrs = curses.A_BOLD + curses.A_UNDERLINE
        remaining_space = width - 2  # Room for box
        for col in self.card_columns:
            w = self.column_widths[col]
            if w > 0:
                remaining_space -= w + 1

        window.move(1, 1)
        for col in self.card_columns:
            w = self.column_widths[col]
            if w == -1:
                w = remaining_space
            to_show = cards.attr_to_readable(col)
            if len(to_show[0]) > w:
                to_show = to_show[1]
            else:
                to_show = to_show[0]
            window.addstr(to_show[0:w].center(w, " "),
                          attrs)
            if col != self.card_columns[-1]:
                window.addstr(" ", attrs - curses.A_UNDERLINE)

        bottom = 5 if self.card_search else 4
        if self.selected_card_index < self.display_top_row:
            self.display_top_row = self.selected_card_index
        elif self.selected_card_index >= self.display_top_row + height - bottom:
            self.display_top_row = self.selected_card_index - height + bottom

        self.update_cardlist_display()

        box(window, app_styles['selected' if self.mode == "C" else 'normal'])

        if self.mode == "C" and self.card_search:
            searchchar = "/" if self.card_search == "forwards" else "?"
            window.addstr(height - 2, 1, searchchar + self.list_search.ljust(width -2),
                    curses.A_REVERSE)

        if self.mode == "C":
            message = (" " + str(self.selected_card_index+1) + " of " +
                       str(len(self.cardlist)) + " cards ")
            if window.getmaxyx()[1] > len(message):
                window.addstr(height - 1, width - (4 + len(message)), "──",
                              app_styles['selected'])  # A hack; TODO
                window.addstr(height - 1, width - (2 + len(message)), message)
        else:
            window.addstr(height - 1, width - 14, (
                " " + str(len(self.cardlist)) + " cards ").rjust(12, "─"))
                                        

    def do_display_card(self, win, card, verbose=False):
        h, w = win.getmaxyx()

        # TODO Styles everywhere
        # TODO: This doesn't seem to work, not sure why
        # win.attrset(app_styles['card_bg'])
        # win.bkgdset(' ', app_styles['card_bg'])

        win.erase()
        if card is None:
            win.addstr(1, 1, "No card")
            return
        win.addstr(1, 1,
                   card.title.center(w - 2, " "), app_styles['card_header'])
        win.addstr(1, 1, "[" + str(card.d.get('cost', "-")) + "]",
                   app_styles['cost'])

        card_type = card.type_code
        win.addstr(2, 1, card.printable("type_code", verbose=verbose), curses.A_BOLD)
        if card.d.get("keywords", None):
            win.addstr(": " + card.printable("keywords", verbose=verbose))
        if card_type == "agenda":
            win.addstr(" - AC/AP: %d/%d" % (card.advancement_cost, card.agenda_points))
        elif card.d.get("strength", None) is not None:
            win.addstr(" - ST: %d" % (card.strength), curses.A_BOLD)
        if card.d.get("trash_cost", None) is not None:
            win.addstr("  Trash: %d" % (card.trash_cost))
        if card.d.get("memory_cost", None) is not None:
            win.addstr("  MU: %d" % (card.memory_cost))

        win.addstr(3, 1, card.printable("faction_code", verbose=verbose),
                   app_styles.get(card.faction_code, 0))
        influence = card.d.get("faction_cost", None)
        if influence is not None:
            win.addstr(" (")
            win.addstr("●" * card.faction_cost, app_styles['filled'])
            win.addstr("●" * (5 - card.faction_cost), app_styles['empty'])
            win.addstr(")")

        # win.addstr(2, 16, "Cost: ", curses.A_BOLD)
        # win.addstr(2, 22, str(card.d.get('cost', "-")))


        # win.addstr(2, 25,
        #            card.printable('type_code', verbose=verbose),
        #            curses.A_BOLD)


        text_win_height = h - 4
        subwin = win.derwin(text_win_height, w - 3, 4, 1)

        wrapper = textwrap.TextWrapper(replace_whitespace=False, width= w - 4)
        text_lines = card.get_formatted(
            "text", replace_newlines=False).split("\n")
        cardtext = []
        for line in text_lines:
            cardtext.extend(wrapper.wrap(line))
        if len(cardtext) > text_win_height:
            cardtext = cardtext[0:text_win_height]
            cardtext[-1] = cardtext[-1] + " (cont...)"
            # cardtext[-1] = cardtext[-1][0:-4] + "..."

        if verbose:
            subwin.move(1, 0)
        try:
            subwin.addstr("\n".join(cardtext[0:text_win_height]))
        except curses.error:
            error_log(card.title)
            error_log("|| \n".join(cardtext))

        if verbose:
            # Flavor text
            remaining_lines = text_win_height - len(cardtext)
            if remaining_lines > 1:
                flavor_text = []
                for line in wrapper.wrap(card.d.get("flavor", "")):
                    flavor_text.extend(line.split("\n"))
                subwin.addstr(text_win_height - len(flavor_text) - 1, 0,
                              "\n".join(flavor_text[0:remaining_lines - 1]),
                              curses.A_UNDERLINE + app_styles['dim'])

        style = app_styles['normal']
        if self.mode == "Z":
            style = app_styles['selected'] # TODO bug
        box(win, style)

    def render_card(self, win, i, card, gattr):
        height, width = win.getmaxyx()
        attr = gattr
        x = 0
        for col in self.card_columns:
            w = self.column_widths[col]
            if w < 0:
                w = width - x - 2

            final_attr = self.format(col, card, attr)
            if col in ['title', 'text']:
                string = card.get_formatted(col)
            else:
                string = card.printable(col, verbose=False)
            if len(string) > w and w > 7:
                string = string[0:w - 3] + "..."
            string = string[0:w]
            # error_log("%d %d %d %d" % (height, width, i, x))
            if x + w < width:
                try:
                    win.addstr(
                        i,
                        x,
                        string.ljust(w, " ") + " ",
                        # card.get_formatted(col)[0:w].ljust(w, " ") + " ",
                        final_attr)  # TODO
                    x += w + 1
                except curses.error:
                    pass # OK, don't render it

    def format(self, field, card, attr):
        if attr == curses.A_REVERSE:
            return attr
        if field == "title":
            attr += curses.A_BOLD
            # attr += curses.A_BOLD  #+ curses.color_pair(5)
            attr += app_styles[card.side_code]
        elif field == "text":
            attr += curses.A_NORMAL
        attr += app_styles.get(card.d.get(field, None), 0)
        return attr

    def toggle_filter_runnercorp(self, side):
        if side in self.filter.filter_strings['side_code']:
            self.filter.remove_filter('side_code', side)
        else:
            self.filter.add_filter('side_code', side)

        self.update_search()

    def toggle_filter_corp(self):
        self.toggle_filter_runnercorp("corp")

    def toggle_filter_runner(self):
        self.toggle_filter_runnercorp("runner")

    def display_image(self):
        card = self.display_card
        if card is None:
            return
        cardid = card.code
        image_file = self.config.config_dir + "/images/" + str(cardid) + '.png'
        if os.path.exists(image_file):
            webbrowser.open("file://" + image_file)
        else:
            webbrowser.open("https://netrunnerdb.com/card_image/" + str(cardid) + ".png")

    def show_fluff(self, progress_track):
        stdscr = self.stdscr
        start = 12
        stdscr.addstr(start, 20, "### WELCOME TO NETRUNNER CONSOLE, $runner! ###", app_styles['greenscreen'] + curses.A_REVERSE)
        stdscr.addstr(start + 2, 20, "> No card datafiles detected...", app_styles['greenscreen'])
        stdscr.refresh()
        curses.doupdate()
        time.sleep(1)
        stdscr.addstr(start + 3, 20, "> Accessing corp network...", app_styles['greenscreen'])
        stdscr.refresh()
        curses.doupdate()
        curses.napms(1500)
        stdscr.addstr(start + 4, 20, "> Bypassing ICE...", app_styles['greenscreen'])
        stdscr.refresh()
        curses.doupdate()
        curses.napms(1750)
        stdscr.addstr(" SUCCESS", app_styles['yellowscreen'] + curses.A_BOLD)
        stdscr.refresh()
        curses.doupdate()
        curses.napms(750)
        stdscr.addstr(start + 5, 20, "> Downloading card data: ", app_styles['greenscreen'])
        stdscr.refresh()
        i = 0
        while(not os.path.exists(self.config.get('card-location') + "/netrunner-cards-json/pack/core.json")):
            progress = progress_track.get('progress', None)
            if progress:
                stdscr.addstr(start + 5, 45, "%02d%%" % (int(100*progress)))
            else:
                stdscr.addstr(start + 5, 45, "."*i, app_styles['greenscreen'] + curses.A_BLINK)
            i += 1
            time.sleep(1)
            stdscr.refresh()

        stdscr.refresh()
        stdscr.erase()

    def download_cards(self, fluff=False):
        progress_track = {}
        t = threading.Thread(target=cards.download_cards, args=([self.config.get('card-location'), 
            progress_track]))
        t.deamon = True
        t.start()
        if fluff:
            self.show_fluff(progress_track)
        return progress_track

    def redownload(self):
        if(ConfirmCancel(self.stdscr, "Redownload cards?").show()):
            self.normal_mode()
            progress = self.download_cards(fluff=False)
            while progress.get('progress', None) is None:
                time.sleep(0.3)
            while progress['progress'] < 1.0:
                self.status("Downloading... %d%%" % (int(100*progress['progress'])))
            self.normal_mode()
            Dialog(self.stdscr, "Cards downloaded successfully.")

if __name__ == "__main__":
    curses.wrapper(main)

def startapp():
    # sys.stderr.close()
    curses.wrapper(main)
