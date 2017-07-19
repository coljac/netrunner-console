import os
import unittest
import pytest
import console.cards as cards


@pytest.fixture(scope="module")
def anr_cards():
    cards.load_cards()
    return cards.cards_by_name.values()


class TestCards():
    def testCardsLoaded(self, anr_cards):
        assert len(anr_cards) == 1204
        assert cards.cards_by_name['Data Raven'].title == "Data Raven"
        assert cards.cards_by_name[
            "Aesop's Pawnshop"].title == "Aesop's Pawnshop"
        assert cards.cards_by_id['01113'].title == "Wall of Static"

    def testPacksLoaded(self, anr_cards):
        assert cards.packs_by_code['bb'] == "Breaker Bay"
        assert cards.packs_by_name["Core Set"] == "core"


class TestDecks():
    pass


def advsearch(search_term, expected):
    assert len(cards.advanced_search(search_term)) == expected

def search(search_term, expected):
    assert len(cards.search(search_term)) == expected


class TestSearch():
    def testBasicSearch(self, anr_cards):
        res = cards.search("")
        assert len(res) == 1204

        search("Aesop's", 1)
        search("credits", 87)
        search("Make a run", 63)

        res = cards.search("contract", fields=['title'])
        assert len(res) == 8
        assert "Subcontract" in [c.title for c in res]

        res = cards.search("ContRact", fields=['title'])
        assert len(res) == 8

        res = cards.search("runner", fields=['side_code'])
        assert len(res) == 549

        res = cards.search("identity", fields=['type_code'])
        assert len(res) == 83

        res = cards.search("never", fields=['flavor', 'text'])
        assert len(res) == 173


    def testAdvancedSearch(self, anr_cards):
        res = cards.advanced_search("e:core f:anarch")
        assert len(res) == 16

        advsearch("", 1204)
        advsearch("f:jint t:asset", 26)
        advsearch("t:agenda ac<3", 7)
        advsearch("t:ice o=4", 32)
        advsearch("t:ice cost>=2 o<=4 o!=3 f:wey", 17)
        advsearch("cost=2 or o=4 t:ice f:wey", 17)
        advsearch("food t:agen", 1)
        advsearch("f:- t:ice", 26)
        advsearch("f:j t:asset", 26)
        advsearch("f:- d:r", 77) 



def main():
    unittest.main()


if __name__ == '__main__':
    main()
