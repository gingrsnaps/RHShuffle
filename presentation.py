"""Small view models for change review and private recovery status."""
import re

from race import token
from race_support import fmt_et, money

LABELS = {
    'start_time': 'Starts · Eastern Time', 'end_time': 'Ends · Eastern Time',
    'site_name': 'Website name', 'race_title': 'Race title',
    'race_description': 'Description', 'kick_channel_slug': 'Kick channel',
    'campaign_code_filter': 'Campaign filter', 'stream_url': 'Livestream link',
    'sponsor_name': 'Sponsor name', 'sponsor_url': 'Sponsor link',
    'community_name': 'Community label', 'community_url': 'Community link',
    'responsible_gambling_url': 'Responsible play link',
}


def changes(before, after):
    result = []
    for key, label in LABELS.items():
        old, new = before.get(key), after.get(key)
        if old != new:
            display = fmt_et if key.endswith('_time') else lambda v: str(v or 'Not set')
            result.append(dict(label=label, before=display(old), after=display(new)))
    for rank in range(1, 16):
        old, new = before.get('prizes', {}).get(str(rank), '0'), after.get('prizes', {}).get(str(rank), '0')
        if money(old) != money(new):
            result.append(dict(label=f'Place {rank} prize', before=money(old), after=money(new)))
    return result


def admin_fingerprint(admin):
    # Exclude migration fields and background timestamps. Exporting a checkpoint
    # never increments the settings revision or invalidates an open admin form.
    return token({key: admin.get(key) for key in (
        'users', 'secret_key', 'site_settings', 'overrides', 'race_history', 'banned_ips', 'audit_log')})


def export_marker(admin, snapshot, boss, generated_at):
    return dict(generated_at=generated_at, admin_token=admin_fingerprint(admin),
                standings_token=token(snapshot['last_top15']), raid_id=boss['id'],
                boss_version=boss['version'], attacks=boss['total_attacks'], damage=boss['total_damage'])


def valid_marker(value):
    """Ignore damaged optional metadata without discarding recovered game data."""
    if not isinstance(value, dict):
        return None
    for key in ('generated_at', 'boss_version', 'attacks', 'damage'):
        if type(value.get(key)) is not int or not 0 <= value[key] <= 10**12:
            return None
    for key, length in (('admin_token', 20), ('standings_token', 20), ('raid_id', 32)):
        if not isinstance(value.get(key), str) or not re.fullmatch(r'[a-f0-9]{%d}' % length, value[key]):
            return None
    return {key: value[key] for key in ('generated_at', 'boss_version', 'attacks', 'damage',
                                       'admin_token', 'standings_token', 'raid_id')}


def checkpoint_status(marker, admin, rows, boss):
    marker = valid_marker(marker)
    if not marker:
        return dict(generated_at=0, label='No recovery export recorded', changes=True,
                    details='Generate a private recovery file to protect this checkpoint.')
    new_raid = marker.get('raid_id') != boss['raid_id']
    attacks = max(0, boss['total_attacks'] - marker.get('attacks', 0)) if not new_raid else boss['total_attacks']
    damage = max(0, boss['total_damage'] - marker.get('damage', 0)) if not new_raid else boss['total_damage']
    changed = admin_fingerprint(admin) != marker.get('admin_token')
    standings = token(rows[:15]) != marker.get('standings_token')
    raid_changed = new_raid or boss['version'] != marker.get('boss_version')
    notes = ([f'{attacks:,} new hits · {damage:,} damage'] if attacks else [])
    if new_raid: notes.append('a different raid is active')
    elif raid_changed and not attacks: notes.append('raid controls changed')
    if changed: notes.append('account or race settings changed')
    if standings: notes.append('standings changed')
    return dict(generated_at=marker.get('generated_at', 0), changes=changed or standings or raid_changed,
                label='Changes since last export' if notes else 'Checkpoint matches current progress',
                details='; '.join(notes) or 'No new saved progress since this export.',
                attacks=attacks, damage=damage, new_raid=new_raid)
