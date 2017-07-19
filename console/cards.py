#!env python3

from collections import defaultdict
import glob
import json
import os
import re
import requests
import shlex
import shutil
import time
import zipfile
imgurl = "https://netrunnerdb.com/card_image/"
image_loc = "./images"

cards_by_id = {}
cards_by_name = {}
values_by_key = defaultdict(set)
packs_by_code = {}
packs_by_name = {}

trace_re = re.compile(r"<trace>[Tt]race (.)</trace>")
cardline = re.compile(
    r'^\s*(\d[xX]?)?\s*([\w\d :!&*,₂/;"\'\-.]*)\s*(\(.*\))?\W*$')


def attr_to_readable(attr):
    return _attr_to_readable.get(attr, (attr.replace("_", " ").title(), attr))


_attr_to_readable = {
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
    "runner": ("Runner", "R"),
    "corp": ("Corp", "C"),
    "advancement_cost": ("Advancement cost", "Adv"),
    "keywords": ("Keywords", "Keywords"),
}

search_abbrevs = {
    "set": "pack_code",
    "kw": "keywords",
    "s": "side_code",
    "side": "side_code",
    "f": "flavor",
    "type": "type_code",
    "name": "title",
    "t": "type_code",
    "ac": "advancement_cost",
    "ap": "agenda_points",
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
    },
    "nerdfonts": {
        "[credit]": "\ue7a7", # "\ue51e",
        "[mu]": "\uf2db", #e066
        "[recurring-credit]": "\uf46a\ue7a7",
        "[influence]": "●",
        "[trash]": "\uf014",
        "[link]":  "\uf0c1", # "\uf127",
        "[click]": "\uf464", # \uf49b  f43a
        "[subroutine]": "↳",
        "super_digits": "⁰¹²³⁴⁵\u2076\u2077\u2078\u2079"
    }
}

symb = symbols['unicode']

# TODO: Control image browser properly


def download_cards(to_dir, progress):
    url = "https://github.com/zaroth/netrunner-cards-json/archive/master.zip"
    local_filename = "./netrunner-cards-json-master.zip"
    r = requests.get(url, stream=True)
    i = 0
    with open(local_filename, 'wb') as f:
        file_size = None
        tries = 0
        while not file_size:
            tries += 1
            if tries >= 10:
                break
            file_size = r.headers.get('Content-Length', None)
            if file_size:
                file_size = int(file_size)
            else:
                time.sleep(0.1)
        # shutil.copyfileobj(r.raw, f)
        for chunk in r.iter_content():
            f.write(chunk)
            i += 1
            if progress is not None and file_size is not None and i % 100 == 0:
                progress['progress'] = i / file_size

    zip_ref = zipfile.ZipFile(local_filename, 'r')
    # for name in zip_ref.namelist():
    #     zip_ref.extract(name, to_dir)
    zip_ref.extractall(to_dir)  # Overwrite?
    zip_ref.close()
    if os.path.exists(to_dir + "/netrunner-cards-json"):
        shutil.rmtree(to_dir + "/netrunner-cards-json")
    os.rename(to_dir + "/netrunner-cards-json-master",
              to_dir + "/netrunner-cards-json")
    os.remove(local_filename)
    load_cards(to_dir + "/netrunner-cards-json")
    progress['progress'] = 1
    return True


class Card(object):
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
        out = _attr_to_readable.get(string, None)
        if out is None:
            return string.title()
        return out[0 if verbose else 1]

    def __lt__(self, other):
        return self.title < other.title


class CardFilter(object):
    # TODO - generate from cards
    filter_by = ['faction_code', 'side_code', 'type_code', 'pack_code']
    key_to_filter = {}

    def __init__(self):

        self.filter_strings = defaultdict(list)

        self.filters = {
            'side': [],
            'faction_code': [],
            'type': [],
            'subtype': []
        }

        i = 0
        keycodes = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        for k in ['faction_code', 'type_code', 'side_code']:
            for v in values_by_key[k]:
                CardFilter.key_to_filter[keycodes[i]] = (k, v)
                i += 1

    def reset(self):
        for key in self.filters.keys():
            self.filters[key] = []
        self.filter_strings = defaultdict(list)

    def toggle_filter(self, filter_type, value):
        if value not in self.filter_strings[filter_type]:
            self.add_filter(filter_type, value)
        else:
            self.remove_filter(filter_type, value)

    def add_filter(self, filter_type, value):
        if value not in self.filter_strings[filter_type]:
            self.filter_strings[filter_type].append(value)
        self.update_filters(filter_type=filter_type)

    def remove_filter(self, filter_type, value):
        if value in self.filter_strings[filter_type]:
            self.filter_strings[filter_type].remove(value)
        self.update_filters(filter_type=filter_type)

    def update_filters(self, filter_type=None):
        if filter_type is not None:
            self.update_filter(filter_type)
        else:
            for t in self.filter_strings.keys():
                self.update_filter(t)

    def update_filter(self, filter_type):
        f = lambda x: search([s for s in self.filter_strings[filter_type]],
                                   cardset=x,
                                   fields=[filter_type], op="or", invert=False)
        self.filters[filter_type] = [f]

    def filter(self, cardlist):
        for type_ in self.filters.keys():
            for f in self.filters[type_]:
                cardlist = f(cardlist)
        return cardlist

    def get_filters(self, type_):
        return self.filters[type_]


def load_cards(card_dir=None):
    if len(cards_by_name) != 0:
        return
    if card_dir is None:
        card_dir = os.path.expanduser(
            '~') + "/.config/netrunner-console/netrunner-cards-json"
    for filename in glob.glob(card_dir + "/pack/*.json"):
        with open(filename, "r", encoding="utf-8") as f:
            jobj = json.load(f)
            for card in jobj:
                card_obj = Card(card)
                cards_by_id[card['code']] = card_obj
                cards_by_name[card['title']] = card_obj
                for key, value in card_obj.d.items():
                    if key not in [
                            'title', 'text', 'code', 'flavor', 'illustrator',
                            'position'
                    ]:
                        values_by_key[key].update(
                            [s.strip() for s in str(value).split(" - ")])
                        # values_by_key[key].add(value)
    with open(card_dir + '/packs.json', encoding="utf-8") as f:
        jobj = json.load(f)
        for pack in jobj:
            packs_by_code[pack['code']] = pack['name']
            packs_by_name[pack['name']] = pack['code']

    for k, v in values_by_key.items():
        values_by_key[k] = sorted(list(v))


def card_by_name(name):
    return cards_by_name.get(name, None)


def card_by_id(card_id):
    return cards_by_id.get(card_id, None)


def advanced_search(searchterm,
                    fields=['text', 'title'],
                    cardset=None,
                    invert=False,
                    op="and"):
    # search_re = re.compile(r"(\w*):(.*)")
    # TODO: replace cardset for AND operations?
    if not searchterm:
        return search("")
    search_re = re.compile(r"(\w*)([:><=]+)(.*)")
    sets = []
    if type(searchterm) == str:
        words = shlex.split(searchterm)
    else:
        words = searchterm
    for word in words:
        if word.lower() in ["and", "or"]:
            sets.append(word)
            continue

        m = search_re.match(word)
        if m:
            field = m.group(1)
            o = m.group(2)
            term = m.group(3)
            if field in search_abbrevs:
                field = search_abbrevs[field]
            if o == ":":
                result = search(
                    term,
                    fields=[field],
                    cardset=cardset,
                    invert=invert,
                    op=op)
            else:
                result = search_numeric(o, term, field, cardset=cardset, invert=invert)
            sets.append(set(result))
        else:
            sets.append(
                set(
                    search(
                        word,
                        fields=fields,
                        cardset=cardset,
                        invert=invert,
                        op=op)))
        sets.append(op)

    resultset = set()
    resultset.update(sets[0])
    nextop = None
    for r in sets[1:]:
        if r in ["and", "or"]:
            nextop = r
        else:
            if nextop == "and":
                resultset = resultset & r
            else:
                resultset = resultset | r
    return list(resultset)


def search_numeric(operator, val, field, cardset=None, invert=False):
    if cardset is None:
        cardset = cards_by_id.values()
    try:
        val = int(val)
    except ValueError:
        return cardset
    
    results = set()
    for card in cardset:
        field_val = card.d.get(field, None)
        if field_val is None:
            continue
        try:
            field_val = int(field_val)
        except ValueError:
            continue
        if operator == "=":
            matches = (field_val == val)
        elif operator == ">":
            matches = (field_val > val)
        elif operator == "<":
            matches = (field_val < val)
        elif operator == "<=":
            matches = (field_val <= val)
        elif operator == ">=":
            matches = (field_val >= val)
        if matches:
            results.add(card)
    return list(results)


def search(search,
           fields=["text", "title"],
           cardset=None,
           invert=False,
           op="or"):
    if cardset is None:
        cardset = cards_by_id.values()

    if search is None or len(search) == 0:
        return list(cardset)

    search_terms = [search.lower()] if type(search) == str else \
            [s.lower() for s in search]

    results = set()
    for card in cardset:
        field_texts = [str(card.d.get(field, "")).lower() for field in fields]
        is_in = [
            (any([search_term in field_text for field_text in field_texts]))
            for search_term in search_terms
        ]
        to_add = any(is_in) if op == "or" else all(is_in)
        if (to_add and not invert) or (not to_add and invert):
            results.add(card)
    return list(results)


class Deck(object):
    card_types = {
        "runner": ["event", "resource", "program", "hardware"],
        "corp": ["operation", "ice", "agenda", "asset", "upgrade"],
        None: []
    }

    def __init__(self, name=None):
        self.cards_qty = {}
        self.cards = []
        self.cards_by_type = defaultdict(list)
        self.side = None  # corp/runner
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
        for type_ in Deck.card_types[self.side]:
            cards_in_type = sum(
                [self.cards_qty[c] for c in self.cards_by_type[type_]])
            if pretty and len(self.cards_by_type[type_]) > 0:
                deckstr += "\n%s (%d):\n" % (_attr_to_readable[type_][0],
                                             cards_in_type)
            for card in self.cards_by_type[type_]:
                deckstr += "%dx %s" % (self.cards_qty[card], card.title) + "\n"
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
            if "Identity: " in line:
                line = line[9:]
            m = cardline.match(line)
            if not m:
                deck.comments += line
                if i == 0:
                    deck.name = line
                continue
            qty = int(m.group(1).lower().replace("x", "")) if m.group(1) else 1
            cardname = m.group(2).strip()
            setname = m.group(3)  # Ignore

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
                if i == 0 and deck.name is None:
                    deck.name = line
                else:
                    deck.comments += line + "\n"

        if not deck.name:
            if deck.identity:
                deck.name = deck.identity.title
            else:
                deck.name = "New Deck"

        deck.order_cards()
        deck.filename = filename
        if warn:
            print("\n".join(warnings))

        return deck

    def save(self, filename=None):
        if not filename:
            filename = self.filename
        if filename is not None:
            with open(filename, "w") as f:
                f.write(self.to_string(pretty=True))
            return True
        return False

    def print(self):
        print(self.to_string())


def deck_sets(deck):
    return set([c.pack_code for c in deck.cards])


if __name__ == "__main__":
    import sys
    load_cards()
    # deck = Deck.from_file(sys.argv[1])
    # print(deck.to_string(pretty=True))
    # for set_ in deck_sets(deck):
    # print(packs_by_code[set_])
    print("\n".join([str(c) for c in advanced_search(" ".join(sys.argv[1:]))]))
