"""Small view models for change review and private recovery status."""
import re

MAX_NUMBER = 2**53 - 1
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


def gaming_fingerprint(value):
    return token({key: [p['version'], p['season'], p['name']] for key,p in value['players'].items()}) if value else ''


def export_marker(admin, snapshot, generated_at, gaming=None):
    return dict(generated_at=generated_at, admin_token=admin_fingerprint(admin),
                standings_token=token(snapshot['last_top15']),
                gaming_token=gaming_fingerprint(gaming))


def valid_marker(value):
    """Accept new checkpoints and safely upgrade older checkpoint markers."""
    if not isinstance(value, dict):
        return None
    generated = value.get('generated_at')
    if type(generated) is not int or not 0 <= generated <= 10**12:
        return None
    for key, length in (('admin_token', 20), ('standings_token', 20)):
        if not isinstance(value.get(key), str) or not re.fullmatch(r'[a-f0-9]{%d}' % length, value[key]):
            return None
    result = {key: value[key] for key in ('generated_at', 'admin_token', 'standings_token')}
    token_value = value.get('gaming_token', '')
    if isinstance(token_value, str) and re.fullmatch(r'[a-f0-9]{20}|', token_value):
        result['gaming_token'] = token_value
    return result


def checkpoint_status(marker, admin, rows, gaming=None):
    marker = valid_marker(marker)
    if not marker:
        return dict(generated_at=0, label='No recovery export recorded', changes=True,
                    details='Generate a private recovery file to protect this checkpoint.')
    changed = admin_fingerprint(admin) != marker.get('admin_token')
    standings = token(rows[:15]) != marker.get('standings_token')
    gaming_changed = marker.get('gaming_token', '') != gaming_fingerprint(gaming)
    notes = []
    if changed: notes.append('account or race settings changed')
    if standings: notes.append('standings changed')
    if gaming_changed: notes.append('RedPoints wallets or fairness receipts changed')
    return dict(generated_at=marker.get('generated_at', 0),
                changes=changed or standings or gaming_changed,
                label='Changes since last export' if notes else 'Checkpoint matches current progress',
                details='; '.join(notes) or 'No new saved progress since this export.')
