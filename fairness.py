"""RedPoints v1: deterministic games and exact, published payout calculations.

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

VERSION = 'redpoints-v1'
GAMES = ('dice', 'keno', 'plinko')
RISKS = ('low', 'medium', 'high')
SCALE = 10000


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
    raise ValueError('Choose Dice, Keno, or Plinko with valid settings.')


@lru_cache(maxsize=64)
def table(game, size, risk):
    """Scale transparent risk weights to 99% RTP, then round DOWN to 4dp.

    Rounding cannot increase the stated return. Whole-point payout rounding can
    reduce it further for very small wagers; the UI shows that explicitly.
    """
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
    return dict(version=VERSION, scale=SCALE, games=list(GAMES), min_wager=1, max_wager=None,
                dice_rtp_percent='99.0000',
                keno={str(k):{risk:table_info('keno', k, risk) for risk in RISKS} for k in range(1,11)},
                plinko={str(k):{risk:table_info('plinko', k, risk) for risk in RISKS} for k in (8,12,16)})


class Draw:
    def __init__(self, seed, receipt):
        self.key = bytes.fromhex(seed)
        self.context = [VERSION, receipt['season'], receipt['game'], receipt['client_seed'],
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
    draw = Draw(seed, {**receipt, 'options':opt})
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
        units = table(game, len(opt['picks']), opt['risk'])[hits]
        return dict(drawn=drawn, hits=hits, multiplier=units, payout=wager*units//SCALE)
    path = [draw.below(2) for _ in range(opt['rows'])]
    slot = sum(path)
    units = table(game, opt['rows'], opt['risk'])[slot]
    return dict(path=path, slot=slot, multiplier=units, payout=wager*units//SCALE)


def verify(receipt, expected_commitment=None):
    """Offline verifier. Compare against the commitment retained before betting."""
    if (not isinstance(receipt, dict) or receipt.get('rules_version') != VERSION or
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
    return result == receipt['result'] and receipt['payout'] == result['payout'] and receipt['net'] == result['payout']-receipt['wager']
