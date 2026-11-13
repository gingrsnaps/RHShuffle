"""Shared play-point wallets. All debits, outcomes, receipts and ranks commit once.

Uses the existing JSON transaction and signed browser identity. IPs are admin-only metadata. No money, SQL,
Botrix balance integration, daily wager cap, or separate launch process.
"""
import copy
import hashlib
import hmac
import ipaddress
import logging
import re
import secrets
import threading
import time

from fairness import VERSION, BLACKJACK_VERSIONS, POKER_VERSIONS, GAMES, commitment, options_for, outcome, max_payout
from weekly_history import completed_weeks

LOG = logging.getLogger('redhunllef')
START_POINTS = 100000
MAX_NUMBER = 2**53-1
MAX_PLAYERS = 10000
RECEIPTS = 30
MAX_IP_BINDINGS = MAX_PLAYERS * 4
MAX_GRANTS = 100
PUBLIC_LIVE_SECONDS = 120
PUBLIC_NOW_SECONDS = 30
PUBLIC_LEADER_LIMIT = 10
PUBLIC_LIVE_LIMIT = 20


class GamingError(ValueError):
    def __init__(self, message, code='invalid_bet', status=422):
        super().__init__(message)
        self.code, self.status = code, status


def player_name(value):
    """Validate a public Gaming name without depending on the removed Boss module."""
    if not isinstance(value, str):
        raise GamingError('Enter a name of 1–64 printable characters.', 'invalid_name', 422)
    value = value.strip()
    if not 1 <= len(value) <= 64 or not value.isprintable():
        raise GamingError('Enter a name of 1–64 printable characters.', 'invalid_name', 422)
    return value


def migrate_legacy_profiles(gaming, legacy_profiles):
    """Copy recoverable profile metadata when a unique name safely matches.

    The retired profile system and Gaming used different one-way identity hashes, so a profile
    cannot be linked to a wallet by hash. Existing Gaming wallet names/balances are
    already authoritative. A unique exact name match can safely preserve the old
    recovery digest; ambiguous names are deliberately ignored.
    """
    if not isinstance(gaming, dict) or not isinstance(legacy_profiles, dict):
        return 0
    players = gaming.get('players')
    profiles = legacy_profiles.get('profiles')
    if not isinstance(players, dict) or not isinstance(profiles, dict):
        return 0
    by_name = {}
    ambiguous = set()
    for profile in profiles.values():
        if not isinstance(profile, dict):
            continue
        name = profile.get('name')
        digest = profile.get('recovery_hash')
        if not isinstance(name, str) or not isinstance(digest, str) or not re.fullmatch(r'[a-f0-9]{64}', digest):
            continue
        key = name.casefold()
        if key in by_name:
            ambiguous.add(key)
        else:
            by_name[key] = profile
    migrated = 0
    for player in players.values():
        key = str(player.get('name', '')).casefold()
        profile = by_name.get(key)
        if not profile or key in ambiguous or player.get('recovery_hash'):
            continue
        player['recovery_hash'] = profile['recovery_hash']
        player['recovery_at'] = profile.get('recovery_at', 0)
        migrated += 1
    return migrated


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
    # Index connections by a stable digest. Canonical addresses are stored separately
    # for the private admin view, never in public wallet responses or bet logs.
    return hmac.new(bytes.fromhex(guard['salt']), canonical_ip(address).encode('ascii'), hashlib.sha256).hexdigest()


def fresh_stats():
    return {game:dict(bets=0, wagered=0, paid=0, net=0, biggest_payout=0) for game in GAMES}


def is_holdem(hand):
    return bool(hand and hand.get('options', {}).get('variant') == 'texas_holdem')


def upgrade_poker_stats(player):
    # One-way, explicit migration: old 'poker' winnings were Video Poker.
    # Keep proof IDs/options untouched; their original HMAC context is immutable.
    if player.get('poker_stats_version', 1) == 1:
        legacy = player['stats'].pop('poker', None)
        if legacy is not None:
            player['stats']['video_poker'] = legacy
        player['poker_stats_version'] = 2
    player['stats'].setdefault('poker', fresh_stats()['poker'])


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
        if type(player.get('community_name_confirmed', False)) is not bool:
            raise ValueError('Invalid community-name confirmation.')
        if type(player.get('public_visibility', False)) is not bool:
            raise ValueError('Invalid public Gaming visibility.')
        last_game = player.get('last_game', '')
        if not isinstance(last_game, str) or (last_game and last_game not in GAMES):
            raise ValueError('Invalid recent Gaming activity.')
        for field in ('last_action_at', 'last_round_at'):
            value_at = player.get(field, 0)
            if type(value_at) not in (int, float) or not 0 <= value_at <= 10**12:
                raise ValueError('Invalid recent Gaming timestamp.')
        recovery_hash = player.get('recovery_hash')
        if recovery_hash is not None and (not isinstance(recovery_hash, str) or not re.fullmatch(r'[a-f0-9]{64}', recovery_hash)):
            raise ValueError('Invalid Gaming recovery digest.')
        recovery_at = player.get('recovery_at', 0)
        if type(recovery_at) not in (int, float) or not 0 <= recovery_at <= 10**12:
            raise ValueError('Invalid Gaming recovery timestamp.')
        if not isinstance(player.get('season'), str) or not re.fullmatch(r'\d{1,12}', player['season']):
            raise ValueError('Invalid RedPoints season.')
        if not isinstance(player.get('server_seed'), str) or not re.fullmatch(r'[a-f0-9]{64}', player['server_seed']):
            raise ValueError('Invalid RedPoints fairness seed.')
        for name in ('balance', 'nonce', 'version'):
            if type(player.get(name)) is not int or not 0 <= player[name] <= MAX_NUMBER:
                raise ValueError('Invalid RedPoints wallet counter.')
        if not {'dice', 'keno', 'plinko'} <= set(player.get('stats', {})) <= set(GAMES) | {'video_poker'}:
            raise ValueError('Invalid RedPoints game statistics.')
        if player.get('poker_stats_version', 1) not in (1, 2):
            raise ValueError('Invalid Poker statistics version.')
        if 'video_poker' in player['stats'] and player.get('poker_stats_version') != 2:
            raise ValueError('Video Poker records need their migration marker.')
        for stats in player['stats'].values():
            for name in ('bets','wagered','paid','biggest_payout'):
                if type(stats.get(name)) is not int or not 0 <= stats[name] <= MAX_NUMBER:
                    raise ValueError('Invalid RedPoints winnings.')
            if stats.get('net') != stats['paid']-stats['wagered']:
                raise ValueError('RedPoints winnings do not balance.')
        if player.get('blackjack') is not None and player.get('poker') is not None:
            raise ValueError('A wallet cannot reserve two card hands at once.')
        reserved = 0
        for game in ('blackjack', 'poker'):
            pending = player.get(game)
            if pending is None:
                continue
            try:
                allowed = BLACKJACK_VERSIONS if game == 'blackjack' else POKER_VERSIONS
                if (pending['game'] != game or pending['rules_version'] not in allowed or
                        pending['nonce'] != player['nonce'] or pending['server_seed'] != player['server_seed'] or
                        pending['commitment'] != commitment(player['server_seed']) or pending['season'] != player['season'] or
                        type(pending['wager']) is not int or not 1 <= pending['wager'] <= MAX_NUMBER or
                        not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', pending['request_id']) or
                        not re.fullmatch(r'[a-f0-9]{32}', pending['client_salt']) or
                        not re.fullmatch(r'[A-Za-z0-9 _.-]{1,64}', pending['client_seed']) or
                        options_for(game, pending['options']) != pending['options']):
                    raise ValueError('Invalid reserved hand')
                if game == 'blackjack' or is_holdem(pending):
                    if (len(pending['action_ids']) != len(pending['actions']) or
                            len(set(pending['action_ids'])) != len(pending['action_ids']) or
                            any(not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', item) for item in pending['action_ids'])):
                        raise ValueError('Invalid saved card moves')
                elif pending.get('holds') is not None or 'draw_id' in pending:
                    raise ValueError('A drawn Poker hand must already be settled')
                if outcome(player['server_seed'], pending)['ended']:
                    raise ValueError('A completed hand cannot remain reserved')
                reserved = pending['wager']
            except (KeyError, TypeError, ValueError):
                raise ValueError('Invalid saved card hand.') from None
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
    activity_revision = value.get('activity_revision', 0)
    if type(activity_revision) is not int or not 0 <= activity_revision <= MAX_NUMBER:
        raise ValueError('Invalid public Gaming activity revision.')
    grants = value.get('admin_grants', [])
    if not isinstance(grants, list) or len(grants) > MAX_GRANTS:
        raise ValueError('Invalid RedPoints grant history.')
    grant_ids = set()
    for grant in grants:
        if (not isinstance(grant, dict) or not isinstance(grant.get('request_id'), str) or
                not re.fullmatch(r'[a-f0-9]{32}', grant['request_id']) or grant['request_id'] in grant_ids or
                not isinstance(grant.get('actor'), str) or not 1 <= len(grant['actor']) <= 64 or
                type(grant.get('amount')) is not int or grant['amount'] != START_POINTS or
                type(grant.get('players')) is not int or not 0 <= grant['players'] <= MAX_PLAYERS or
                type(grant.get('at')) is not int or not 0 <= grant['at'] <= MAX_NUMBER or
                not isinstance(grant.get('season'), str) or not re.fullmatch(r'\d{1,12}', grant['season'])):
            raise ValueError('Invalid RedPoints grant record.')
        grant_ids.add(grant['request_id'])
    guard = value.get('ip_guard')
    if guard is not None:
        if (not isinstance(guard, dict) or guard.get('version') not in (1, 2) or
                not isinstance(guard.get('salt'), str) or not re.fullmatch(r'[a-f0-9]{64}', guard['salt']) or
                not isinstance(guard.get('season'), str) or not re.fullmatch(r'\d{1,12}', guard['season']) or
                not isinstance(guard.get('claims'), dict) or len(guard['claims']) > MAX_IP_BINDINGS):
            raise ValueError('Invalid RedPoints IP bindings.')
        links = 0
        for address, owners in guard['claims'].items():
            owners = [owners] if guard['version'] == 1 else owners
            if (not isinstance(address, str) or not re.fullmatch(r'[a-f0-9]{64}', address) or
                    not isinstance(owners, list) or not owners or len(owners) > MAX_PLAYERS or
                    any(not isinstance(key, str) or key not in value['players'] for key in owners) or
                    len(set(owners)) != len(owners)):
                raise ValueError('Invalid RedPoints IP association.')
            links += len(owners)
        if links > MAX_IP_BINDINGS:
            raise ValueError('Too many saved RedPoints IP associations.')
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
        self._public_cache_lock = threading.RLock()
        self._public_cache_key = None
        self._public_cache_value = None
        self._public_cache_expires_at = 0
        with store.connection() as conn:
            validate_gaming(conn.get('gaming'))
        # Adding a game never resets an existing wallet, seed or receipt.
        # Public activity fields are additive and default private for existing
        # players until they explicitly opt in from the Gaming profile.
        with store.connection(transaction=True) as conn:
            if conn.get('gaming') is None:
                conn['gaming'] = dict(version=1, players={}, activity_revision=0)
            data = conn['gaming']
            data.setdefault('activity_revision', 0)
            for player in data.get('players', {}).values():
                upgrade_poker_stats(player)
                for game, stats in fresh_stats().items():
                    player['stats'].setdefault(game, stats)
                player.setdefault('public_visibility', False)
                player.setdefault('last_game', '')
                player.setdefault('last_action_at', 0)
                player.setdefault('last_round_at', 0)
            self._upgrade_networks(data.get('ip_guard'))

    def restart_balances(self, now=None):
        """Run once at server startup, never from a page or automatic poll.

        Restore the playable allowance without erasing names, results, seeds or
        unfinished hands. Normal weekly rollover still starts a fresh leaderboard.
        """
        current = season(now)
        restored = skipped = 0
        with self.store.connection(transaction=True) as conn:
            for player in (conn.get('gaming') or {}).get('players', {}).values():
                try:
                    self._rollover(player, current)
                    if player['balance'] != START_POINTS:
                        self._reset_allowance(player)
                    restored += 1
                except GamingError:
                    # An exceptional numeric/clock record must not take the
                    # entire community offline. Keep that record unchanged.
                    skipped += 1
        LOG.info('GAMING startup restored %s RedPoints for %s wallets; names and game records retained. Shared IPs are allowed.',
                 START_POINTS, restored)
        if skipped:
            LOG.warning('GAMING retained %s wallets unchanged due to their numeric range or future season.', skipped)
        return dict(restored=restored, skipped=skipped)

    @staticmethod
    def _reset_allowance(player):
        # This adjustment is funding, not winnings. Reserved Blackjack stakes
        # remain in the hand and are settled exactly once by the normal ledger.
        adjustment = player.get('balance_adjustment', 0) + START_POINTS - player['balance']
        hand = player.get('blackjack') or player.get('poker')
        room = max_payout(hand['game'], hand['wager'], hand['options']) if hand else 0
        if START_POINTS+room > MAX_NUMBER or abs(adjustment) > MAX_NUMBER or player['version'] >= MAX_NUMBER:
            raise GamingError('This wallet reached its supported numeric range.', 'capacity', 409)
        player.update(balance=START_POINTS, balance_adjustment=adjustment, version=player['version']+1)

    def _player(self, conn, identity, name, now):
        current = season(now)
        if conn.get('gaming') is None:
            conn['gaming'] = dict(version=1, players={}, activity_revision=0)
        conn['gaming'].setdefault('activity_revision', 0)
        players = conn['gaming']['players']
        key = player_key(identity)
        if key not in players:
            if len(players) >= MAX_PLAYERS:
                raise GamingError('The player registry is full. Contact the host.', 'capacity', 409)
            players[key] = dict(name=name, season=current['id'], balance=START_POINTS, stats=fresh_stats(),
                                nonce=0, version=1, poker_stats_version=2, server_seed=secrets.token_hex(32),
                                receipts=[], last_bet_at=0, public_visibility=False, last_game='',
                                last_action_at=0, last_round_at=0)
        player = players[key]
        upgrade_poker_stats(player)
        for game, stats in fresh_stats().items():
            player['stats'].setdefault(game, stats)
        self._rollover(player, current)
        if player['name'] != name:
            player['name'] = name
            player['version'] += 1
        return player, current

    @staticmethod
    def _touch_activity(data, player, game, now, *, round_completed=False):
        """Record only server-confirmed game actions for the public activity feed.

        Page views and five-second wallet polls never call this helper, so they
        cannot make a visitor appear to be actively playing.
        """
        if game not in GAMES:
            return
        stamp = int(now)
        player['last_game'] = game
        player['last_action_at'] = stamp
        if round_completed:
            player['last_round_at'] = stamp
        data['activity_revision'] = min(MAX_NUMBER, int(data.get('activity_revision', 0)) + 1)

    @staticmethod
    def _rollover(player, current):
        """Reuse the same weekly accounting for player visits and bulk grants."""
        if int(player['season']) > int(current['id']):
            raise GamingError('The server clock moved backwards. The saved wallet is protected.', 'clock', 409)
        if player['season'] != current['id']:
            hand = player.get('blackjack') or player.get('poker')
            if hand:
                if hand['game'] == 'blackjack':
                    hand['actions'].append('stand')
                elif is_holdem(hand):
                    # Fold the saved hand at the boundary; do not wager more.
                    pass
                else:
                    # A week boundary keeps all five initial cards, then settles
                    # under the old week before the new allowance is created.
                    hand.update(holds=list(range(5)), draw_id='weekly-reset')
                hand['ending'] = 'weekly_reset'
                Gaming._settle(player, hand, outcome(player['server_seed'], hand))
            player.update(season=current['id'], balance=START_POINTS, balance_adjustment=0,
                          stats=fresh_stats(), version=player['version']+1)

    @staticmethod
    def _upgrade_networks(guard):
        """Turn old exclusive claims into many-player associations, in place."""
        if guard and guard['version'] == 1:
            guard['claims'] = {digest: [owner] for digest, owner in guard['claims'].items()}
            guard['version'] = 2

    @staticmethod
    def _needs_network_record(data, key, address, current):
        """Missing/full tracking data never affects eligibility to play."""
        try:
            address = canonical_ip(address)
        except ValueError:
            return False
        guard = (data or {}).get('ip_guard')
        if not guard or int(guard['season']) < int(current['id']):
            return True
        if int(guard['season']) > int(current['id']):
            return False
        digest = ip_key(guard, address)
        owners = guard['claims'].get(digest, [])
        if isinstance(owners, str):
            owners = [owners]  # Recovery imports may still contain the old format.
        if key in owners:
            return digest not in guard.get('addresses', {})
        links = sum(1 if isinstance(items, str) else len(items) for items in guard['claims'].values())
        return links < MAX_IP_BINDINGS

    def _record_ip(self, data, key, address, current):
        # A household, VPN, mobile carrier or proxy can represent many people.
        # Only the signed browser/recovery identity owns a wallet, never an IP.
        if not self._needs_network_record(data, key, address, current):
            return
        guard = data.get('ip_guard')
        if guard is None:
            guard = data['ip_guard'] = dict(version=2, salt=secrets.token_hex(32), season=current['id'], claims={}, addresses={})
        self._upgrade_networks(guard)
        if guard['season'] != current['id']:
            guard.update(season=current['id'], claims={}, addresses={})
        digest = ip_key(guard, address)
        owners = guard['claims'].setdefault(digest, [])
        if key not in owners:
            owners.append(key)
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
    def _poker_view(player):
        hand = player.get('poker')
        if not hand:
            return None
        value = outcome(player['server_seed'], hand)
        value.update(round_id=hand['request_id'], wager=hand['wager'], step=len(hand.get('actions', [])),
                     bet={k:v for k,v in hand.items() if k not in {'server_seed', 'holds', 'actions', 'action_ids'}})
        return value

    @staticmethod
    def _view(player, current):
        return dict(season=current, name=player['name'], balance=player['balance'], nonce=player['nonce'],
                    version=player['version'], commitment=commitment(player['server_seed']),
                    stats={game:copy.deepcopy(player['stats'].get(game, stats)) for game, stats in fresh_stats().items()},
                    legacy_poker=copy.deepcopy(player['stats'].get('video_poker')),
                    poker_button='player' if player['stats'].get('poker', {}).get('bets', 0) % 2 == 0 else 'computer',
                    receipts=copy.deepcopy(player['receipts']),
                    needs_profile=not player.get('community_name_confirmed', False),
                    public_visibility=bool(player.get('public_visibility', False)),
                    rules_version=VERSION, ip_bound=False, play_blocked=None,
                    blackjack=Gaming._hand_view(player), poker=Gaming._poker_view(player))

    def view(self, identity, name, now=None, *, client_ip=None):
        now = time.time() if now is None else now
        current = season(now)
        key = player_key(identity)
        def preview():
            return dict(season=current, balance=START_POINTS, name=name or '', nonce=0, version=0,
                        commitment='', stats=fresh_stats(), receipts=[], needs_profile=True, public_visibility=False,
                        rules_version=VERSION, ip_bound=False, play_blocked=None, blackjack=None, poker=None,
                        poker_button='player', legacy_poker=None)
        # Routine five-second reads neither copy the complete community save nor
        # rewrite it. Connection metadata is recorded only when it changes.
        with self.store.connection() as conn:
            data = conn.get('gaming') or {}
            player = data.get('players', {}).get(key)
            if player:
                # The wallet owns its name. No retired profile lookup is required.
                name = player['name']
                if player.get('poker_stats_version') == 2 and player['season'] == current['id']:
                    if not self._needs_network_record(data, key, client_ip, current):
                        return self._view(player, current)
            elif not name:
                return preview()
        with self.store.connection(transaction=True) as conn:
            player, current = self._player(conn, identity, name, now)
            self._record_ip(conn['gaming'], key, client_ip, current)
            return self._view(player, current)

    def confirm_community_name(self, identity, name, public_visibility=None, now=None, *, client_ip=None):
        """Activate the shared wallet once, retaining wins, receipts and its owner.

        Names migrated from the retired profile system remain suggestions until confirmed on Gaming. Older
        empty wallets receive the starting allowance here; re-saving a confirmed
        name does not grant more points or erase larger balances/admin credits.
        """
        name = player_name(name)
        now = time.time() if now is None else now
        if public_visibility is not None and type(public_visibility) is not bool:
            raise GamingError('Choose whether your Gaming name appears publicly.', 'invalid_visibility', 422)
        with self.store.connection(transaction=True) as conn:
            if conn.get('gaming') is None:
                conn['gaming'] = dict(version=1, players={}, activity_revision=0)
            data = conn['gaming']
            data.setdefault('activity_revision', 0)
            before_name = (data.get('players', {}).get(player_key(identity)) or {}).get('name')
            before_visibility = (data.get('players', {}).get(player_key(identity)) or {}).get('public_visibility', False)
            player, current = self._player(conn, identity, name, now)
            self._record_ip(data, player_key(identity), client_ip, current)
            if not player.get('community_name_confirmed', False):
                extra = max(0, START_POINTS - player['balance'])
                adjustment = player.get('balance_adjustment', 0) + extra
                if abs(adjustment) > MAX_NUMBER or player['version'] >= MAX_NUMBER:
                    raise GamingError('This wallet reached its supported numeric range.', 'capacity', 409)
                player.update(community_name_confirmed=True, balance=player['balance']+extra,
                              balance_adjustment=adjustment, version=player['version']+1)
            if public_visibility is not None and player.get('public_visibility', False) != public_visibility:
                player['public_visibility'] = public_visibility
                player['version'] += 1
            if before_name != player['name'] or before_visibility != player.get('public_visibility', False):
                data['activity_revision'] = min(MAX_NUMBER, int(data.get('activity_revision', 0)) + 1)
            return self._view(player, current)

    def save_recovery(self, identity, code_hash, now=None):
        """Attach a replaceable recovery digest to this signed Gaming wallet."""
        if not isinstance(code_hash, str) or not re.fullmatch(r'[a-f0-9]{64}', code_hash):
            raise GamingError('Invalid recovery code.', 'invalid_recovery', 422)
        now = time.time() if now is None else now
        with self.store.connection(transaction=True) as conn:
            player = (conn.get('gaming') or {}).get('players', {}).get(player_key(identity))
            if not player or not player.get('community_name_confirmed'):
                raise GamingError('Save your Gaming name before creating a recovery code.', 'profile_required', 409)
            if now - player.get('recovery_at', 0) < 30:
                raise GamingError('Wait 30 seconds before replacing your recovery code.', 'profile_cooldown', 429)
            player['recovery_hash'] = code_hash
            player['recovery_at'] = now
            player['version'] += 1
            return self._view(player, season(now))

    def recover(self, identity, code_hash, now=None, *, client_ip=None):
        """Validate a recovery digest and return the wallet owned by identity."""
        if not isinstance(code_hash, str) or not re.fullmatch(r'[a-f0-9]{64}', code_hash):
            raise GamingError('That recovery code is invalid or was replaced.', 'invalid_recovery', 400)
        now = time.time() if now is None else now
        key = player_key(identity)
        with self.store.connection(transaction=True) as conn:
            data = conn.get('gaming') or {}
            player = data.get('players', {}).get(key)
            if not player or not hmac.compare_digest(str(player.get('recovery_hash', '')), code_hash):
                raise GamingError('That recovery code is invalid or was replaced.', 'invalid_recovery', 400)
            current = season(now)
            self._rollover(player, current)
            self._record_ip(data, key, client_ip, current)
            return self._view(player, current)

    def grant_everyone(self, request_id, actor, now=None):
        """Add 100k per saved wallet in one atomic write; retries cannot double it.

        HTTP authentication/CSRF is enforced by the admin route. Credits are
        separate from game profit, so Top 5 and fairness receipts stay accurate.
        """
        if (not isinstance(request_id, str) or not re.fullmatch(r'[a-f0-9]{32}', request_id) or
                not isinstance(actor, str) or not 1 <= len(actor) <= 64):
            raise GamingError('Reload the admin panel before granting points.', 'invalid_grant', 422)
        now = time.time() if now is None else now
        current = season(now)
        with self.store.connection(transaction=True) as conn:
            if conn.get('gaming') is None:
                conn['gaming'] = dict(version=1, players={})
            data = conn['gaming']
            history = data.setdefault('admin_grants', [])
            prior = next((item for item in history if item['request_id'] == request_id), None)
            if prior:
                return dict(duplicate=True, **copy.deepcopy(prior))
            for player in data['players'].values():
                self._rollover(player, current)
                adjustment = player.get('balance_adjustment', 0) + START_POINTS
                # Reserve room for the largest return on an unfinished card hand.
                hand = player.get('blackjack') or player.get('poker')
                room = max_payout(hand['game'], hand['wager'], hand['options']) if hand else 0
                if (player['balance'] + START_POINTS + room > MAX_NUMBER or
                        abs(adjustment) > MAX_NUMBER or player['version'] >= MAX_NUMBER):
                    raise GamingError('A wallet reached the numeric limit. No points were granted.', 'capacity', 409)
                player.update(balance=player['balance']+START_POINTS, balance_adjustment=adjustment,
                              version=player['version']+1)
            record = dict(request_id=request_id, actor=actor, amount=START_POINTS,
                          players=len(data['players']), at=int(now), season=current['id'])
            data['admin_grants'] = [record] + history[:MAX_GRANTS-1]
        LOG.info('GAMING Admin %r granted +%s RedPoints to %s wallets; game winnings unchanged.',
                 actor, START_POINTS, record['players'])
        return dict(duplicate=False, **record)

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
            self._record_ip(conn['gaming'], player_key(identity), client_ip, current)
            if body['season'] != current['id']:
                # The weekly rollover already supplies the new allowance.
                return dict(ok=True, wallet=self._view(player, current))
            if body['version'] != player['version']:
                raise GamingError('Your balance changed in another request. Reload to refresh the latest wallet.',
                                  'stale_wallet', 409)
            self._reset_allowance(player)
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
                return dict(ok=True, duplicate=True, receipt=copy.deepcopy(duplicate), wallet=self._view(player, current))
            # Old receipts remain recoverable; new wagers use the current rules.
            if body.get('rules_version') != VERSION:
                raise GamingError('Game rules changed. Reload before placing another wager.', 'release_mismatch', 409)
            self._record_ip(conn['gaming'], player_key(identity), client_ip, current)
            active = player.get('blackjack') or player.get('poker')
            if active:
                if active['request_id'] == request_id:
                    return dict(ok=True, duplicate=True, receipt=None, wallet=self._view(player, current))
                raise GamingError('Finish your '+active['game'].capitalize()+' hand before starting another game.', 'active_hand', 409)
            if body.get('season') != current['id']:
                raise GamingError('A new wager-race week started. Refresh to use your new 100,000 RedPoints.', 'new_season', 409)
            if nonce != player['nonce'] or body.get('commitment') != commitment(player['server_seed']):
                raise GamingError('Another tab used this seed. Refresh your balance and fairness details.', 'stale_seed', 409)
            if wager > player['balance']:
                raise GamingError('Not enough RedPoints. Lower the wager or refresh the page for 100,000 RedPoints.', 'balance', 409)
            if game == 'poker':
                button = 'player' if player['stats']['poker']['bets'] % 2 == 0 else 'computer'
                if opt != dict(variant='texas_holdem', button=button):
                    raise GamingError('The dealer button changed. Reload the saved table.', 'stale_hand', 409)
            largest = max_payout(game, wager, opt)
            stats = player['stats'][game]
            if max(player['balance']-wager+largest, stats['paid']+largest, stats['wagered']+wager*(2 if game=='blackjack' else 1),
                   player['nonce']+1, player['version']+1) > MAX_NUMBER:
                raise GamingError('This wallet reached its supported numeric range.', 'capacity', 409)
            receipt = dict(rules_version=VERSION, season=current['id'], request_id=request_id, game=game,
                           client_seed=client, client_salt=salt, nonce=nonce, wager=wager, options=opt,
                           commitment=commitment(player['server_seed']), server_seed=player['server_seed'], at=int(now))
            if game == 'blackjack':
                receipt.update(actions=[], action_ids=[])
            elif game == 'poker':
                receipt.update(actions=[], action_ids=[])
            result = outcome(player['server_seed'], receipt)
            player['balance'] -= wager
            if game in ('blackjack', 'poker') and not result['ended']:
                player[game] = receipt
                player['version'] += 1
                self._touch_activity(conn['gaming'], player, game, now, round_completed=False)
                return dict(ok=True, duplicate=False, receipt=None, wallet=self._view(player, current))
            self._settle(player, receipt, result)
            self._touch_activity(conn['gaming'], player, game, now, round_completed=True)
            return dict(ok=True, duplicate=False, receipt=copy.deepcopy(receipt), wallet=self._view(player, current))

    @staticmethod
    def _settle(player, receipt, result):
        """Credit once after the complete stake has been reserved in this transaction."""
        wager = result['total_wager'] if receipt['game'] == 'blackjack' else receipt['wager']
        payout, net = result['payout'], result['payout']-wager
        player.update(balance=player['balance']+payout, nonce=player['nonce']+1,
                      server_seed=secrets.token_hex(32), version=player['version']+1, last_bet_at=receipt['at'])
        player.pop('blackjack', None)
        player.pop('poker', None)
        receipt.update(result=result, payout=payout, net=net, balance_after=player['balance'],
                       next_commitment=commitment(player['server_seed']))
        stat_game = 'video_poker' if receipt['game'] == 'poker' and not is_holdem(receipt) else receipt['game']
        stats = player['stats'].setdefault(stat_game, dict(bets=0, wagered=0, paid=0, net=0, biggest_payout=0))
        # Hold’em credits the entire remaining table stack to the wallet, but
        # only contested chips and pot awards belong in gambling statistics.
        if is_holdem(receipt):
            wager, payout = result['total_wager'], result['returned']
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
                return dict(ok=True, duplicate=True, receipt=copy.deepcopy(done), wallet=self._view(player, current))
            self._record_ip(conn['gaming'], player_key(identity), client_ip, current)
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
                self._touch_activity(conn['gaming'], player, 'blackjack', now, round_completed=True)
                return dict(ok=True, duplicate=False, receipt=copy.deepcopy(receipt), wallet=self._view(player, current))
            player['version'] += 1
            self._touch_activity(conn['gaming'], player, 'blackjack', now, round_completed=False)
            return dict(ok=True, duplicate=False, receipt=None, wallet=self._view(player, current))

    def poker_action(self, identity, name, body, now=None, *, client_ip=None):
        """Commit one hold/draw decision and settle it atomically, once."""
        if isinstance(body, dict) and body.get('variant') == 'texas_holdem':
            return self.holdem_action(identity, name, body, now, client_ip=client_ip)
        from poker import validate_holds
        if not name or not isinstance(body, dict):
            raise GamingError('Restore your player before drawing cards.', 'username_required', 409)
        holds = validate_holds(body.get('holds'))
        action_id, round_id = body.get('action_id'), body.get('round_id')
        if any(not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', value) for value in (action_id, round_id)):
            raise GamingError('Send a valid Poker draw.')
        now = time.time() if now is None else now
        with self.store.connection(transaction=True) as conn:
            player, current = self._player(conn, identity, name, now)
            done = next((r for r in player['receipts'] if r['request_id'] == round_id and r['game'] == 'poker'), None)
            if done:
                if is_holdem(done):
                    raise GamingError('This is a saved Hold’em result.', 'stale_hand', 409)
                if done.get('draw_id') != action_id or done['holds'] != holds:
                    raise GamingError('This hand was already drawn. Its saved result has been kept.', 'stale_hand', 409)
                return dict(ok=True, duplicate=True, receipt=copy.deepcopy(done), wallet=self._view(player, current))
            self._record_ip(conn['gaming'], player_key(identity), client_ip, current)
            hand = player.get('poker')
            if not hand or hand['request_id'] != round_id:
                raise GamingError('This Poker hand is no longer active. Reload your saved result.', 'stale_hand', 409)
            if is_holdem(hand):
                raise GamingError('Use the Hold’em action controls.', 'stale_hand', 409)
            hand.update(holds=holds, draw_id=action_id)
            self._settle(player, hand, outcome(player['server_seed'], hand))
            self._touch_activity(conn['gaming'], player, 'poker', now, round_completed=True)
            return dict(ok=True, duplicate=False, receipt=copy.deepcopy(hand), wallet=self._view(player, current))

    def holdem_action(self, identity, name, body, now=None, *, client_ip=None):
        """Replay a saved hand and commit one player decision exactly once."""
        from holdem import validate_action
        if not name or not isinstance(body, dict):
            raise GamingError('Restore your player before continuing.', 'username_required', 409)
        move = validate_action(body.get('move'))
        action_id, round_id, step = (body.get(k) for k in ('action_id', 'round_id', 'step'))
        if (type(step) is not int or not 0 <= step < 4096 or
                any(not isinstance(v, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,64}', v) for v in (action_id, round_id))):
            raise GamingError('Send a valid Hold’em move.')
        now = time.time() if now is None else now
        with self.store.connection(transaction=True) as conn:
            player, current = self._player(conn, identity, name, now)
            done = next((r for r in player['receipts'] if r['request_id'] == round_id and is_holdem(r)), None)
            hand = done or player.get('poker')
            if not is_holdem(hand) or hand['request_id'] != round_id:
                raise GamingError('This Hold’em hand is no longer active. Reload its saved result.', 'stale_hand', 409)
            # Reusing an ID with a different move is not an idempotent retry.
            if action_id in hand['action_ids']:
                index = hand['action_ids'].index(action_id)
                if index != step or hand['actions'][index] != move:
                    raise GamingError('That move ID already has a different decision.', 'stale_hand', 409)
                return dict(ok=True, duplicate=True, receipt=copy.deepcopy(done), wallet=self._view(player, current))
            if done or step != len(hand['actions']):
                raise GamingError('Another tab moved. Your saved table has been updated.', 'stale_hand', 409)
            self._record_ip(conn['gaming'], player_key(identity), client_ip, current)
            hand['actions'].append(move)
            hand['action_ids'].append(action_id)
            result = outcome(player['server_seed'], hand)  # Illegal actions roll back the transaction.
            if result['ended']:
                self._settle(player, hand, result)
                self._touch_activity(conn['gaming'], player, 'poker', now, round_completed=True)
                return dict(ok=True, duplicate=False, receipt=copy.deepcopy(hand), wallet=self._view(player, current))
            player['version'] += 1
            self._touch_activity(conn['gaming'], player, 'poker', now, round_completed=False)
            return dict(ok=True, duplicate=False, receipt=None, wallet=self._view(player, current))

    @staticmethod
    def _game_label(game):
        return {
            'poker': "Texas Hold’em",
            'video_poker': 'Video Poker',
            'coinflip': 'Coinflip',
        }.get(game, game.capitalize())

    def public_leaderboard(self, now=None):
        """Return a compact, privacy-safe five-second Gaming community feed.

        The projection contains no wallet IDs, IP addresses, balances, recovery
        data, seeds, receipts or funding adjustments. Rankings use settled
        server-side ledger statistics only. Page views and polling never create
        activity; only confirmed game actions call ``_touch_activity``.
        """
        now = time.time() if now is None else now
        current = season(now)
        with self.store.connection() as conn:
            data = conn.get('gaming') or {}
            revision = int(data.get('activity_revision', 0))
            cache_key = (current['id'], revision)
            with self._public_cache_lock:
                if (cache_key == self._public_cache_key and self._public_cache_value is not None and
                        now < self._public_cache_expires_at):
                    return copy.deepcopy(self._public_cache_value)
            players = data.get('players', {})
            game_counts = {game: 0 for game in GAMES}
            live = []
            next_change = None
            leaders = []
            per_game = {game: [] for game in GAMES}
            for player in players.values():
                if player.get('season') != current['id'] or not player.get('community_name_confirmed'):
                    continue
                stats = player.get('stats') or {}
                net = rounds = 0
                visible = bool(player.get('public_visibility', False))
                for game in GAMES:
                    record = stats.get(game) or {}
                    game_net = int(record.get('net', 0))
                    game_rounds = int(record.get('bets', 0))
                    net += game_net
                    rounds += game_rounds
                    if visible and game_rounds:
                        per_game[game].append(dict(name=player['name'], net=game_net, rounds=game_rounds))
                legacy = stats.get('video_poker') or {}
                net += int(legacy.get('net', 0))
                rounds += int(legacy.get('bets', 0))
                if visible and rounds:
                    leaders.append(dict(name=player['name'], net=net, rounds=rounds))
                last_action = float(player.get('last_action_at', 0) or 0)
                age = max(0, now - last_action) if last_action else PUBLIC_LIVE_SECONDS + 1
                recent_game = 'blackjack' if player.get('blackjack') else 'poker' if player.get('poker') else player.get('last_game', '')
                if last_action and age <= PUBLIC_LIVE_SECONDS and recent_game in GAMES:
                    game_counts[recent_game] += 1
                    transition = (last_action + PUBLIC_NOW_SECONDS
                                  if age <= PUBLIC_NOW_SECONDS and not (player.get('blackjack') or player.get('poker'))
                                  else last_action + PUBLIC_LIVE_SECONDS)
                    if transition > now:
                        next_change = transition if next_change is None else min(next_change, transition)
                    if visible:
                        status = 'In a hand' if player.get('blackjack') or player.get('poker') else ('Playing now' if age <= PUBLIC_NOW_SECONDS else 'Recently active')
                        live.append(dict(name=player['name'], game=recent_game, game_label=self._game_label(recent_game),
                                         status=status, last_action_at=int(last_action)))

            def ranked(rows):
                rows.sort(key=lambda row: (-row['net'], -row['rounds'], row['name'].casefold()))
                result = rows[:PUBLIC_LEADER_LIMIT]
                for index, row in enumerate(result, 1):
                    row['rank'] = index
                return result

            leaders = ranked(leaders)
            game_leaders = {game: ranked(rows) for game, rows in per_game.items()}
            live.sort(key=lambda row: (-row['last_action_at'], row['name'].casefold()))
            value = dict(
                generated_at=int(now), season=current, revision=revision,
                live_players=live[:PUBLIC_LIVE_LIMIT], weekly_leaders=leaders,
                game_leaders=game_leaders,
                game_counts={game: count for game, count in game_counts.items() if count},
                active_count=sum(game_counts.values()),
            )
            with self._public_cache_lock:
                self._public_cache_key = cache_key
                self._public_cache_value = copy.deepcopy(value)
                self._public_cache_expires_at = next_change if next_change is not None else float('inf')
            return value

    def leaders(self, now=None):
        """Private rankings from settled ledger totals, never client-reported wins."""
        current = season(now)
        with self.store.connection() as conn:
            data = conn.get('gaming') or {}
            players = data.get('players', {})
            guard = data.get('ip_guard') or {}
            networks = {}
            if guard.get('season') == current['id']:
                for digest, owners in guard['claims'].items():
                    address = guard.get('addresses', {}).get(digest)
                    if address:
                        for key in ([owners] if isinstance(owners, str) else owners):
                            networks.setdefault(key, []).append(address)
            result, counts = {}, {}
            active = {key:p for key,p in players.items() if p['season']==current['id']}
            def game_stats(player, game):
                # A live recovery import may predate startup migration. Keep its
                # Video Poker rankings separate even before that player visits.
                if player.get('poker_stats_version', 1) == 1:
                    if game == 'poker': return {}
                    if game == 'video_poker': return player['stats'].get('poker', {})
                return player['stats'].get(game, {})
            for game in (*GAMES, 'video_poker'):
                rows = [dict(name=p['name'], player_tag=key[:12], ips=sorted(networks.get(key, [])),
                             balance=p['balance'], funding_adjustment=p.get('balance_adjustment', 0),
                             public_visibility=bool(p.get('public_visibility', False)),
                             last_game=p.get('last_game', ''), last_action_at=p.get('last_action_at', 0),
                             **game_stats(p, game)) for key,p in active.items() if game_stats(p, game).get('bets')]
                rows.sort(key=lambda p:(-p['net'], -p['paid'], p['player_tag']))
                # Count the complete ledger before slicing the five leaders.
                counts[game] = dict(players=len(rows), rounds=sum(row['bets'] for row in rows))
                result[game] = rows[:5]
            legacy = result.pop('video_poker')
            legacy_counts = counts.pop('video_poker')
            return dict(season=current, games=result, counts=counts, legacy_poker=legacy, legacy_poker_counts=legacy_counts,
                        completed_rounds=sum(c['rounds'] for c in counts.values())+legacy_counts['rounds'],
                        revision=sum(p['version'] for p in active.values()), player_count=len(active),
                        confirmed_players=sum(bool(p.get('community_name_confirmed')) for p in active.values()),
                        last_grant=copy.deepcopy((data.get('admin_grants') or [None])[0]),
                        ip_count=sum(map(len, networks.values())), active_hands=sum(bool(p.get('blackjack') or p.get('poker')) for p in active.values()))

    def recovery(self):
        with self.store.connection() as conn:
            return copy.deepcopy(conn.get('gaming'))
