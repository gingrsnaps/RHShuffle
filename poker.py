"""Single-player five-card draw: 9/6 Jacks or Better, one standard deck.

The committed HMAC stream deals without replacement. Holds are a later player
decision: they never reseed or reshuffle the already committed deck. No jokers.
All listed multipliers are total returns, including the original stake.
"""
from collections import Counter

PAYTABLE = {
    'royal_flush': 800, 'straight_flush': 50, 'four_of_a_kind': 25,
    'full_house': 9, 'flush': 6, 'straight': 4, 'three_of_a_kind': 3,
    'two_pair': 2, 'jacks_or_better': 1, 'no_win': 0,
}
LABELS = {
    'royal_flush': 'Royal flush', 'straight_flush': 'Straight flush',
    'four_of_a_kind': 'Four of a kind', 'full_house': 'Full house',
    'flush': 'Flush', 'straight': 'Straight', 'three_of_a_kind': 'Three of a kind',
    'two_pair': 'Two pair', 'jacks_or_better': 'Jacks or better', 'no_win': 'No paying hand',
}


def validate_holds(holds):
    if (not isinstance(holds, list) or len(holds) > 5 or
            any(type(index) is not int or not 0 <= index < 5 for index in holds) or
            len(set(holds)) != len(holds)):
        raise ValueError('Choose which of the five cards to hold.')
    return sorted(holds)


def classify(cards):
    if (not isinstance(cards, list) or len(cards) != 5 or len(set(cards)) != 5 or
            any(type(card) is not int or not 0 <= card < 52 for card in cards)):
        raise ValueError('Poker requires five different standard-deck cards.')
    # Card IDs match Blackjack's display: A,2,...,K within each suit.
    ranks = sorted(14 if card % 13 == 0 else card % 13 + 1 for card in cards)
    counts = Counter(ranks)
    groups = sorted(counts.values(), reverse=True)
    flush = len({card // 13 for card in cards}) == 1
    straight = len(counts) == 5 and (ranks[-1]-ranks[0] == 4 or ranks == [2, 3, 4, 5, 14])
    if flush and ranks == [10, 11, 12, 13, 14]: return 'royal_flush'
    if straight and flush: return 'straight_flush'
    if groups == [4, 1]: return 'four_of_a_kind'
    if groups == [3, 2]: return 'full_house'
    if flush: return 'flush'
    if straight: return 'straight'
    if groups == [3, 1, 1]: return 'three_of_a_kind'
    if groups == [2, 2, 1]: return 'two_pair'
    if groups == [2, 1, 1, 1] and any(rank >= 11 and count == 2 for rank, count in counts.items()):
        return 'jacks_or_better'
    return 'no_win'


def replay(draw, wager, holds=None):
    deck, cursor = list(range(52)), 0

    def card():
        nonlocal cursor
        other = cursor + draw.below(52-cursor)
        deck[cursor], deck[other] = deck[other], deck[cursor]
        value = deck[cursor]
        cursor += 1
        return value

    initial = [card() for _ in range(5)]
    if holds is None:
        return dict(ended=False, initial=initial, cards=initial[:], holds=None,
                    category='playing', multiplier=0, payout=0)
    holds = validate_holds(holds)
    final = [initial[i] if i in holds else card() for i in range(5)]
    category = classify(final)
    multiplier = PAYTABLE[category]
    return dict(ended=True, initial=initial, cards=final, holds=holds,
                category=category, multiplier=multiplier, payout=wager*multiplier)
