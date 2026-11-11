"""Safe, provider-agnostic data-quality summaries for the administration UI.

This module never calls a remote API. It reads already-verified local snapshots
and emits only operational metadata; names, player IDs and credentials stay out.
Neither provider's amounts are converted, inferred, or combined here.
"""

from race_support import fmt_et
import time

_ERROR_HELP = {
    'access': 'Check the API key pair and the server outbound IP allowlist.',
    'rate_limit': 'Provider rate limit reached. Leave automatic retry enabled.',
    'format': 'The provider response did not match the documented data format.',
    'scope': 'Check that the selected race belongs to this affiliate account.',
    'selection': 'Select a race slug, or enable auto-select for one running race.',
    'window': 'Check the saved race dates and whether the provider accepts this period.',
    'bad_request': 'Shuffle rejected a request parameter. Review race dates and affiliate endpoint settings.',
    'configuration': 'Review the race mode, slug, and API configuration.',
    'connection': 'Check outbound network connectivity from the application.',
    'http': 'Check the provider status and retry later.',
}


def _int(value):
    return value if type(value) is int and 0 <= value <= 10 ** 12 else 0


def _component(health, key):
    return next((x for x in (health or {}).get('components', [])
                 if isinstance(x, dict) and x.get('key') == key), {})


def summarize_providers(status, empire):
    """Return two uniform cards with explicit source-quality indicators.

    status: output of Runtime.status() (admin only)
    empire: output of EmpireDropBoard.private_status() (admin only)
    Every displayed field is operational or aggregated, never a credential.
    """
    health = status.get('health') or {}
    jobs = status.get('jobs') or {}
    shuffle = jobs.get('shuffle') or {}
    quality = status.get('diagnostics') or {}
    s_health = _component(health, 'shuffle')
    e_health = _component(health, 'empiredrop')
    received = _int(quality.get('received'))
    accepted = _int(quality.get('accepted'))
    missing = _int(quality.get('missing_campaign'))
    rejected = quality.get('rejected') or {}
    rejected_total = sum(_int(n) for n in rejected.values()) if isinstance(rejected, dict) else 0
    s_issues = []
    if not _int(shuffle.get('last_success')):
        s_issues.append('No verified Shuffle response yet.')
    if missing:
        s_issues.append(f'{missing:,} record(s) lack campaign metadata; verify campaign scoping before relying on totals.')
    if rejected_total:
        s_issues.append(f'{rejected_total:,} record(s) were excluded by validation or campaign filtering.')
    if shuffle.get('error'):
        http_status = shuffle.get('http_status')
        s_issues.append(
            'Latest request returned HTTP 400. Review the saved race window and endpoint; this does not prove the API key is invalid.'
            if http_status == 400 else
            'Latest check failed. Previous verified results are retained.'
        )
    site = status.get('site') or {}
    end_time = _int(site.get('end_time'))
    if end_time and end_time < time.time() - 86400:
        s_issues.append(
            'The saved Shuffle race ended on ' + fmt_et(end_time) +
            '. This is a historical window. Open Schedule & prizes to prepare a current race; changes require confirmation.'
        )
    rows = status.get('rows') or []
    s_card = {
        'key': 'shuffle', 'name': 'Shuffle',
        'state': s_health.get('state', 'warning'),
        'status': s_health.get('status', 'Waiting for source'),
        'last_success': _int(shuffle.get('last_success')),
        'last_attempt': _int(shuffle.get('attempt_at')),
        'refresh_seconds': 60,
        'participants': _int(status.get('count')),
        'loaded': len(rows) if isinstance(rows, list) else 0,
        'metric': 'Weighted wager',
        'scope': ('Shuffle window: ' + str((status.get('site') or {}).get('start_et') or 'Not configured') + ' → ' +
                  str((status.get('site') or {}).get('end_et') or 'Not configured')),
        'quality': f'{accepted:,} accepted / {received:,} received' if received else 'Waiting for source records',
        'issues': s_issues, 'action': '/admin?tab=shuffle',
        'details': '/admin?tab=players',
    }
    meta = empire.get('race_meta') or {}
    erows = empire.get('rows') or []
    mode = empire.get('source_mode') or 'races'
    engine, kind = meta.get('engine'), meta.get('type')
    metric = ('Tickets' if engine == 'RAFFLE' else
              'Deposited' if kind == 'DEPOSIT' else 'Wagered')
    e_issues = []
    if not _int(empire.get('updated_at')):
        e_issues.append('No verified EmpireDrop race response yet.')
    kind_error = empire.get('error_kind')
    if kind_error:
        e_issues.append(_ERROR_HELP.get(kind_error, 'Check the selected race and provider connection.'))
    if meta.get('is_active') is False:
        e_issues.append('This race has closed. The provider may return an empty live ranking.')
    if engine == 'RAFFLE':
        e_issues.append('Raffle totals represent tickets, not wagered currency.')
    if kind == 'DEPOSIT' and engine != 'RAFFLE':
        e_issues.append('This race ranks deposits, not wagers.')
    e_card = {
        'key': 'empiredrop', 'name': 'EmpireDrop',
        'state': e_health.get('state', 'warning'),
        'status': e_health.get('status', 'Waiting for source'),
        'last_success': _int(empire.get('updated_at')),
        'last_attempt': _int(empire.get('attempt_at')),
        'refresh_seconds': max(60, min(86400, _int(empire.get('refresh_interval')) or 300)),
        'participants': len(erows) if isinstance(erows, list) else 0,
        'loaded': len(erows) if isinstance(erows, list) else 0,
        'metric': metric,
        'scope': ('Official race: ' + str(meta.get('slug') or 'Not selected')[:100]) if mode == 'races' else
                 ('Custom date window (deprecated API)' if mode == 'legacy_window' else 'Legacy adapter'),
        'quality': (f'{len(erows):,} verified position(s) / provider cap {meta["ranks_limit"]}'
                    if isinstance(erows, list) and type(meta.get('ranks_limit')) is int
                    else 'Awaiting provider ranking confirmation'),
        'issues': e_issues, 'action': '/admin?tab=empiredrop',
        'details': '/admin?tab=empiredrop#empireRaceDetails',
    }
    return {'shuffle': s_card, 'empiredrop': e_card}
