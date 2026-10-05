"""Versioned RedPoints: deterministic games and exact, published payout calculations.

No HTTP, player records or mutable state live here. A one-time server seed is
committed before each bet and revealed with its receipt. The browser verifier
implements this same specification independently with Web Crypto and BigInt.
"""
from fractions import Fraction
from functools import lru_cache
import hashlib
import hmac
import json
from math import comb
import re

VERSION = 'redpoints-v4'
V2_VERSION = 'redpoints-v2'
V3_VERSION = 'redpoints-v3'
LEGACY_VERSION = 'redpoints-v1'
SUPPORTED_VERSIONS = (LEGACY_VERSION, V2_VERSION, V3_VERSION, VERSION)
BLACKJACK_VERSIONS = (V2_VERSION, V3_VERSION, VERSION)
POKER_VERSIONS = (V3_VERSION, VERSION)
GAMES = ('dice', 'keno', 'plinko', 'blackjack', 'limbo', 'coinflip', 'poker', 'baccarat')
RISKS = ('low', 'medium', 'high')
SCALE = 10000

# Fixed, symmetric v2 Plinko paytables, stored as exact 1/10,000 units.
# The highest edge multiplier is 1000x on the 16-row High board.
# v1 tables remain available below to verify all earlier receipts.
PLINKO_TABLES = {
    8: {
        'low': (56000, 21000, 11000, 10000, 5000, 10000, 11000, 21000, 56000),
        'medium': (130000, 30000, 13000, 7000, 4000, 7000, 13000, 30000, 130000),
        'high': (290000, 40000, 15000, 3000, 2000, 3000, 15000, 40000, 290000),
    },
    12: {
        'low': (100000, 30000, 16000, 14000, 11000, 10000, 5000, 10000, 11000, 14000, 16000, 30000, 100000),
        'medium': (330000, 110000, 40000, 20000, 11000, 6000, 3000, 6000, 11000, 20000, 40000, 110000, 330000),
        'high': (1700000, 240000, 81000, 20000, 7000, 2000, 2000, 2000, 7000, 20000, 81000, 240000, 1700000),
    },
    16: {
        'low': (160000, 90000, 20000, 14000, 14000, 12000, 11000, 10000, 5000, 10000, 11000, 12000, 14000, 14000, 20000, 90000, 160000),
        'medium': (1100000, 410000, 100000, 50000, 30000, 15000, 10000, 5000, 3000, 5000, 10000, 15000, 30000, 50000, 100000, 410000, 1100000),
        'high': (10000000, 1300000, 260000, 90000, 40000, 20000, 2000, 2000, 2000, 2000, 2000, 20000, 40000, 90000, 260000, 1300000, 10000000),
    },
}


def commitment(seed):
    return hashlib.sha256(bytes.fromhex(seed)).hexdigest()


def options_for(game, value):
    if not isinstance(value, dict):
        raise ValueError('Choose valid game settings.')
    if game == 'dice':
        chance, side = value.get('chance'), value.get('side')
        if type(chance) is not int or not 1 <= chance <= 95 or side not in {'under', 'over'}:
            raise ValueError('Choose a win chance from 1 to 95 and Roll under or Roll over.')
        return dict(chance=chance, side=side)
    if game == 'blackjack':
        if type(value.get('decks')) is not int or value['decks'] != 6:
            raise ValueError('Blackjack uses six decks.')
        return dict(decks=6)
    if game == 'baccarat':
        if type(value.get('decks')) is not int or value['decks'] != 8 or value.get('side') not in ('player', 'banker', 'tie'):
            raise ValueError('Choose Player, Banker or Tie. Baccarat uses eight decks.')
        return dict(decks=8, side=value['side'])
    if game == 'limbo':
        target = value.get('target')
        if type(target) is not int or not 101 <= target <= 100_000_000:
            raise ValueError('Choose a Limbo target from 1.01x to 1,000,000.00x, in 0.01 steps.')
        return dict(target=target)  # Hundredths, never binary floating-point money.
    if game == 'coinflip':
        if value.get('side') not in ('heads', 'tails'):
            raise ValueError('Choose Heads or Tails.')
        return dict(side=value['side'])
    if game == 'poker':
        if value.get('variant') != 'jacks_or_better':
            raise ValueError('Poker uses the published Jacks or Better paytable.')
        return dict(variant='jacks_or_better')
    risk = value.get('risk')
    if risk not in RISKS:
        raise ValueError('Choose Low, Medium, or High risk.')
    if game == 'keno':
        picks = value.get('picks')
        if (not isinstance(picks, list) or not 1 <= len(picks) <= 10 or
                any(type(n) is not int or not 1 <= n <= 40 for n in picks) or len(set(picks)) != len(picks)):
            raise ValueError('Pick 1–10 different numbers from 1 to 40.')
        return dict(picks=sorted(picks), risk=risk)
    if game == 'plinko' and type(value.get('rows')) is int and value['rows'] in {8, 12, 16}:
        return dict(risk=risk, rows=value['rows'])
    raise ValueError('Choose a game with valid settings.')


@lru_cache(maxsize=128)
def table(game, size, risk, version=VERSION):
    """Return exact units for the selected version's published paytable.

    V2 Plinko uses fixed tables. Keno and legacy Plinko scale probability
    weights toward 99%; all final payouts round down to whole points.
    """
    if version not in SUPPORTED_VERSIONS:
        raise ValueError('Unknown game rules version.')
    if game == 'plinko' and version != LEGACY_VERSION:
        return PLINKO_TABLES[size][risk]
    power = dict(low=2, medium=4, high=7)[risk]
    if game == 'keno':
        probabilities = [Fraction(comb(size, h)*comb(40-size, 10-h), comb(40, 10)) for h in range(size+1)]
        weights = [Fraction(h**power) for h in range(size+1)]
    elif game == 'plinko':
        probabilities = [Fraction(comb(size, slot), 2**size) for slot in range(size+1)]
        weights = [Fraction(1, 2) + abs(2*slot-size)**power for slot in range(size+1)]
    else:
        raise ValueError('Unsupported payout table.')
    average = sum(p*w for p, w in zip(probabilities, weights))
    values = tuple(int(Fraction(99, 100)*w/average*SCALE) for w in weights)
    return values


def table_info(game, size, risk):
    values = table(game, size, risk)
    probabilities = ([Fraction(comb(size, h)*comb(40-size, 10-h), comb(40, 10)) for h in range(size+1)]
                     if game == 'keno' else [Fraction(comb(size, i), 2**size) for i in range(size+1)])
    rtp = sum(p*Fraction(v, SCALE) for p, v in zip(probabilities, values))
    return dict(multipliers=list(values), rtp_percent=f'{float(rtp)*100:.4f}',
                probabilities=[float(p) for p in probabilities])


@lru_cache(maxsize=1)
def rules():
    from poker import PAYTABLE, LABELS
    from baccarat import RETURNS
    return dict(version=VERSION, scale=SCALE, games=list(GAMES), min_wager=1, max_wager=None,
                dice_rtp_percent='99.0000',
                limbo=dict(min_target=101, max_target=100_000_000, scale=100, outcomes=2**32),
                coinflip=dict(multiplier=19800, win_probability=0.5),
                poker=dict(variant='jacks_or_better', paytable=PAYTABLE, labels=LABELS),
                baccarat=dict(decks=8, returns=RETURNS),
                keno={str(k):{risk:table_info('keno', k, risk) for risk in RISKS} for k in range(1,11)},
                plinko={str(k):{risk:table_info('plinko', k, risk) for risk in RISKS} for k in (8,12,16)})


def max_payout(game, wager, opt):
    """Exact upper bound used before reserving a stake or granting more funds."""
    if game == 'blackjack': return wager*4
    if game == 'baccarat':
        from baccarat import RETURNS
        return wager*RETURNS[opt['side']]//SCALE
    if game == 'poker': return wager*800
    if game == 'limbo': return wager*opt['target']//100
    if game == 'coinflip': return wager*198//100
    if game == 'dice': return wager*99//opt['chance']
    return wager*max(table(game, len(opt['picks']) if game == 'keno' else opt['rows'], opt['risk']))//SCALE


class Draw:
    def __init__(self, seed, receipt):
        self.key = bytes.fromhex(seed)
        version = receipt.get('rules_version', VERSION)
        if version not in SUPPORTED_VERSIONS:
            raise ValueError('Unknown game rules version.')
        self.context = [version, receipt['season'], receipt['game'], receipt['client_seed'],
                        receipt['client_salt'], receipt['nonce'], receipt['wager'], receipt['options']]
        self.block, self.buffer = 0, b''

    def below(self, size):
        # Rejection sampling removes modulo bias, including Keno's changing pool.
        boundary = 2**32 - 2**32 % size
        while True:
            if len(self.buffer) < 4:
                message = json.dumps([*self.context, self.block], sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')
                self.buffer = hmac.new(self.key, message, hashlib.sha256).digest()
                self.block += 1
            value, self.buffer = int.from_bytes(self.buffer[:4], 'big'), self.buffer[4:]
            if value < boundary:
                return value % size


def outcome(seed, receipt):
    game, opt, wager = receipt['game'], options_for(receipt['game'], receipt['options']), receipt['wager']
    version = receipt.get('rules_version', VERSION)
    if game in ('limbo', 'coinflip', 'poker') and version not in POKER_VERSIONS:
        raise ValueError('This game requires redpoints-v3 or later.')
    draw = Draw(seed, {**receipt, 'options':opt})
    if game == 'baccarat':
        if version != VERSION:
            raise ValueError('Baccarat requires redpoints-v4.')
        from baccarat import replay
        return replay(draw, wager, opt['side'])
    if game == 'limbo':
        roll = draw.below(2**32)
        multiplier = max(100, 99*2**32//(2**32-roll))
        won = multiplier >= opt['target']
        return dict(roll=roll, multiplier=multiplier, won=won,
                    payout=wager*opt['target']//100 if won else 0)
    if game == 'coinflip':
        side = ('heads', 'tails')[draw.below(2)]
        won = side == opt['side']
        return dict(side=side, won=won, multiplier=19800, payout=wager*198//100 if won else 0)
    if game == 'poker':
        from poker import replay
        return replay(draw, wager, receipt.get('holds'))
    if game == 'dice':
        roll = draw.below(10000)
        win = roll < opt['chance']*100 if opt['side']=='under' else roll >= 10000-opt['chance']*100
        payout = wager*99//opt['chance'] if win else 0
        return dict(roll=roll, won=win, payout=payout)
    if game == 'keno':
        numbers = list(range(1, 41))
        drawn = []
        for i in range(10):
            j = i + draw.below(40-i)
            numbers[i], numbers[j] = numbers[j], numbers[i]
            drawn.append(numbers[i])
        hits = len(set(drawn) & set(opt['picks']))
        units = table(game, len(opt['picks']), opt['risk'], receipt.get('rules_version', VERSION))[hits]
        return dict(drawn=drawn, hits=hits, multiplier=units, payout=wager*units//SCALE)
    if game == 'blackjack':
        if version not in BLACKJACK_VERSIONS:
            raise ValueError('Blackjack requires redpoints-v2 or later.')
        from blackjack import replay
        return replay(draw, wager, receipt.get('actions', []))
    path = [draw.below(2) for _ in range(opt['rows'])]
    slot = sum(path)
    units = table(game, opt['rows'], opt['risk'], receipt.get('rules_version', VERSION))[slot]
    return dict(path=path, slot=slot, multiplier=units, payout=wager*units//SCALE)


def _verify(receipt, expected_commitment=None):
    """Offline verifier. Compare against the commitment retained before betting."""
    if (not isinstance(receipt, dict) or receipt.get('rules_version') not in SUPPORTED_VERSIONS or
        any(type(receipt.get(k)) is not int or abs(receipt[k]) > 2**53-1 for k in ('nonce', 'wager', 'payout', 'net')) or
        receipt['wager'] < 1 or receipt['nonce'] < 0 or
        not isinstance(receipt.get('season'), str) or not re.fullmatch(r'\d{1,12}', receipt['season']) or
        not isinstance(receipt.get('client_seed'), str) or not re.fullmatch(r'[A-Za-z0-9 _.-]{1,64}', receipt['client_seed']) or
        not isinstance(receipt.get('client_salt'), str) or not re.fullmatch(r'[a-f0-9]{32}', receipt['client_salt']) or
        not isinstance(receipt.get('server_seed'), str) or not re.fullmatch(r'[a-f0-9]{64}', receipt['server_seed'])):
        return False
    if options_for(receipt.get('game'), receipt.get('options')) != receipt['options']:
        return False
    if commitment(receipt['server_seed']) != receipt['commitment']:
        return False
    if expected_commitment is not None and expected_commitment != receipt['commitment']:
        return False
    result = outcome(receipt['server_seed'], receipt)
    if receipt['game'] in ('blackjack', 'poker') and not result['ended']:
        return False
    stake = result['total_wager'] if receipt['game'] == 'blackjack' else receipt['wager']
    return result == receipt['result'] and receipt['payout'] == result['payout'] and receipt['net'] == result['payout']-stake


def verify(receipt, expected_commitment=None):
    """Reject malformed/unverifiable receipts without crashing the verifier."""
    try:
        return _verify(receipt, expected_commitment)
    except (KeyError, TypeError, ValueError, OverflowError):
        return False
