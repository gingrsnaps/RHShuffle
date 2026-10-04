"""Shared play-point wallets. All debits, outcomes, receipts and ranks commit once.

Uses the existing JSON transaction, signed browser identity and weekly IP binding. No money, SQL,
Botrix balance integration, daily wager cap, or separate launch process.
"""
import copy
import hashlib
import hmac
import ipaddress
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
MAX_IP_BINDINGS = MAX_PLAYERS * 4


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


def canonical_ip(address):
    """Normalize aliases; request headers are resolved by the trusted web layer."""
    if not isinstance(address, str) or '%' in address:
        raise ValueError('A valid visitor IP is required.')
    value = ipaddress.ip_address(address)
    if isinstance(value, ipaddress.IPv6Address) and value.ipv4_mapped:
        value = value.ipv4_mapped
    return str(value)


def ip_key(guard, address):
    # Key ownership by a stable digest. Canonical addresses are stored separately
    # for the private admin view, never in public wallet responses or bet logs.
    return hmac.new(bytes.fromhex(guard['salt']), canonical_ip(address).encode('ascii'), hashlib.sha256).hexdigest()


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
        if set(player.get('stats', {})) not in (set(GAMES), set(GAMES)-{'blackjack'}):
            raise ValueError('Invalid RedPoints game statistics.')
        for stats in player['stats'].values():
            for name in ('bets','wagered','paid','biggest_payout'):
                if type(stats.get(name)) is not int or not 0 <= stats[name] <= MAX_NUMBER:
                    raise ValueError('Invalid RedPoints winnings.')
            if stats.get('net') != stats['paid']-stats['wagered']:
                raise ValueError('RedPoints winnings do not balance.')
        pending = player.get('blackjack')
        reserved = 0
        if pending is not None:
            try:
                if (pending['game'] != 'blackjack' or pending['rules_version'] != VERSION or
                        pending['nonce'] != player['nonce'] or pending['server_seed'] != player['server_seed'] or
                        pending['commitment'] != commitment(player['server_seed']) or pending['season'] != player['season'] or
                        type(pending['wager']) is not int or not 1 <= pending['wager'] <= MAX_NUMBER or
                        not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', pending['request_id']) or
                        not re.fullmatch(r'[a-f0-9]{32}', pending['client_salt']) or
                        not re.fullmatch(r'[A-Za-z0-9 _.-]{1,64}', pending['client_seed']) or
                        len(pending['action_ids']) != len(pending['actions']) or
                        len(set(pending['action_ids'])) != len(pending['action_ids']) or
                        any(not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', item) for item in pending['action_ids']) or
                        outcome(player['server_seed'], pending)['ended']):
                    raise ValueError('Invalid active hand')
                reserved = pending['wager']
            except (KeyError, TypeError, ValueError):
                raise ValueError('Invalid saved Blackjack hand.') from None
        # Refresh grants belong to the wallet, never to game winnings/rankings.
        # Older saves have no adjustment and retain their original accounting.
        adjustment = player.get('balance_adjustment', 0)
        if type(adjustment) is not int or abs(adjustment) > MAX_NUMBER:
            raise ValueError('Invalid RedPoints refresh adjustment.')
        if player['balance'] != START_POINTS + adjustment + sum(s['net'] for s in player['stats'].values()) - reserved:
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
    guard = value.get('ip_guard')
    if guard is not None:
        if (not isinstance(guard, dict) or guard.get('version') != 1 or
                not isinstance(guard.get('salt'), str) or not re.fullmatch(r'[a-f0-9]{64}', guard['salt']) or
                not isinstance(guard.get('season'), str) or not re.fullmatch(r'\d{1,12}', guard['season']) or
                not isinstance(guard.get('claims'), dict) or len(guard['claims']) > MAX_IP_BINDINGS):
            raise ValueError('Invalid RedPoints IP bindings.')
        for address, owner in guard['claims'].items():
            if (not isinstance(address, str) or not re.fullmatch(r'[a-f0-9]{64}', address) or
                    not isinstance(owner, str) or owner not in value['players']):
                raise ValueError('Invalid RedPoints IP owner.')
        addresses = guard.get('addresses', {})
        if not isinstance(addresses, dict) or set(addresses)-set(guard['claims']):
            raise ValueError('Invalid private IP directory.')
        for digest, address in addresses.items():
            if canonical_ip(address) != address or ip_key(guard, address) != digest:
                raise ValueError('Invalid private IP address.')
    return value


class Gaming:
    def __init__(self, store):
        self.store = store
        with store.connection() as conn:
            validate_gaming(conn.get('gaming'))
        # Adding a game never resets an existing wallet, seed or receipt.
        with store.connection(transaction=True) as conn:
            for player in (conn.get('gaming') or {}).get('players', {}).values():
                player['stats'].setdefault('blackjack', fresh_stats()['blackjack'])

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
            if player.get('blackjack'):
                receipt = player['blackjack']
                receipt['actions'].append('stand')
                receipt['ending'] = 'weekly_reset'
                self._settle(player, receipt, outcome(player['server_seed'], receipt))
            player.update(season=current['id'], balance=START_POINTS, balance_adjustment=0,
                          stats=fresh_stats(), version=player['version']+1)
        if player['name'] != name:
            player['name'] = name
            player['version'] += 1
        return player, current

    @staticmethod
    def _ip_issue(data, key, address, current):
        try:
            address = canonical_ip(address)
        except ValueError:
            return dict(code='ip_unavailable', message='Your connection could not be verified. Reload, or ask the host to check visitor IP settings.')
        guard = (data or {}).get('ip_guard')
        if guard and int(guard['season']) > int(current['id']):
            return dict(code='clock', message='The server clock moved backwards. Your saved points are protected.')
        if guard and guard['season'] == current['id']:
            owner = guard['claims'].get(ip_key(guard, address))
            if owner and owner != key:
                return dict(code='ip_wallet_exists', message='This public IP already has a RedPoints wallet this race week. Restore that player with its recovery code, or use your usual connection.')
        return None

    def _claim_ip(self, data, key, address, current):
        issue = self._ip_issue(data, key, address, current)
        if issue:
            raise GamingError(issue['message'], issue['code'], 409)
        guard = data.get('ip_guard')
        if guard is None:
            guard = data['ip_guard'] = dict(version=1, salt=secrets.token_hex(32), season=current['id'], claims={}, addresses={})
        if guard['season'] != current['id']:
            guard.update(season=current['id'], claims={}, addresses={})
        digest = ip_key(guard, address)
        if digest not in guard['claims']:
            if len(guard['claims']) >= MAX_IP_BINDINGS:
                raise GamingError('The connection registry is full. Contact the host.', 'capacity', 409)
            guard['claims'][digest] = key
        guard.setdefault('addresses', {})[digest] = canonical_ip(address)

    @staticmethod
    def _hand_view(player):
        receipt = player.get('blackjack')
        if not receipt:
            return None
        value = outcome(player['server_seed'], receipt)
        # Never expose the unrevealed seed, hole card or remaining shoe.
        from blackjack import total
        value.update(dealer=[value['dealer'][0], None], dealer_total=total(value['dealer'][:1])[0],
                     dealer_soft=False, round_id=receipt['request_id'], step=len(receipt['actions']),
                     wager=receipt['wager'], can_double=not receipt['actions'] and player['balance'] >= receipt['wager'])
        value['bet'] = {k:v for k,v in receipt.items() if k not in {'server_seed', 'actions', 'action_ids'}}
        return value

    @staticmethod
    def _view(player, current, issue=None):
        return dict(season=current, name=player['name'], balance=player['balance'], nonce=player['nonce'],
                    version=player['version'], commitment=commitment(player['server_seed']),
                    stats=copy.deepcopy(player['stats']), receipts=copy.deepcopy(player['receipts']),
                    needs_profile=False, rules_version=VERSION, ip_bound=issue is None, play_blocked=issue,
                    blackjack=Gaming._hand_view(player))

    def view(self, identity, name, now=None, *, client_ip=None):
        now = time.time() if now is None else now
        current = season(now)
        key = player_key(identity)
        def preview(issue):
            return dict(season=current, balance=0 if issue else START_POINTS, name=name or '', nonce=0, version=0,
                        commitment='', stats=fresh_stats(), receipts=[], needs_profile=not bool(name),
                        rules_version=VERSION, ip_bound=False, play_blocked=issue, blackjack=None)
        # Routine five-second reads neither copy the complete community save nor
        # rewrite it. IP claims and wallet creation share the same transaction.
        with self.store.connection() as conn:
            data = conn.get('gaming') or {}
            issue = self._ip_issue(data, key, client_ip, current)
            player = data.get('players', {}).get(key)
            if not name or (issue and not player):
                return preview(issue)
            if player and player['season'] == current['id'] and player['name'] == name:
                guard = data.get('ip_guard')
                if issue or (guard and guard['season'] == current['id'] and
                             guard['claims'].get(ip_key(guard, client_ip)) == key and
                             ip_key(guard, client_ip) in guard.get('addresses', {})):
                    return self._view(player, current, issue)
        with self.store.connection(transaction=True) as conn:
            data = conn.get('gaming') or {}
            issue = self._ip_issue(data, key, client_ip, current)
            if issue and key not in data.get('players', {}):
                return preview(issue)
            player, current = self._player(conn, identity, name, now)
            if not issue:
                self._claim_ip(conn['gaming'], key, client_ip, current)
            return self._view(player, current, issue)

    def refresh_balance(self, identity, name, body, now=None, *, client_ip=None):
        """Reset available points on a browser refresh; preserve all game records.

        Reads and automatic polls never call this method. The version check makes
        retries harmless and prevents a stale page from overwriting a newer bet.
        An unfinished Blackjack stake stays reserved; its hand/seed are untouched.
        """
        if not name:
            raise GamingError('Save your player name before refreshing points.', 'username_required', 409)
        if (not isinstance(body, dict) or type(body.get('version')) is not int or
                not 0 <= body['version'] <= MAX_NUMBER or not isinstance(body.get('season'), str) or
                not re.fullmatch(r'\d{1,12}', body['season'])):
            raise GamingError('Reload the page to refresh your RedPoints.')
        now = time.time() if now is None else now
        with self.store.connection(transaction=True) as conn:
            player, current = self._player(conn, identity, name, now)
            self._claim_ip(conn['gaming'], player_key(identity), client_ip, current)
            if body['season'] != current['id']:
                # The weekly rollover already supplies the new allowance.
                return dict(ok=True, wallet=self._view(player, current))
            if body['version'] != player['version']:
                raise GamingError('Your balance changed in another request. Reload to refresh the latest wallet.',
                                  'stale_wallet', 409)
            adjustment = player.get('balance_adjustment', 0) + START_POINTS - player['balance']
            if abs(adjustment) > MAX_NUMBER or player['version'] >= MAX_NUMBER:
                raise GamingError('This wallet reached its supported numeric range.', 'capacity', 409)
            player.update(balance=START_POINTS, balance_adjustment=adjustment, version=player['version']+1)
            LOG.info('GAMING browser refresh restored %s RedPoints; game records retained.', START_POINTS)
            return dict(ok=True, wallet=self._view(player, current))

    def bet(self, identity, name, body, now=None, *, client_ip=None):
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
                issue = self._ip_issue(conn['gaming'], player_key(identity), client_ip, current)
                return dict(ok=True, duplicate=True, receipt=copy.deepcopy(duplicate), wallet=self._view(player, current, issue))
            # Old receipts remain recoverable, but new wagers must use v2.
            if body.get('rules_version') != VERSION:
                raise GamingError('Game rules changed. Reload before placing another wager.', 'release_mismatch', 409)
            self._claim_ip(conn['gaming'], player_key(identity), client_ip, current)
            active = player.get('blackjack')
            if active:
                if active['request_id'] == request_id:
                    return dict(ok=True, duplicate=True, receipt=None, wallet=self._view(player, current))
                raise GamingError('Finish your Blackjack hand before starting another game.', 'active_hand', 409)
            if body.get('season') != current['id']:
                raise GamingError('A new wager-race week started. Refresh to use your new 100,000 RedPoints.', 'new_season', 409)
            if nonce != player['nonce'] or body.get('commitment') != commitment(player['server_seed']):
                raise GamingError('Another tab used this seed. Refresh your balance and fairness details.', 'stale_seed', 409)
            if wager > player['balance']:
                raise GamingError('Not enough RedPoints. Lower the wager or refresh the page for 100,000 RedPoints.', 'balance', 409)
            largest = (wager*4 if game=='blackjack' else wager*99//opt['chance'] if game=='dice' else
                       wager*max(table(game, len(opt['picks']) if game=='keno' else opt['rows'], opt['risk']))//10000)
            stats = player['stats'][game]
            if max(player['balance']-wager+largest, stats['paid']+largest, stats['wagered']+wager*(2 if game=='blackjack' else 1),
                   player['nonce']+1, player['version']+1) > MAX_NUMBER:
                raise GamingError('This wallet reached its supported numeric range.', 'capacity', 409)
            receipt = dict(rules_version=VERSION, season=current['id'], request_id=request_id, game=game,
                           client_seed=client, client_salt=salt, nonce=nonce, wager=wager, options=opt,
                           commitment=commitment(player['server_seed']), server_seed=player['server_seed'], at=int(now))
            if game == 'blackjack':
                receipt.update(actions=[], action_ids=[])
            result = outcome(player['server_seed'], receipt)
            player['balance'] -= wager
            if game == 'blackjack' and not result['ended']:
                player['blackjack'] = receipt
                player['version'] += 1
                return dict(ok=True, duplicate=False, receipt=None, wallet=self._view(player, current))
            self._settle(player, receipt, result)
            return dict(ok=True, duplicate=False, receipt=copy.deepcopy(receipt), wallet=self._view(player, current))

    @staticmethod
    def _settle(player, receipt, result):
        """Credit once after the complete stake has been reserved in this transaction."""
        wager = result['total_wager'] if receipt['game'] == 'blackjack' else receipt['wager']
        payout, net = result['payout'], result['payout']-wager
        player.update(balance=player['balance']+payout, nonce=player['nonce']+1,
                      server_seed=secrets.token_hex(32), version=player['version']+1, last_bet_at=receipt['at'])
        player.pop('blackjack', None)
        receipt.update(result=result, payout=payout, net=net, balance_after=player['balance'],
                       next_commitment=commitment(player['server_seed']))
        stats = player['stats'][receipt['game']]
        stats.update(bets=stats['bets']+1, wagered=stats['wagered']+wager, paid=stats['paid']+payout,
                     net=stats['net']+net, biggest_payout=max(stats['biggest_payout'], payout))
        player['receipts'] = [copy.deepcopy(receipt)]+player['receipts'][:RECEIPTS-1]
        LOG.info('GAMING %s settled; nonce=%s wager=%s payout=%s.', receipt['game'], receipt['nonce'], wager, payout)

    def blackjack_action(self, identity, name, body, now=None, *, client_ip=None):
        if not name or not isinstance(body, dict):
            raise GamingError('Restore your player before continuing.', 'username_required', 409)
        action, action_id, round_id, step = (body.get(k) for k in ('action', 'action_id', 'round_id', 'step'))
        if (action not in ('hit', 'stand', 'double') or type(step) is not int or not 0 <= step <= 32 or
                any(not isinstance(v, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', v) for v in (action_id, round_id))):
            raise GamingError('Send a valid Blackjack move.')
        now = time.time() if now is None else now
        with self.store.connection(transaction=True) as conn:
            player, current = self._player(conn, identity, name, now)
            done = next((r for r in player['receipts'] if r['request_id'] == round_id and r['game']=='blackjack'), None)
            if done:
                issue = self._ip_issue(conn['gaming'], player_key(identity), client_ip, current)
                return dict(ok=True, duplicate=True, receipt=copy.deepcopy(done), wallet=self._view(player, current, issue))
            self._claim_ip(conn['gaming'], player_key(identity), client_ip, current)
            receipt = player.get('blackjack')
            if not receipt or receipt['request_id'] != round_id:
                raise GamingError('This hand is no longer active. Reload your saved result.', 'stale_hand', 409)
            if action_id in receipt['action_ids']:
                return dict(ok=True, duplicate=True, receipt=None, wallet=self._view(player, current))
            if step != len(receipt['actions']):
                raise GamingError('Another tab played a move. Your saved hand has been updated.', 'stale_hand', 409)
            if action == 'double' and player['balance'] < receipt['wager']:
                raise GamingError('Not enough RedPoints to double. Hit or Stand.', 'balance', 409)
            receipt['actions'].append(action)
            receipt['action_ids'].append(action_id)
            result = outcome(player['server_seed'], receipt)  # Illegal moves roll back.
            if action == 'double':
                player['balance'] -= receipt['wager']
            if result['ended']:
                self._settle(player, receipt, result)
                return dict(ok=True, duplicate=False, receipt=copy.deepcopy(receipt), wallet=self._view(player, current))
            player['version'] += 1
            return dict(ok=True, duplicate=False, receipt=None, wallet=self._view(player, current))

    def leaders(self, now=None):
        """Private rankings from settled ledger totals, never client-reported wins."""
        current = season(now)
        with self.store.connection() as conn:
            data = conn.get('gaming') or {}
            players = data.get('players', {})
            guard = data.get('ip_guard') or {}
            networks = {}
            if guard.get('season') == current['id']:
                for digest, key in guard['claims'].items():
                    address = guard.get('addresses', {}).get(digest)
                    if address:
                        networks.setdefault(key, []).append(address)
            result, counts = {}, {}
            active = {key:p for key,p in players.items() if p['season']==current['id']}
            for game in GAMES:
                rows = [dict(name=p['name'], player_tag=key[:12], ips=sorted(networks.get(key, [])),
                             balance=p['balance'], **p['stats'][game]) for key,p in active.items() if p['stats'][game]['bets']]
                rows.sort(key=lambda p:(-p['net'], -p['paid'], p['player_tag']))
                # Count the complete ledger before slicing the five leaders.
                counts[game] = dict(players=len(rows), rounds=sum(row['bets'] for row in rows))
                result[game] = rows[:5]
            return dict(season=current, games=result, counts=counts, completed_rounds=sum(c['rounds'] for c in counts.values()),
                        revision=sum(p['version'] for p in active.values()), player_count=len(active),
                        ip_count=sum(map(len, networks.values())), active_hands=sum(bool(p.get('blackjack')) for p in active.values()))

    def recovery(self):
        with self.store.connection() as conn:
            return copy.deepcopy(conn.get('gaming'))
