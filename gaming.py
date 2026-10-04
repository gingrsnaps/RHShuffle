"""Shared play-point wallets. All debits, outcomes, receipts and ranks commit once.

Uses the existing JSON transaction and signed browser identity. No money, SQL,
Botrix balance integration, daily wager cap, or separate launch process.
"""
import copy
import hashlib
import logging
import re
import secrets
import time

from fairness import VERSION, GAMES, commitment, options_for, outcome, table
from weekly_history import completed_weeks

LOG = logging.getLogger('redhunllef')
START_POINTS = 100000
MAX_NUMBER = 2**53-1
MAX_PLAYERS = 10000
RECEIPTS = 30


class GamingError(ValueError):
    def __init__(self, message, code='invalid_bet', status=422):
        super().__init__(message)
        self.code, self.status = code, status


def season(now=None):
    # This is the same Tuesday 18:00 America/New_York boundary as race history.
    # It advances even if the host has not yet edited an expired race form.
    from datetime import datetime, timedelta
    from race_support import EASTERN, fmt_et
    end = completed_weeks(now)[0]['end_time']
    following = int((datetime.fromtimestamp(end, EASTERN)+timedelta(days=7)).timestamp())
    return dict(id=str(end), start_time=end, end_time=following, end_et=fmt_et(following))


def player_key(identity):
    return hashlib.sha256(('redpoints-player-v1:'+identity).encode()).hexdigest()


def fresh_stats():
    return {game:dict(bets=0, wagered=0, paid=0, net=0, biggest_payout=0) for game in GAMES}


def validate_gaming(value):
    """Fail closed on malformed recovery, without overwriting existing saves."""
    if value is None:
        return None
    if not isinstance(value, dict) or value.get('version') != 1 or not isinstance(value.get('players'), dict) or len(value['players']) > MAX_PLAYERS:
        raise ValueError('Invalid RedPoints recovery.')
    for key, player in value['players'].items():
        if not re.fullmatch(r'[a-f0-9]{64}', key) or not isinstance(player, dict):
            raise ValueError('Invalid RedPoints player.')
        if not isinstance(player.get('name'), str) or not 1 <= len(player['name']) <= 64:
            raise ValueError('Invalid RedPoints display name.')
        if not isinstance(player.get('season'), str) or not re.fullmatch(r'\d{1,12}', player['season']):
            raise ValueError('Invalid RedPoints season.')
        if not isinstance(player.get('server_seed'), str) or not re.fullmatch(r'[a-f0-9]{64}', player['server_seed']):
            raise ValueError('Invalid RedPoints fairness seed.')
        for name in ('balance', 'nonce', 'version'):
            if type(player.get(name)) is not int or not 0 <= player[name] <= MAX_NUMBER:
                raise ValueError('Invalid RedPoints wallet counter.')
        if set(player.get('stats', {})) != set(GAMES):
            raise ValueError('Invalid RedPoints game statistics.')
        for stats in player['stats'].values():
            for name in ('bets','wagered','paid','biggest_payout'):
                if type(stats.get(name)) is not int or not 0 <= stats[name] <= MAX_NUMBER:
                    raise ValueError('Invalid RedPoints winnings.')
            if stats.get('net') != stats['paid']-stats['wagered']:
                raise ValueError('RedPoints winnings do not balance.')
        if player['balance'] != START_POINTS + sum(s['net'] for s in player['stats'].values()):
            raise ValueError('RedPoints wallet does not balance.')
        receipts = player.get('receipts')
        if not isinstance(receipts, list) or len(receipts) > RECEIPTS:
            raise ValueError('Invalid RedPoints receipts.')
        seen = set()
        if len(receipts) != min(RECEIPTS, player['nonce']):
            raise ValueError('RedPoints receipt sequence is incomplete.')
        from fairness import verify
        for index, receipt in enumerate(receipts):
            try:
                valid = (isinstance(receipt, dict) and receipt['request_id'] not in seen and
                         type(receipt['nonce']) is int and receipt['nonce'] == player['nonce']-1-index and
                         type(receipt['wager']) is int and 1 <= receipt['wager'] <= MAX_NUMBER and verify(receipt))
                if not valid: raise ValueError('Invalid receipt')
                seen.add(receipt['request_id'])
            except (KeyError, TypeError, ValueError):
                raise ValueError('A saved RedPoints receipt failed verification.') from None
    return value


class Gaming:
    def __init__(self, store):
        self.store = store
        with store.connection() as conn:
            validate_gaming(conn.get('gaming'))

    def _player(self, conn, identity, name, now):
        current = season(now)
        if conn.get('gaming') is None:
            conn['gaming'] = dict(version=1, players={})
        players = conn['gaming']['players']
        key = player_key(identity)
        if key not in players:
            if len(players) >= MAX_PLAYERS:
                raise GamingError('The player registry is full. Contact the host.', 'capacity', 409)
            players[key] = dict(name=name, season=current['id'], balance=START_POINTS, stats=fresh_stats(),
                                nonce=0, version=1, server_seed=secrets.token_hex(32), receipts=[], last_bet_at=0)
        player = players[key]
        if int(player['season']) > int(current['id']):
            raise GamingError('The server clock moved backwards. The saved wallet is protected.', 'clock', 409)
        if player['season'] != current['id']:
            player.update(season=current['id'], balance=START_POINTS, stats=fresh_stats(), version=player['version']+1)
        player['name'] = name
        return player, current

    @staticmethod
    def _view(player, current):
        return dict(season=current, name=player['name'], balance=player['balance'], nonce=player['nonce'],
                    version=player['version'], commitment=commitment(player['server_seed']),
                    stats=copy.deepcopy(player['stats']), receipts=copy.deepcopy(player['receipts']),
                    needs_profile=False, rules_version=VERSION)

    def view(self, identity, name, now=None):
        now = time.time() if now is None else now
        if not name:
            return dict(season=season(now), balance=START_POINTS, name='', nonce=0, version=0,
                        commitment='', stats=fresh_stats(), receipts=[], needs_profile=True, rules_version=VERSION)
        current = season(now)
        # Routine five-second reads neither copy the complete community save nor
        # rewrite it. Open a write transaction only for signup, rename or reset.
        with self.store.connection() as conn:
            player = (conn.get('gaming') or {}).get('players', {}).get(player_key(identity))
            if player and player['season'] == current['id'] and player['name'] == name:
                return self._view(player, current)
        with self.store.connection(transaction=True) as conn:
            player, current = self._player(conn, identity, name, now)
            return self._view(player, current)

    def bet(self, identity, name, body, now=None):
        if not name:
            raise GamingError('Save your player name before playing.', 'username_required', 409)
        if not isinstance(body, dict):
            raise GamingError('Send a valid wager.')
        game, request_id = body.get('game'), body.get('request_id')
        if game not in GAMES or not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', request_id):
            raise GamingError('Choose a game and provide a valid bet receipt ID.')
        opt = options_for(game, body.get('options'))
        wager, nonce = body.get('wager'), body.get('nonce')
        # There is no fixed stake cap or timed delay. Keep amounts exact across
        # Python and JavaScript; the wallet balance remains authoritative.
        if type(wager) is not int or not 1 <= wager <= MAX_NUMBER:
            raise GamingError('Enter a positive whole-point wager within the supported exact-integer range.')
        if type(nonce) is not int or nonce < 0:
            raise GamingError('Reload the fairness details before playing.')
        client, salt = body.get('client_seed'), body.get('client_salt')
        if not isinstance(client, str) or not re.fullmatch(r'[A-Za-z0-9 _.-]{1,64}', client):
            raise GamingError('Use 1–64 letters, numbers, spaces, dots, underscores or hyphens for your client seed.')
        if not isinstance(salt, str) or not re.fullmatch(r'[a-f0-9]{32}', salt):
            raise GamingError('Your browser must generate fresh entropy for this bet.')
        now = time.time() if now is None else now
        with self.store.connection(transaction=True) as conn:
            player, current = self._player(conn, identity, name, now)
            duplicate = next((r for r in player['receipts'] if r['request_id']==request_id), None)
            if duplicate:
                return dict(ok=True, duplicate=True, receipt=copy.deepcopy(duplicate), wallet=self._view(player, current))
            if body.get('season') != current['id']:
                raise GamingError('A new wager-race week started. Refresh to use your new 100,000 RedPoints.', 'new_season', 409)
            if nonce != player['nonce'] or body.get('commitment') != commitment(player['server_seed']):
                raise GamingError('Another tab used this seed. Refresh your balance and fairness details.', 'stale_seed', 409)
            if wager > player['balance']:
                raise GamingError('Not enough RedPoints. Lower the wager or wait for the next race reset.', 'balance', 409)
            largest = wager*99//opt['chance'] if game=='dice' else wager*max(table(game, len(opt['picks']) if game=='keno' else opt['rows'], opt['risk']))//10000
            stats = player['stats'][game]
            if max(player['balance']-wager+largest, stats['paid']+largest, stats['wagered']+wager,
                   player['nonce']+1, player['version']+1) > MAX_NUMBER:
                raise GamingError('This wallet reached its supported numeric range.', 'capacity', 409)
            receipt = dict(rules_version=VERSION, season=current['id'], request_id=request_id, game=game,
                           client_seed=client, client_salt=salt, nonce=nonce, wager=wager, options=opt,
                           commitment=commitment(player['server_seed']), server_seed=player['server_seed'], at=int(now))
            result = outcome(player['server_seed'], receipt)
            payout, net = result['payout'], result['payout']-wager
            player.update(balance=player['balance']+net, nonce=nonce+1, server_seed=secrets.token_hex(32),
                          version=player['version']+1, last_bet_at=now)
            receipt.update(result=result, payout=payout, net=net, balance_after=player['balance'], next_commitment=commitment(player['server_seed']))
            stats.update(bets=stats['bets']+1, wagered=stats['wagered']+wager, paid=stats['paid']+payout,
                         net=stats['net']+net, biggest_payout=max(stats['biggest_payout'], payout))
            player['receipts'] = [receipt]+player['receipts'][:RECEIPTS-1]
            # Atomic JSON commit happens when this context exits. No points are
            # returned to the browser unless the wager and its proof were saved.
            response = dict(ok=True, duplicate=False, receipt=copy.deepcopy(receipt), wallet=self._view(player, current))
        LOG.info('GAMING %s bet committed; nonce=%s wager=%s payout=%s.', game, nonce, wager, payout)
        return response

    def leaders(self, now=None):
        current = season(now)
        with self.store.connection() as conn:
            players = (conn.get('gaming') or {}).get('players', {})
            result = {}
            for game in GAMES:
                rows = [dict(name=p['name'], player_tag=key[:8], **p['stats'][game]) for key,p in players.items()
                        if p['season']==current['id'] and p['stats'][game]['bets']]
                rows.sort(key=lambda p:(-p['net'], -p['paid'], p['player_tag']))
                result[game] = rows[:5]
            return dict(season=current, games=result)

    def recovery(self):
        with self.store.connection() as conn:
            return copy.deepcopy(conn.get('gaming'))
