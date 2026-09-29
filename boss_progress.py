"""Private community names and eight persistent, server-earned raid badges.

Names are self-reported, not verified Shuffle identities. Records are keyed by
salted browser/network hashes; raw addresses never enter the gameplay save.
"""
import copy
import re

DAY = 86400
MAX_NUMBER = 2**53 - 1  # Exact integer range shared by Python and browser JSON.
STYLES = ('blade', 'bow', 'magic')


def username(value):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= 64 or not value.isprintable():
        raise ValueError('Enter a username of 1–64 printable characters.')
    return value.strip()


def new_profile(name, network, now, player=None):
    old = player or {}
    return dict(name=username(name), network=network, named_at=now,
                attacks=old.get('attacks', 0), active_days=old.get('active_days', 1 if old else 0),
                first_hit_at=old.get('last_attack', 0), last_day=0 if old else -1, weak_hits=0, bursts=old.get('attacks', 0) // 10,
                styles={style: 0 for style in STYLES})


def record_hit(profile, hit, now):
    if not profile['first_hit_at']:
        profile['first_hit_at'] = now
    # Personal 24-hour periods prevent a midnight click from earning two days.
    day = int(max(0, now - profile['first_hit_at']) // DAY)
    if day > profile['last_day']:
        profile['active_days'] += 1
        profile['last_day'] = day
    profile['attacks'] += 1
    profile['weak_hits'] += int(hit['weakness'])
    profile['bursts'] += int(hit['burst'])
    profile['styles'][hit['style']] += 1


def badges(player, now=0):
    hits, days = player.get('attacks', 0), player.get('active_days', 0)
    week = bool(player.get('first_hit_at')) and now - player['first_hit_at'] >= 6 * DAY and days >= 7
    goals = (
        ('first', 'First strike', 'Land your first hit.', hits, 1),
        ('burst', 'Crimson veteran', 'Trigger 10 Crimson bursts.', player.get('bursts', hits // 10), 10),
        ('weak', 'Weakness hunter', 'Match 100 random weaknesses.', player.get('weak_hits', 0), 100),
        ('arsenal', 'Full arsenal', 'Land 25 hits with each of the three styles.', min(player.get('styles', {}).get(s, 0) for s in STYLES), 25),
        ('loyal', 'Three-day crew', 'Attack in 3 different personal raid days.', days, 3),
        ('regular', 'Crimson regular', 'Attack in 5 different personal raid days.', days, 5),
        ('week', 'Weeklong guardian', 'Attack in 7 personal raid days over at least 6 full days.', min(days, 7) if week else min(days, 6), 7),
        ('legend', 'Crimson legend', 'Land 500 hits and earn Weeklong guardian.', min(hits, 500) if week else min(hits, 499), 500),
    )
    return [dict(id=key, label=label, description=description, earned=value >= target,
                 progress=min(value, target), target=target) for key, label, description, value, target in goals]


def validate_profiles(profiles, limit, households=None):
    if not isinstance(profiles, dict) or len(profiles) > limit:
        raise ValueError('Invalid community player profiles.')
    names = set()
    # Network/household fields are accepted for recovery compatibility only.
    # Multiple independent profiles may have the same legacy network value.
    for key, p in profiles.items():
        if not isinstance(key, str) or not re.fullmatch(r'[a-f0-9]{64}', key) or not isinstance(p, dict):
            raise ValueError('Invalid community player profile.')
        name = username(p.get('name'))
        network = p.get('network')
        if not isinstance(network, str) or not re.fullmatch(r'[a-f0-9]{64}', network):
            raise ValueError('Invalid private connection identifier.')
        if name.casefold() in names:
            raise ValueError('Duplicate community username.')
        names.add(name.casefold())
        if 'recovery_hash' in p and (not isinstance(p['recovery_hash'], str) or not re.fullmatch(r'[a-f0-9]{64}', p['recovery_hash'])):
            raise ValueError('Invalid private recovery digest.')
        if 'recovery_at' in p and (type(p['recovery_at']) not in (int, float) or not 0 <= p['recovery_at'] <= 10**12):
            raise ValueError('Invalid recovery timestamp.')
        for field in ('named_at', 'first_hit_at'):
            n = p.get(field)
            if type(n) not in (float, int) or not 0 <= n <= 10**12:
                raise ValueError('Invalid player timestamp.')
        for field in ('attacks', 'active_days', 'weak_hits', 'bursts', 'last_day'):
            n = p.get(field)
            if type(n) is not int or not (-1 if field == 'last_day' else 0) <= n <= MAX_NUMBER:
                raise ValueError('Invalid achievement progress.')
        if not isinstance(p.get('styles'), dict) or set(p['styles']) != set(STYLES):
            raise ValueError('Invalid style progress.')
        for n in p['styles'].values():
            if type(n) is not int or not 0 <= n <= p['attacks']:
                raise ValueError('Invalid style count.')
        if (p['weak_hits'] > p['attacks'] or p['bursts'] > p['attacks'] // 10
                or p['active_days'] > p['attacks'] or sum(p['styles'].values()) > p['attacks']):
            raise ValueError('Inconsistent achievement totals.')
    return copy.deepcopy(profiles)
