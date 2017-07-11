# Netrunner Console

Fast, terminal-based *Android: Netrunner* card database and deck editor.

To help test, a web version *may* available here: http://console.coljac.space

## Installation

**Netrunner Console** requires Python 3 and support for the curses library, which should work out of the box on any Unix or Mac OS system. Because of spotty support for ncurses, Microsoft Windows support is a little tricky, and is still being worked on.

Download or clone the repository, then run:

`python setup.py install`

### Card data
The card information is taken from zaroth's [handy repository](https://github.com/zaroth/netrunner-cards-json). You can point **Netrunner Console** at an existing copy of this data, or it will download the data on first run. Updating the cards can be done 
Łukasz Dobrogowski

## Configuration

By default, Netrunner Console will store some settings in `$HOME/.config/netrunner-console` or `$HOME/.netrunner-console`.  Card data (~8MB) will be downloaded there also unless a card directory is specified with the environment variable 
`ANR_CARD_DIR` which should contain `netrunner-cards-json` as per the above project. The location will be stored for subsequent runs.

If a directory is passed as an argument to the script (e.g. `netrunner-console ~/Documents/anrdecks`), it will be used as the default deck location. Subsequently, the location of the last deck opened will be used as the default directory.

If you pass the `-a` flag to the command (i.e. `netrunner-console -a`) it will use ascii instead of some unicode symbols for things like the credit, click and baselink symbols on cards. Use this if things look weird.

## Quick start

- `> netrunner-console` to start
- App will download the card data
- App will start with a search bar, list of all *Android: Netrunner* cards, and an empty card detail window down the bottom
- Use arrow keys, page up/down, home/end to navigate the card list and see more detail in the card display window
- Press `<SPACE>` or `<ENTER>` on a card to "zoom" for easier reading
- Hit `<ESC>` then `/`. Type `credits`, card list will show filtered results
- Hit `<ENTER>`. Hit `r` to toggle runner cards only on/off
- Hit `q` to exit the app

## How to use

First things first:

- Detailed help with all keyboard commands can be accessed by pressing `?`. 
- Quit the app by pressing `<ESC>` then `q`

As a terminal-based application, Netrunner Console is designed to be operated efficiently with the keyboard. It can operate in several modes that have different keyboard shortcuts:

- *Normal mode*, `<ESC>`: Default mode. `q` quits from normal mode. (Hi *vim* users)
- *Search mode*, `i` or `/`: For typing in a search string. Search results are applied dynamically.
- *List mode*, `j`, `k` or arrow keys: For navigating the list of cards, and adding/subtracting from a deck
- *Deck mode*, `D`: The deck box is highlighted; for loading/saving/renaming a deck, adding and subtracting cards.

In addition, `f` brings up a filter screen (card faction, side, set, keywords, etc), `t` allows you to customise the table view.

In normal mode, `w` toggles the card detail window; `W` toggles its size (small/large); `d` toggles the deck display.

## Deck formats

Card files in any text format should work if they contain card names alone on a line except for a quantity (`1, 2` or `1x, 2X`) or the string `Identity:`. Other lines will be treated as comments, except for the first which will be used as the deck name if is not a card. See `examples/`.

## Demo

[![asciicast](https://asciinema.org/a/128404.png)](https://asciinema.org/a/128404)

## Development status

I consider the app to be in the testing phase at the moment (July 2017) - I expect crashes and other significant bugs still to be found. Future version focused on stability will come in short order and a 1.0 release will be made and uploaded to pypi.

For subsequent versions, planned enhancements include:

- Documented Windows support
- Sorting the card list 
- Advanced search with boolean operators and card fields
- Integration with netrunnerdb and jinteki.net stored decks
- Potentially build out and properly support the web-based version
- Improved colours and colour schemes
- More customisable layout options
- Performance and usability improvements

**Bug reports/pull requests are welcome.**
