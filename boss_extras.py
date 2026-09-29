"""Small, bounded raid additions: cosmetic rally, pace estimates and host history.

These features never change damage, replenish health or limit successful hits.
All timestamps and counts come from committed server attacks.
"""
import copy
import math
import re
import time

MAX_NUMBER = 2**53 - 1
RALLY_GOAL, RALLY_WINDOW = 15, 600


def record_activity(state, player_key, damage, now):
    rally = state.setdefault('rally', {'players': {}, 'unlocked_at': 0})
    if not rally['unlocked_at']:
        rally['players'] = {k: t for k, t in rally['players'].items() if t > now - RALLY_WINDOW}
        rally['players'][player_key] = now
        if len(rally['players']) >= RALLY_GOAL:
            rally['unlocked_at'] = now
            rally['players'] = {}  # No ongoing writes needed after the cosmetic unlock.
    minute = int(now // 60)
    pace = [b for b in state.get('pace', []) if b['minute'] > minute - 60]
    if not pace or pace[-1]['minute'] != minute:
        pace.append(dict(minute=minute, damage=0, attacks=0))
    pace[-1]['damage'] += damage
    pace[-1]['attacks'] += 1
    state['pace'] = pace


def rally_view(state, now):
    rally = state.get('rally', {})
    reached = bool(rally.get('unlocked_at'))
    times = [t for t in rally.get('players', {}).values() if t > now - RALLY_WINDOW]
    return dict(goal=RALLY_GOAL, count=RALLY_GOAL if reached else len(times),
                window_seconds=RALLY_WINDOW, unlocked=reached,
                unlocked_at=rally.get('unlocked_at', 0),
                next_expiry=min(times) + RALLY_WINDOW if times else 0)


def balance_view(state, now):
    # Whole minute buckets bound the work to sixty records per view. Label the
    # estimate as approximate: attendance and selected styles can change it.
    recent = [b for b in state.get('pace', []) if b['minute'] > int(now // 60) - 60]
    elapsed = max(60, min(3600, now - state['started_at'])) if state['started_at'] else 60
    damage, hits = sum(b['damage'] for b in recent), sum(b['attacks'] for b in recent)
    enough = elapsed >= 300 and hits >= 10 and damage > 0
    rate = damage * 3600 / elapsed if enough else 0
    return dict(damage_per_hour=round(rate), sample_hits=hits, sample_seconds=round(elapsed),
                remaining_seconds=math.ceil(state['hp'] / rate * 3600) if rate else None,
                observed=bool(rate), presets=[dict(label=label, days=days,
                    hp=min(MAX_NUMBER, max(1, round(rate * 24 * days))) if rate else fallback)
                    for label, days, fallback in [('Short raid', 3, 10_000_000), ('Long raid', 5, 25_000_000), ('Epic raid', 7, 50_000_000)]])


def host_snapshot(state):
    return dict(name=state.get('settings', {}).get('name', 'Crimson Hunllef'),
                hp=state['hp'], max_hp=state['max_hp'], paused=state['paused'],
                damage=state.get('settings', {}).get('damage', 100),
                weak_damage=state.get('settings', {}).get('weak_damage', 150),
                burst_bonus=state.get('settings', {}).get('burst_bonus', 100),
                avatar=state.get('avatar_hash') or 'Original logo')


def audit(state, action, actor, before, after, now=None):
    entry = dict(action=action, actor=str(actor)[:64], at=int(time.time() if now is None else now),
                 before=copy.deepcopy(before), after=copy.deepcopy(after))
    state['admin_history'] = (state.get('admin_history', []) + [entry])[-100:]


def validate_extras(state, limit):
    households = state.get('households', {})
    if not isinstance(households, dict) or len(households) > limit:
        raise ValueError('Invalid shared connection settings.')
    for key, slots in households.items():
        if not isinstance(key, str) or not re.fullmatch(r'[a-f0-9]{64}', key) or type(slots) is not int or not 2 <= slots <= 10:
            raise ValueError('Invalid shared connection allowance.')
    rally = state.get('rally', {'players': {}, 'unlocked_at': 0})
    if not isinstance(rally, dict) or not isinstance(rally.get('players'), dict) or len(rally['players']) > RALLY_GOAL:
        raise ValueError('Invalid community rally.')
    timestamps = [rally.get('unlocked_at')]
    for key, t in rally['players'].items():
        if not isinstance(key, str) or not re.fullmatch(r'[a-f0-9]{64}', key): raise ValueError('Invalid rally player.')
        timestamps.append(t)
    if any(type(n) not in (int, float) or not 0 <= n <= 10**12 for n in timestamps):
        raise ValueError('Invalid rally time.')
    pace = state.get('pace', [])
    if not isinstance(pace, list) or len(pace) > 60:
        raise ValueError('Invalid raid pace.')
    previous = -1
    for b in pace:
        if (not isinstance(b, dict) or any(type(b.get(k)) is not int or not 0 <= b[k] <= MAX_NUMBER for k in ('minute', 'damage', 'attacks'))
                or b['minute'] <= previous): raise ValueError('Invalid raid pace bucket.')
        previous = b['minute']
    history = state.get('admin_history', [])
    if not isinstance(history, list) or len(history) > 100: raise ValueError('Invalid boss admin history.')
    for entry in history:
        if (not isinstance(entry, dict) or type(entry.get('at')) is not int or not 0 <= entry['at'] <= 10**12
                or any(not isinstance(entry.get(k), str) or len(entry[k]) > 64 for k in ('actor', 'action'))):
            raise ValueError('Invalid boss admin history entry.')
        for k in ('before', 'after'):
            if not isinstance(entry.get(k), dict) or len(entry[k]) > 12: raise ValueError('Invalid boss change summary.')
            for name, v in entry[k].items():
                if (not isinstance(name, str) or len(name) > 64 or
                    not (v is None or type(v) is bool or type(v) is int and abs(v) <= MAX_NUMBER
                         or isinstance(v, str) and len(v) <= 256)):
                    raise ValueError('Invalid boss change value.')
