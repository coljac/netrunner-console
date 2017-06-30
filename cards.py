#!env python3

import json
import glob
import os
import re
# import sys
import requests
import shutil
from colorama import Fore, Back, Style
from collections import defaultdict

dbpath = os.environ.get("HOME") + "/build/netrunner-cards-json"
imgurl = "https://netrunnerdb.com/card_image/"
image_loc = "./images"

cards_by_id = {}
cards_by_name = {}

trace_re = re.compile(r"<trace>[Tt]race (.)</trace>")
cardline = re.compile(r'^\s*(\d[xX]?)?\s*([\w "\-:.]*)\s*(\(.*\))?\W*$')

attr_to_readable = {
    "title": ("Card", "Card"),
    "text": ("Text", "Text"),
    "side_code": ("Side", "S"),
    "faction_code": ("Faction", "F"),
    "faction_cost": ("Influence", "●"),  #•
    "pack_code": ("Set", "Set"),
    "flavor": ("Flavor", "Flavor"),
    "type_code": ("Type", "Type"),
    "weyland-consortium": ("Weyland", "W"),
    "nbn": ("NBN", "N"),
    "jinteki": ("Jinteki", "J"),
    "haas-bioroid": ("Haas", "H"),
    "anarch": ("Anarch", "A"),
    "shaper": ("Shaper", "S"),
    "criminal": ("Criminal", "C"),
    "neutral-runner": ("Neutral", "-"),
    "neutral-corp": ("Neutral", "-"),
    "apex": ("Apex", "A"),
    "adam": ("Adam", "Ad"),
    "sunny-lebeau": ("Sunny Lebeau", "Su"),
    "operation": ("Operation", "OP"),
    "asset": ("Asset", "AST"),
    "cost": ("Cost", "©"),
    "event": ("Event", "EVT"),
    "hardware": ("Hardware", "HW"),
    "ice": ("ICE", "ICE"),
    "identity": ("Identity", "ID"),
    "program": ("Program", "PGM"),
    "resource": ("Resource", "RES"),
    "upgrade": ("Upgrade", "UGD"),
    "agenda": ("Agenda", "AGD"),
}

symbols = {
    "ascii": {
        "[credit]": "[c]",
        "[mu]": "[MU]",
        "[recurring-credit]": "[r-c]",
        "[influence]": "o",
        "[trash]": "[trash]",
        "[link]": "[link]",
        "[click]": "[click]",
        "[subroutine]": "[sub]",
        "super_digits": "0123456789"

    },
    "unicode": {   # ꌡ Ѿ ⏣ ᆿ ۞ፀ ᕫ ᐌ  ᗣ  ᖵ   ᝅ  ♨   ⧮ ⨷
        "[credit]": "ᚖ", #¢ ⬨ ⟠ Ⓒ
        "[mu]": "⧮", #ᝅ ᲁ, Ⰾ ▟ ⵖ
        "[recurring-credit]": "↺¢",
        "[influence]": "●",
        "[trash]": "➠☖ ", #♺ ⌸♺#⎋⌧",#, ""ᮿ ⌸ ⌫ ☖ ⌧ ᐫ ᮕ",
        "[link]": "⧉", # ☍
        "[click]": "◴", #〄 ⥁⏣
        "[subroutine]": "↳",
        "super_digits": "⁰¹²³⁴⁵\u2076\u2077\u2078\u2079"
    },
    "fancy": {
        "[credit]": "©",
        "[mu]": "⛫",
        "[recurring-credit]": "↺",
        "[influence]": "●",
        "[trash]": "🗑",
        "[link]": "☍",
        "[click]": "⏣",
        "[subroutine]": "↳"
    }
}

# TODO: Control image browser properly


class Card:
    def __init__(self, entries):
        self.text = ""
        self.d = entries
        self.__dict__.update(**entries)

    def __str__(self):
        return (self.title)

    def __repr__(self):
        return self.title + " | " + self.code

    def __eq__(self, other):
        return self.code == other.code

    def __hash__(self):
        return hash((self.code, self.title))

    def get_image(self):
        local_filename = image_loc + "/" + self.code + ".png"
        if not os.path.exists(local_filename):
            url = imgurl + self.code + ".png"
            r = requests.get(url, stream=True)
            with open(local_filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
            print("Fetching: " + url)
        return local_filename

    def to_string_full(self):
        pass

    def to_string(self, limit=9999):
        rules = self.text.replace("\n", " ").replace(
            "<strong>", Style.NORMAL).replace("</strong>", Style.DIM)
        rules = self.replace_special(rules)
        return ("%s%s:%s %s%s" % (Style.BRIGHT, self.title, Style.NORMAL,
                                  Style.DIM, rules))[0:limit] + Style.RESET_ALL

    def get_formatted(self, field, replace_newlines=True):
        string = self.d.get(field, "")
        if string == "":
            return string
        if replace_newlines:
            string = string.replace("\n", " ")
        string = string.replace("<strong>", "").replace("</strong>", "")
        string = self.replace_special(string)
        # return ("%s%s:%s %s%s" % (Style.BRIGHT, self.title, Style.NORMAL,
        # Style.DIM, rules))[0:limit] + Style.RESET_ALL
        return string

    def show(self):
        print(self.get_image())

    def replace_special(self, string):
        symb = symbols['unicode']
        # CREDIT = "©"
        # RECURRING = "↺ "
        # CLICK = "⏣ "  # ⌀⌚ "🕐",
        # MU = "⛫ "
        # LINK = "☍"  # "⚯ " # ⚯☍
        # ⌬  ⛃   ⛗
        # ☍ (link?)
        # ⍧   ⏎  ⏣ ◔
        # super_digits = "⁰¹²³⁴⁵\u2076\u2077\u2078\u2079"
        # TRASH = "🗑"
        # replacements = {
        #     "[subroutine]": "↳",
        #     '[click]': CLICK,
        #     "[credit]": CREDIT,
        #     "[trash]": TRASH,
        #     "[mu]": MU,
        #     "[link]": LINK,
        #     "[recurring-credit]": RECURRING + CREDIT,
        # }
        # for frm, to in replacements.items():
        for frm, to in symb.items():
            string = string.replace(frm, to)
        matches = re.search(trace_re, string)
        while matches:
            if matches.group(1) == "X":
                string = string.replace(matches.group(0), "Trace X")
            else:
                num = int(matches.group(1))
                string = string.replace(
                    matches.group(0), "Trace" + symb['super_digits'][num])
            matches = re.search(trace_re, string)

        return string

    def printable(self, attribute, verbose=False):
        string = str(self.d.get(attribute, ""))
        out = attr_to_readable.get(string, None)
        if out is None:
            return string.title()
        return out[0 if verbose else 1]

    def __lt__(self, other):
        return self.title < other.title


def load_cards():
    for filename in glob.glob(dbpath + "/pack/*.json"):
        with open(filename, "r") as f:
            jobj = json.load(f)
            for card in jobj:
                cards_by_id[card['code']] = Card(card)
                cards_by_name[card['title']] = Card(card)


def card_by_name(name):
    return cards_by_name.get(name, None)


def card_by_id(card_id):
    return cards_by_id.get(card_id, None)




def search(search_term, fields=["text", "title"], cardset=None):
    if cardset is None:
        cardset = cards_by_id.values()
    if search_term is None or search_term == "":
        return list(cardset)
    results = set()
    search_term = search_term.lower()
    for card in cardset:
        try:
            for field in fields:
                if search_term in card.d.get(field, "").lower():
                    results.add(card)
                    continue
        except AttributeError:
            print("!! - ", card)
    return list(results)


class Deck(object):
    card_types = { "runner": [ "event", "resource", "program", "hardware" ],
            "corp": [ "operation", "ice", "agenda", "asset", "upgrade" ],
                   None: []}

    def __init__(self, name=None):
        self.cards_qty = {}
        self.cards = []
        self.cards_by_type = defaultdict(list)
        self.side = None # corp/runner
        self.name = name
        self.identity = None
        self.filename = None
        self.comments = ""

    def add_card(self, card, qty=None):
        if self.side is not None and card.side_code != self.side:
            return False
        if self.side is None:
            self.side = card.side_code
        if qty is None:
            qty = self.cards_qty.get(card, 0) + 1
        self.cards_qty[card] = qty
        if card.type_code == "identity":
            self.identity = card
            return True
        ss = self.cards_by_type[card.type_code]
        if card not in ss:
            ss.append(card)
            ss.sort()
            self.order_cards()
        return True

    def order_cards(self):
        ordered_cards = []
        for type_ in Deck.card_types[self.side]:
            ordered_cards.extend(self.cards_by_type[type_])
        self.cards = ordered_cards

    def remove_card(self, card, qty=None):
        if qty is None:
            qty = max(self.cards_qty.get(card, 0) - 1, 0)
        if qty == 0:
            self.cards_qty.pop(card, None)
            if card in self.cards_by_type[card.type_code]:
                self.cards_by_type[card.type_code].remove(card)
        else:
            self.cards_qty[card] = qty
        self.order_cards()

    def to_string(self, pretty=False):
        deckstr = ""
        if pretty:
            deckstr += self.name + "\n\n"
        if pretty:
            deckstr += "Identity: "
        else:
            deckstr += "1x "
        deckstr += str(self.identity) + "\n"
        for type_ in Deck.card_types[deck.side]:
            if pretty and len(self.cards_by_type[type_]) > 0:
                deckstr += "\n%s (%d):\n" % (attr_to_readable[type_][0],
                        len(self.cards_by_type[type_]))
            for card in self.cards_by_type[type_]:
                deckstr += "%dx %s" % (self.cards_qty[card], card.title) + "\n"
        # for c in sorted(self.cards.keys()):
            # deckstr += "%dx %s" % (self.cards[c], c.title) + "\n"

        # if self.side == "runner":
        #     types = [""]
        # else:
        #     types = [""]

        # deckstr = "Deck: %s\nIdentity: %s\n\n" %\
        #         (self.name, self.identity.title)
        # for type_ in types:
        #     deckstr += "%s:\n"
        #     for card in sorted(self.cards_by_type[type_]):
        #         deckstr += "%d %s" % (card[0], card[1])
        return deckstr

    def save_to_dropbox(self):
        pass

    def from_string(self):
        pass

    def from_file(filename, format=None, warn=False):
       with open(filename, "r") as f:
           lines = f.readlines()
       deck = Deck()
       warnings = []
       for i, line in enumerate(lines):
           line = line.strip()
           if len(line) == 0:
               continue
           m = cardline.match(line)
           if not m:
               deck.comments += line
               if i == 0:
                   deck.name = line
               continue
           qty = int(m.group(1).lower().replace("x", "")) if m.group(1) else 1
           cardname = m.group(2).strip()
           setname = m.group(3) # Ignore

           card = cards_by_name.get(cardname, None)
           if card is not None:
               deck.side = card.side_code
               if card.type_code == "identity":
                   if deck.identity is not None:
                       warnings.append("Multiple identities found.")
                   deck.identity = card
               else:
                   deck.add_card(card, qty)
           else:
               deck.comments += line + "\n"

       if not deck.name:
           if deck.identity:
               deck.name = deck.identity.title
           else:
               deck.name = "new deck"

       deck.order_cards()
       deck.filename = filename
       if warn:
           print( "\n".join(warnings))

       return deck

    def save(self, filename=None):
        if not filename:
            filename = self.filename
        if filename is not None:
            with open(filename, "w") as f:
                f.write(self.to_string())
            return True
        return False

    def print(self):
        print(self.to_string())

if __name__ == "__main__":
    load_cards()
    import sys
    new_card = cards_by_name["Stimhack"]
    print(new_card)
    old_card = cards_by_name["Diesel"]
    deck = Deck.from_file(sys.argv[1], warn=True)
    deck.print()
    print("----")
    deck.add_card(new_card)
    deck.print()
    print("----")
    deck.remove_card(new_card)
    deck.remove_card(old_card)
    deck.remove_card(old_card)
    deck.remove_card(old_card)
    print(deck.to_string(pretty=True))

