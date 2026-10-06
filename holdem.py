"""Heads-up no-limit Hold'em, RedPoints only, with a reproducible computer seat.

A hand reserves equal table stacks. Only chips actually committed count as wagers.
The deck is fixed before decisions; the opponent receives a deliberately restricted
observation, never the player's cards, unrevealed board, seed, or deck. Keep this
versioned policy stable so archived receipts can always be replayed.
"""
from collections import Counter
from itertools import combinations

VARIANT = 'texas_holdem'
POLICY = 'redbot-v1'
MIN_BUY_IN = 20
MAX_BUY_IN = (2**53-1)//2
LABELS = ('High card', 'One pair', 'Two pair', 'Three of a kind', 'Straight',
          'Flush', 'Full house', 'Four of a kind', 'Straight flush')
STREETS = ('preflop', 'flop', 'turn', 'river')
SEATS = ('player', 'computer')


def rank_five(cards):
    """Lexicographic rank including every relevant kicker; suits never break ties."""
    ranks = sorted((14 if c % 13 == 0 else c % 13+1 for c in cards), reverse=True)
    groups = sorted(((count, rank) for rank, count in Counter(ranks).items()), reverse=True)
    unique = sorted(set(ranks))
    straight = (5 if unique == [2, 3, 4, 5, 14] else
                unique[-1] if len(unique) == 5 and unique[-1]-unique[0] == 4 else 0)
    flush = len({c//13 for c in cards}) == 1
    if straight and flush: return (8, straight)
    if groups[0][0] == 4: return (7, groups[0][1], groups[1][1])
    if [x[0] for x in groups] == [3, 2]: return (6, groups[0][1], groups[1][1])
    if flush: return (5, *ranks)
    if straight: return (4, straight)
    if groups[0][0] == 3: return (3, groups[0][1], *sorted((r for n, r in groups if n == 1), reverse=True))
    pairs = sorted((r for n, r in groups if n == 2), reverse=True)
    if len(pairs) == 2: return (2, *pairs, groups[-1][1])
    if pairs: return (1, pairs[0], *sorted((r for n, r in groups if n == 1), reverse=True))
    return (0, *ranks)


def best_hand(cards):
    if (not isinstance(cards, list) or not 5 <= len(cards) <= 7 or len(set(cards)) != len(cards)
            or any(type(c) is not int or not 0 <= c < 52 for c in cards)):
        raise ValueError('Evaluate five to seven different cards.')
    # Equal-ranked combinations choose the lexicographically smallest card IDs.
    # This makes the five highlighted cards identical in both implementations.
    candidates = sorted(combinations(sorted(cards), 5))
    best = max(candidates, key=rank_five)
    rank = rank_five(best)
    return dict(rank=list(rank), cards=list(best), label=LABELS[rank[0]])


def validate_action(value):
    if not isinstance(value, dict) or set(value) != {'action', 'amount'}:
        raise ValueError('Send an action and a whole-point amount.')
    action, amount = value['action'], value['amount']
    if (action not in ('fold', 'check', 'call', 'bet', 'raise', 'all_in') or
            type(amount) is not int or not 0 <= amount <= MAX_BUY_IN or
            (action not in ('bet', 'raise') and amount != 0)):
        raise ValueError('Choose a legal Hold’em action.')
    return dict(action=action, amount=amount)


def bot_action(observation):
    """Published redbot-v1: a small, deterministic heuristic, not an odds claim.

    Accept only this observation. Do not pass the engine, deck, player hole cards
    or server seed here. Tests change hidden cards and assert identical decisions.
    """
    cards, board, legal = observation['hole'], observation['board'], observation['legal']
    ranks = sorted((14 if c % 13 == 0 else c % 13+1 for c in cards), reverse=True)
    if not board:
        strength = (65+ranks[0]*2 if ranks[0] == ranks[1] else
                    ranks[0]*3+ranks[1] + (8 if cards[0]//13 == cards[1]//13 else 0)
                    + (5 if ranks[0]-ranks[1] == 1 else 0))
    else:
        rank = best_hand(cards+board)['rank']
        strength = (rank[1]*2 if rank[0] == 0 else 40+rank[1]*2 if rank[0] == 1
                    else 75 if rank[0] == 2 else 90 if rank[0] == 3 else 110)
    # Occasional reproducible bluffs use only this seat's cards and public state.
    bluff = (sum(cards)+sum(board)+observation['pot']+observation['street_index']) % 13 == 0
    if legal['can_raise'] and observation['raises'] == 0 and (strength >= 80 or (bluff and not legal['call'])):
        target = max(legal['min_raise_to'], observation['highest']+max(observation['big_blind'], observation['pot']//2))
        target = min(target, legal['max_raise_to'])
        if target >= legal['min_raise_to']:
            return dict(action='bet' if observation['highest'] == 0 else 'raise', amount=target)
    if legal['check']:
        return dict(action='check', amount=0)
    # Integer-only price/strength thresholds. No fabricated equity percentages.
    cheap = legal['call']*4 <= observation['pot']
    medium = legal['call']*2 <= observation['pot']
    call = strength >= 90 or (strength >= 65 and medium) or (strength >= 40 and cheap)
    return dict(action='call' if call else 'fold', amount=0)


class Hand:
    def __init__(self, deck, buy_in, button):
        if type(buy_in) is not int or not MIN_BUY_IN <= buy_in <= MAX_BUY_IN:
            raise ValueError('Hold’em table stacks must be at least 20 whole RedPoints.')
        if button not in SEATS or len(deck) != 52 or set(deck) != set(range(52)):
            raise ValueError('Invalid Hold’em deal.')
        self.buy_in, self.deck, self.button = buy_in, deck, SEATS.index(button)
        self.big = max(2, buy_in//50)
        self.small = max(1, self.big//2)
        first = 1-self.button  # Heads-up big blind receives the first card.
        self.holes = [[], []]
        for i in range(4): self.holes[(first+i)%2].append(deck[i])
        # Burn before flop, turn and river. Every card is fixed before any move.
        self.boards = [[], deck[5:8], deck[5:8]+[deck[9]], deck[5:8]+[deck[9], deck[11]]]
        self.stacks, self.committed, self.bets = [buy_in, buy_in], [0, 0], [0, 0]
        self.acted, self.raises = [False, False], [0, 0]
        self.street, self.actor, self.last_raise = 0, self.button, self.big
        self.ended, self.winner, self.reason = False, None, None
        self.refunds, self.awards, self.hands = [0, 0], [0, 0], [None, None]
        self.pot_at_end = 0
        self.events = []
        self.pay(self.button, self.small)
        self.pay(1-self.button, self.big)
        self.event('deal', seat=None, action='blinds', amount=self.small+self.big)

    def pay(self, seat, amount):
        self.stacks[seat] -= amount
        self.committed[seat] += amount
        self.bets[seat] += amount

    def legal(self, seat):
        if self.ended: return {}
        high = max(self.bets)
        call = min(self.stacks[seat], high-self.bets[seat])
        maximum = self.bets[seat]+self.stacks[seat]
        can_raise = maximum > high and self.stacks[1-seat] > 0
        return dict(fold=True, check=call == 0, call=call,
                    can_raise=can_raise, min_raise_to=high+self.last_raise,
                    max_raise_to=maximum, all_in=self.stacks[seat] > 0 and (can_raise or self.stacks[seat] <= call))

    def snapshot(self):
        reveal = self.ended and self.reason == 'showdown'
        return dict(player=self.holes[0][:], computer=self.holes[1][:] if reveal else [None, None],
                    board=self.boards[self.street][:], stacks=self.stacks[:], bets=self.bets[:],
                    pot=self.pot_at_end if self.ended else sum(self.committed),
                    street=STREETS[self.street], turn=None if self.ended else SEATS[self.actor],
                    ended=self.ended, winner=self.winner, reason=self.reason)

    def event(self, kind, **extra):
        self.events.append(dict(kind=kind, **extra, state=self.snapshot()))

    def observation(self):
        seat = self.actor
        return dict(hole=self.holes[seat][:], board=self.boards[self.street][:],
                    legal=self.legal(seat), pot=sum(self.committed), highest=max(self.bets),
                    big_blind=self.big, street_index=self.street, raises=self.raises[seat])

    def finish(self, winner=None):
        # Return any uncalled portion before awarding the contested pot.
        matched = min(self.committed)
        self.refunds = [amount-matched for amount in self.committed]
        for i in range(2):
            self.stacks[i] += self.refunds[i]
            self.committed[i] -= self.refunds[i]
        self.pot_at_end = sum(self.committed)
        self.reason = 'fold' if winner is not None else 'showdown'
        if winner is None:
            self.hands = [best_hand(hole+self.boards[3]) for hole in self.holes]
            ranks = [tuple(hand['rank']) for hand in self.hands]
            winner = 0 if ranks[0] > ranks[1] else 1 if ranks[1] > ranks[0] else -1
        self.winner = 'split' if winner == -1 else SEATS[winner]
        if winner == -1:
            self.awards = [self.pot_at_end//2]*2
            # With equal whole-point contributions the heads-up pot is even.
            # Retain the standard odd-chip rule for completeness.
            self.awards[1-self.button] += self.pot_at_end % 2
        else:
            self.awards[winner] = self.pot_at_end
        for i in range(2): self.stacks[i] += self.awards[i]
        self.ended = True
        self.event('settle', seat=self.winner, action=self.reason, amount=self.pot_at_end)
        if sum(self.stacks) != self.buy_in*2 or min(self.stacks) < 0:
            raise ValueError('Hold’em chips did not balance.')

    def advance(self):
        if self.street == 3:
            self.finish()
            return
        self.street += 1
        self.bets, self.acted, self.raises = [0, 0], [False, False], [0, 0]
        self.last_raise, self.actor = self.big, 1-self.button
        self.event('street', seat=None, action=STREETS[self.street], amount=0)
        if 0 in self.stacks:
            self.advance()

    def move(self, value):
        value = validate_action(value)
        if self.ended: raise ValueError('This Hold’em hand is already complete.')
        seat, other = self.actor, 1-self.actor
        legal, action, amount = self.legal(seat), value['action'], value['amount']
        if action == 'fold':
            self.event('action', seat=SEATS[seat], action=action, amount=0)
            self.finish(other)
            return
        if action == 'check':
            if not legal['check']: raise ValueError('Call, raise or fold when facing a bet.')
            paid = 0
        elif action == 'call':
            if not legal['call']: raise ValueError('There is no bet to call. Check instead.')
            paid = legal['call']
        else:
            high = max(self.bets)
            if action == 'all_in':
                if not legal['all_in']: raise ValueError('All-in is not available.')
                amount = legal['max_raise_to']
            elif (action == 'bet') != (high == 0):
                raise ValueError('Use Bet to open a street, or Raise to increase an existing bet.')
            if amount <= high:
                if action != 'all_in' or self.stacks[seat] > legal['call']:
                    raise ValueError('A raise must increase the current bet.')
            else:
                if (not legal['can_raise'] or amount > legal['max_raise_to'] or
                        (amount < legal['min_raise_to'] and amount != legal['max_raise_to'])):
                    raise ValueError('Raise by at least the last full raise, or go all-in.')
                increase = amount-high
                if increase >= self.last_raise: self.last_raise = increase
                self.raises[seat] += 1
                self.acted[other] = False
            paid = amount-self.bets[seat]
        if paid < 0 or paid > self.stacks[seat]: raise ValueError('Not enough chips at the table.')
        self.pay(seat, paid)
        self.acted[seat] = True
        self.actor = other
        self.event('action', seat=SEATS[seat], action=action, amount=paid)
        if self.bets[0] == self.bets[1] and (all(self.acted) or 0 in self.stacks):
            self.advance()
        elif self.stacks[other] == 0 and self.bets[seat] >= self.bets[other]:
            # A short all-in call cannot be raised. Return uncalled excess and run out.
            while self.street < 3:
                self.street += 1
                self.event('street', seat=None, action=STREETS[self.street], amount=0)
            self.finish()

    def auto(self):
        while not self.ended and self.actor == 1:
            self.move(bot_action(self.observation()))

    def result(self, actions):
        value = self.snapshot()
        value.update(variant=VARIANT, policy=POLICY, initial=self.holes[0][:], button=SEATS[self.button],
                     small_blind=self.small, big_blind=self.big, buy_in=self.buy_in,
                     legal={} if self.ended else self.legal(0), actions=actions,
                     events=self.events, total_wager=self.committed[0], returned=self.awards[0],
                     refunds=self.refunds[:], best=self.hands[:],
                     payout=self.stacks[0] if self.ended else 0)
        if self.ended: value['computer'] = self.holes[1][:]
        return value


def replay(draw, buy_in, options, actions=None, ending=None):
    if options.get('variant') != VARIANT or set(options) != {'variant', 'button'}:
        raise ValueError('Invalid Hold’em options.')
    if not isinstance(actions, list) or len(actions) > 4096:
        raise ValueError('Invalid Hold’em action history.')
    # A full Fisher–Yates deck is committed once; later choices cannot reshuffle it.
    deck = list(range(52))
    for i in range(51):
        j = i+draw.below(52-i)
        deck[i], deck[j] = deck[j], deck[i]
    hand = Hand(deck, buy_in, options['button'])
    hand.auto()
    moves = []
    for action in actions:
        move = validate_action(action)
        if hand.ended or hand.actor != 0: raise ValueError('Action after the hand ended.')
        hand.move(move)
        moves.append(move)
        hand.auto()
    if ending is not None:
        if ending != 'weekly_reset' or hand.ended:
            raise ValueError('Invalid automatic Hold’em settlement.')
        # An expired week never places another wager on the player's behalf.
        hand.move(dict(action='fold', amount=0))
    return hand.result(moves)
