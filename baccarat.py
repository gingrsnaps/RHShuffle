"""Eight-deck Punto Banco, replayed only from the committed random stream.

Each round starts a fresh 416-card shoe; there are no burns or side bets.
The draw tableau follows standard commission Baccarat. All returns include
the stake and round down to whole RedPoints, including the 1.95x Banker win.
"""

RETURNS = {'player': 20000, 'banker': 19500, 'tie': 90000}


def card_value(card):
    rank = card % 13 + 1
    return rank if rank < 10 else 0


def total(cards):
    return sum(map(card_value, cards)) % 10


def banker_draws(points, player_third):
    """Called only after both initial naturals have been ruled out."""
    if player_third is None:
        return points <= 5
    if points <= 2:
        return True
    if points == 3:
        return player_third != 8
    if points == 4:
        return 2 <= player_third <= 7
    if points == 5:
        return 4 <= player_third <= 7
    return points == 6 and player_third in (6, 7)


def replay(draw, wager, side):
    if side not in RETURNS:
        raise ValueError('Choose Player, Banker or Tie.')
    shoe = list(range(416))
    cursor = 0

    def card():
        nonlocal cursor
        # Partial Fisher–Yates: sample distinct physical cards without replacement.
        other = cursor + draw.below(len(shoe) - cursor)
        shoe[cursor], shoe[other] = shoe[other], shoe[cursor]
        value = shoe[cursor]
        cursor += 1
        return value

    player, banker = [card()], [card()]
    player.append(card())
    banker.append(card())
    pt, bt = total(player), total(banker)
    natural = pt >= 8 or bt >= 8
    if not natural:
        third = None
        if pt <= 5:
            player.append(card())
            third = card_value(player[-1])
        if banker_draws(bt, third):
            banker.append(card())
    pt, bt = total(player), total(banker)
    winner = 'tie' if pt == bt else 'player' if pt > bt else 'banker'
    won = side == winner
    push = winner == 'tie' and side != 'tie'
    payout = wager * RETURNS[side] // 10000 if won else wager if push else 0
    return dict(player=player, banker=banker, player_total=pt, banker_total=bt,
                natural=natural, winner=winner, won=won, push=push, payout=payout)
