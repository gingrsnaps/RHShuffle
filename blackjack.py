"""Pure six-deck Blackjack replay. No storage, HTTP, clock or random source.

The fairness module supplies unbiased draws from the precommitted seed.
Cards are unique IDs 0..311: deck*52 + suit*13 + rank-1 (A=1, K=13).
A fresh six-deck shoe is sampled without replacement for every round.
"""


def total(cards):
    ranks = [card % 13 + 1 for card in cards]
    points = sum(min(rank, 10) for rank in ranks)
    soft = 1 in ranks and points + 10 <= 21
    return points + (10 if soft else 0), soft


def replay(draw, wager, actions):
    """Replay legal player decisions; keep the dealer hole card private upstream."""
    if not isinstance(actions, list) or len(actions) > 32:
        raise ValueError('Invalid Blackjack action history.')
    shoe = list(range(312))
    cursor = 0
    def card():
        nonlocal cursor
        other = cursor + draw.below(len(shoe) - cursor)
        shoe[cursor], shoe[other] = shoe[other], shoe[cursor]
        value = shoe[cursor]
        cursor += 1
        return value
    player, dealer = [card()], [card()]
    player.append(card()); dealer.append(card())
    pt, _ = total(player); dt, _ = total(dealer)
    ended = pt == 21 or dt == 21  # Dealer peeks before any player decision.
    natural = pt == 21 and dt != 21
    stake = wager
    for index, action in enumerate(actions):
        if ended or action not in ('hit', 'stand', 'double'):
            raise ValueError('That Blackjack action is not legal.')
        if action == 'double':
            if index or len(player) != 2:
                raise ValueError('Double is available only on your first two cards.')
            stake = wager * 2
        if action in ('hit', 'double'):
            player.append(card())
        pt, _ = total(player)
        ended = action in ('stand', 'double') or pt >= 21
    if ended and not (len(player) == 2 and (pt == 21 or dt == 21)) and pt <= 21:
        while total(dealer)[0] < 17:  # Stand on hard and soft 17.
            dealer.append(card())
    pt, ps = total(player); dt, ds = total(dealer)
    status, payout = 'playing', 0
    if ended:
        if len(dealer) == 2 and dt == 21:
            status = 'push' if len(player) == 2 and pt == 21 else 'lose'
        elif natural:
            status = 'blackjack'
        elif pt > 21:
            status = 'lose'
        elif dt > 21 or pt > dt:
            status = 'win'
        elif pt == dt:
            status = 'push'
        else:
            status = 'lose'
        payout = wager * 5 // 2 if status == 'blackjack' else stake * 2 if status == 'win' else stake if status == 'push' else 0
    return dict(ended=ended, player=player, dealer=dealer, player_total=pt, dealer_total=dt,
                player_soft=ps, dealer_soft=ds, status=status, total_wager=stake, payout=payout)
