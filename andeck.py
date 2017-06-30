#!env python3

import curses
# from PIL import Image
import sys
import cards
from cards import Deck, Card
# import time
import os
import textwrap
from curses import panel
import webbrowser
from curses_utils import FileChooser

os.environ.setdefault('ESCDELAY', '15')

# PANELS FORK #######
# BUG: ] in search = crash
# BUG: empty string not clearing search
# BUG: Not resizing until keypress
# BUG: init_win doesn't preserve state properly e.g. display_top
# BUG: Can't set background color properly
# Bug: credit symbol in two places (see col headers)
# BUG: deck box stays highlighted
# Alpha 1 todos:
# TODO: Deck window size
# TODO: Helps screen
# TODO: Scroll deck, scroll file chooser
# TODO: Some sort of config
# TODO: Filter page
# TODO: Table columns

# Version 1 todos:
# TODO: Search with / in card list view
# TODO: Nicer colors
# TODO: Layout swap with card viewer

# Other todos:
# TODO move card display window to side
# TODO: Dynamically determine verbosity
# TODo: Refershing single lines only
# TODO: dynamic help at bottom
# TODO: first down-press doesn't initiate card view
# TODO config panel
# TODO: Saveable layout
# TODO change columns
# TODO advanced search / filters
# TODO images - fancy style with window and caching
# TODO optional unicode characters
# TODO config file
# TODO: cache, sqlite
# TODO Help text
# TODO deckbuilding
# todo layouts
# TODO /search in card list
# TODO sort or
# TODO: Themes
# TODO: SHift tab
# TODO: Load cards in bg thread

# Wishlist: Run HQ; card ascii art

def error_log(string):
    with open("/tmp/error.log", "a") as log:
        log.write(string + "\n")


app_styles = {}


def main(stdscr):
    # stdscr.border(0)
    curses.curs_set(False)
    curses.use_default_colors()
    # stdscr.nodelay(1)

    init_app_colors()

    cardapp = Andeck(stdscr)
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
            elif c == 27:
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
                elif c == "t":
                    cardapp.table_mode()
                elif c == ord('w'):
                    cardapp.card_display_toggle()
                elif c == ord('c'):
                    cardapp.toggle_filter_corp()
                elif c == ord('r'):
                    cardapp.toggle_filter_runner()
                elif c == ord('d'):
                    cardapp.deck_box_toggle()
                else:
                    curses.napms(10)
            elif cardapp.mode == "Z":
                cardapp.previous_mode()
                cardapp.card_zoom_panel.bottom()
            else:
                cardapp.keystroke(c)

            # cardapp.search_panel.top()
            panel.update_panels()
            curses.doupdate()
        except Exception as e:
            import traceback
            tb = sys.last_traceback()
            with open("/tmp/error_log", "a") as err:
                traceback.print_tb(tb, 100, err)
            # error_log("Unexpected error:" + str(sys.exc_info()))
            # error_log(str(e))
            break

    sys.exit(0)


def init_app_colors():

    curses.init_pair(1, 228, -1)
    curses.init_pair(2, 4, -1)
    curses.init_pair(3, 1, -1)
    curses.init_pair(4, 202, -1)
    curses.init_pair(5, 226, -1)
    curses.init_pair(6, 146, -1)
    curses.init_pair(7, 151, -1)
    curses.init_pair(8, 214, -1)
    curses.init_pair(9, 76, -1)
    curses.init_pair(10, 39, -1)
    curses.init_pair(11, 11, -1)
    curses.init_pair(12, 6, 246)
    # curses.init_pair(12, 232, 246)  # 15)
    curses.init_pair(13, 236, -1)
    curses.init_pair(14, 87, -1)
    curses.init_pair(15, 227, 246)
    curses.init_pair(16, 18, 231)
    curses.init_pair(17, -1, 16)
    curses.init_pair(18, 250, -1)
    curses.init_pair(19, 12, 1)

    app_styles.update({
        "normal": curses.color_pair(0),
        "selected": curses.color_pair(1),  # + curses.A_BOLD,
        "corp": curses.color_pair(2),
        "runner": curses.color_pair(3),
        "jinteki": curses.color_pair(4),
        "nbn": curses.color_pair(5),
        "haas-bioroid": curses.color_pair(6),
        "weyland-consortium": curses.color_pair(7),
        "anarch": curses.color_pair(8),
        "shaper": curses.color_pair(9),
        "criminal": curses.color_pair(10),
        "heading": curses.color_pair(11),
        "card_header": curses.color_pair(12),
        "empty": curses.color_pair(13),
        "filled": curses.color_pair(14),
        "cost": curses.color_pair(15),
        "standout": curses.color_pair(16),
        "card_bg": curses.color_pair(17),
        "dim": curses.color_pair(18),
        "error": curses.color_pair(19),

    })


def open_netrunnerdb(card):
    if card is None:
        return
    cardid = card.code
    url = "https://netrunnerdb.com/en/card/" + str(cardid)
    if True:
        import subprocess
        subprocess.call(["open", url])
    else:
        webbrowser.open(url) # Sierra bug not my fault

def display_image(card):
    if card is None:
        return
    cardid = card.code
    image = "./images/" + str(cardid) + '.png'
    webbrowser.open("file://" + image)

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
    Z = Card zoom mode
    """

    def __init__(self, stdscr):
        self.screen = stdscr

        self.mode = "N"
        self.decklist_on = False
        self.stdscr = stdscr
        self.windows = []
        # self.window_arrangement = 1

        self.deck = None
        self.deck_box_on = False
        self.card_display_pos = "bottom"
        self.card_display_on = True
        self.deck_pad = None
        self.deck_pad_top = 0

        cards.load_cards()

        self.filters = []
        self.layout = {"card_display": True, "card_display_loc": "bottom"}
        self.search_string = ""
        self.cardlist = cards.search("")
        self.selected_card_index = 0
        self.selected_deck_card_index = 0
        self.display_top_row = 0
        self.display_bottom_row = -1
        self.display_card = None

        self.prev_mode = []

        # self.card_columns = ["title", "side_code", "type_code", "text"]
        # self.card_columns = ["title", "type_code", "text"]

        # Title   Faction     Type    …   Subtype •   Set

        self.card_columns = [
            "title", "faction_code", "cost", "type_code", "faction_cost",
            "pack_code", "text"
        ]
        self.search_fields = ["title", "text"]
        self.column_widths = {
            "title": 25,
            "text": -1,  # Rest of available space
            "side_code": 1,
            "type_code": 4,
            "cost": 1,
            "faction_code": 1,
            "faction_cost": 1,
            "pack_code": 5
        }

        self.init_windows()
        self.status("Loaded " + str(len(cards.cards_by_id)) + " cards." + chr(7103)+"!")

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
        card_display_height = 7 if self.card_display_on else 0
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

    def deck_box_toggle(self):
        # self.deck = Deck.from_file("decks/anti_andy.txt")
        self.deck_box_on = (not self.deck_box_on)
        self.init_windows()

    def update_deck_box(self):
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
            self.deck = Deck(name="New deck")
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
        for type_ in Deck.card_types[deck.side]:
            cards_in_type = sum([deck.cards_qty[c] for c in deck.cards_by_type[type_]])
            card_count += cards_in_type
            if pretty and len(deck.cards_by_type[type_]) > 0:
                deck_pad.addstr(i, 1, "\n %s: (%d)" % (
                    cards.attr_to_readable[type_][0], cards_in_type),
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
                win.addstr(height - 3, 0, "(More...)")

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
            self.deck = Deck()
            self.deck.name = "New deck"
        elif c == ord('l'): # Load
            filename = FileChooser(self.stdscr, "./decks/").choose()
            if filename is not None:
                self.deck = Deck.from_file(filename)
                self.status("Loaded " + filename)
            self.card_table_panel.window().touchwin()
        elif c == ord('s'): # Save
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
        if c == 10 or c == 32:
            self.zoom_mode()
        elif c == ord('n'):
            open_netrunnerdb(self.display_card)
            return
        elif c == ord('i'):
            display_image(self.display_card)
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
        # elif c == ord('r'):
        # self.toggle_filter_runner()
        # elif c == ord('c'):
        # self.toggle_filter_corp()

        self.update_card_table()
        self.render_card_display()

    def keystroke_search(self, c):
        # error_log(str(c))
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


    def table_mode(self):
        self.render_table_edit()
        self.table_edit_panel.top()

    def filter_mode(self):
        self.render_filter()
        self.filter_panel.top()

    def render_filter(self):
        pass

    def normal_mode(self):
        curses.curs_set(False)
        self.mode = "N"
        self.render_search()
        self.update_card_table()
        self.update_deck_box()

        self.status("")

    def zoom_mode(self):
        self.prev_mode.append(self.mode)
        self.mode = "Z"
        self.do_display_card(self.card_zoom_panel.window(),
                             self.display_card, verbose=True)
        self.card_zoom_panel.top()

    def help_mode(self):
        self.prev_mode.append(self.mode)
        self.mode = "H"
        self.help_window = self.makehelp()
        self.help_window.refresh()
        self.help_window.getch()
        del self.help_window
        self.normal_mode()

    def filter_window(self):
        ideal_size = [30, 70]

    def card_window(self):
        ideal_size = [25, 45]
        maxy, maxx = self.stdscr.getmaxyx()
        # height, width = ideal_size
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

    def makehelp(self):
        maxy, maxx = self.stdscr.getmaxyx()
        height, width = 20, 40
        y = int((maxy - height) / 2)
        x = int((maxx - width) / 2)
        win = curses.newwin(20, 40, y, x)
        # , app_styles['normal'])
        win.addstr(1, 1, self.get_help_text())
        box(win, app_styles['selected'])
        return win

    def deck_mode(self):
        self.mode = "D"
        self.update_deck_box()

    def list_mode(self):
        self.mode = "C"
        # box(self.card_table_panel.window(), app_styles['selected'])
        self.update_card_table()
        self.render_card_display()

    def update_search(self):
        self.cardlist = cards.search(self.search_string)
        for fil in self.filters:
            self.cardlist = fil(self.cardlist)
        self.cardlist.sort()
        self.selected_card_index = 0

        self.update_card_table()

    def update_cardlist_display(self):
        win = self.card_table_subwin
        height, width = win.getmaxyx()
        win.erase()
        for i in range(height):
            if i >= len(self.cardlist):
                break
            row = i
            cardindex = self.display_top_row + i
            card = self.cardlist[cardindex]
            attr = curses.A_NORMAL
            if self.mode == "C" and cardindex == self.selected_card_index:
                attr = curses.A_REVERSE
            self.render_card(win, row, card, attr)

    def update_card_table(self):
        # Window gets column headers
        self.display_card = self.cardlist[self.selected_card_index]
        window = self.card_table_panel.window()
        height, width = window.getmaxyx()
        attrs = curses.A_BOLD + curses.A_UNDERLINE
        remaining_space = width - 2  # Box
        for col in self.card_columns:
            w = self.column_widths[col]
            if w > 0:
                remaining_space -= w + 1

        window.move(1, 1)
        for col in self.card_columns:
            w = self.column_widths[col]
            if w == -1:
                w = remaining_space
            window.addstr(cards.attr_to_readable[col][1][0:w].center(w, " "),
                          attrs)
            if col != self.card_columns[-1]:
                window.addstr(" ", attrs - curses.A_UNDERLINE)

        if self.selected_card_index < self.display_top_row:
            self.display_top_row = self.selected_card_index
        elif self.selected_card_index >= self.display_top_row + height - 3:
            self.display_top_row = self.selected_card_index - height + 3

        self.update_cardlist_display()

        box(window, app_styles['selected' if self.mode == "C" else 'normal'])

        if self.mode == "C":
            #TODO fix
            message = (" " + str(self.selected_card_index+1) + " of " +
                       str(len(self.cardlist)) + " cards ")
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
        except Exception:
            error_log(card.title)
            error_log("|| \n".join(cardtext))

        if verbose:
            # Flavor text
            remaining_lines = text_win_height - len(cardtext)
            if remaining_lines > 1:
                flavor_text = wrapper.wrap(card.d.get("flavor", ""))
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
            win.addstr(
                i,
                x,
                string.ljust(w, " ") + " ",
                # card.get_formatted(col)[0:w].ljust(w, " ") + " ",
                final_attr)  # TODO
            x += w + 1

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

    def toggle_filter_runnercorp(self, filter_rc):
        if filter_rc in self.filters:
            self.filters.remove(filter_rc)
        else:
            self.filters.append(filter_rc)

        if filter_runner in self.filters and filter_corp in self.filters:
            self.filters.remove(filter_runner)
            self.filters.remove(filter_corp)
        self.update_search()

    def toggle_filter_corp(self):
        self.toggle_filter_runnercorp(filter_corp)

    def toggle_filter_runner(self):
        self.toggle_filter_runnercorp(filter_runner)

    def get_help_text(self):
        return """
        This is the help text.

        i: Search (new search)
        /: Search (edit search)

        j,k: Navigate card
        Key: command
        Key: command
"""
    def get_filter_text(self):
        return """
 Faction                            Type                    
 5. ( ) NBN       6. ( ) Anarch     a. ( ) Resource  f. ( ) Agenda          
 2. ( ) Haas      7. ( ) Criminal   b. ( ) Hardware  g. ( ) Asset
 3. ( ) Weyland   8. ( ) Shaper     d. ( ) Program   h. ( ) Upgrade                          
 4. ( ) Jinteki                     e. ( ) Event     i. ( ) Operation        
                                                                    
 Side                                Subtype: s. [___________]                                             
 r. (*) Runner
 c. ( ) Corp
 
 R: Reset   Esc: Cancel     Enter: Apply 
"""

def filter_faction(faction, cardset):
    return cards.search(faction, fields=['faction_code'], cardset=cardset)


def filter_type(ctype, cardset):
    return cards.search(ctype, fields=['type'], cardset=cardset)


def filter_runner(cardset):
    return cards.search("runner", fields=['side_code'], cardset=cardset)


def filter_corp(cardset):
    return cards.search("corp", fields=['side_code'], cardset=cardset)


if __name__ == "__main__":
    curses.wrapper(main)
