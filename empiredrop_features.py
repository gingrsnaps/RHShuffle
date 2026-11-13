"""Independent EmpireDrop rewards and public-name presentation.

These are *advertised local prizes*, not confirmed provider payouts or
payment instructions. Shuffle's settings are never copied implicitly.
"""
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import re

# EmpireDrop advertises ten local payout positions; Shuffle remains Top 15.
EMPIRE_PLACES = 10
DEFAULT_REWARDS = {'currency': 'EUR', 'enabled': False,
                   'prizes': {str(i): '0.00' for i in range(1, EMPIRE_PLACES + 1)},
                   'revision': 1, 'updated_at': 0, 'updated_by': ''}
CURRENCY_SIGNS = {'EUR': '€', 'USD': '$'}
_AMOUNT = re.compile(r'^(?:\d{1,7})(?:\.\d{1,2})?$')


def validate_rewards(value):
    """Reject negative/oversized/ambiguous payouts before saving any state.

    Private revision/audit metadata is validated here but stripped by the public
    projection. Old exports without metadata are upgraded additively.
    """
    if not isinstance(value, dict) or set(value) - {'currency', 'enabled', 'prizes', 'revision', 'updated_at', 'updated_by'}:
        raise ValueError('Invalid EmpireDrop payout settings.')
    currency = value.get('currency', 'EUR')
    if currency not in CURRENCY_SIGNS:
        raise ValueError('Choose EUR or USD for EmpireDrop rewards.')
    prizes = value.get('prizes', DEFAULT_REWARDS['prizes'])
    if not isinstance(prizes, dict) or set(prizes) not in (
        set(DEFAULT_REWARDS['prizes']), {str(i) for i in range(1, 16)}
    ):
        raise ValueError('Provide a payout for every position from 1 to 10.')
    # Accept old 15-place JSON exports but normalize to the new ten places.
    # Old places 11-15 are not advertised and never enter the new prize pool.
    result = {}
    for key in DEFAULT_REWARDS['prizes']:
        val = str(prizes[key]).strip()
        if not _AMOUNT.fullmatch(val):
            raise ValueError('Place ' + key + ': use a non-negative amount with at most two decimal places.')
        amt = Decimal(val)
        if amt > Decimal('1000000'):
            raise ValueError('Place ' + key + ': payout cannot exceed 1,000,000.')
        result[key] = f'{amt:.2f}'
    revision = value.get('revision', 1)
    updated_at = value.get('updated_at', 0)
    updated_by = value.get('updated_by', '')
    if type(revision) is not int or revision < 1 or revision > 2**31-1:
        raise ValueError('Invalid EmpireDrop payout revision.')
    if type(updated_at) is not int or not 0 <= updated_at <= 4102444799:
        raise ValueError('Invalid EmpireDrop payout timestamp.')
    if not isinstance(updated_by, str) or len(updated_by) > 64 or not updated_by.isprintable():
        raise ValueError('Invalid EmpireDrop payout editor.')
    return {'currency': currency, 'enabled': value.get('enabled') is True, 'prizes': result,
            'revision': revision, 'updated_at': updated_at, 'updated_by': updated_by}


def format_reward(value, currency):
    return CURRENCY_SIGNS[currency] + f'{Decimal(str(value)):,.2f}'


def rewards_public(raw):
    """Only prize amounts and currency are public, never admin metadata."""
    value = validate_rewards(raw if raw else {})
    pool = sum((Decimal(v) for v in value['prizes'].values()), Decimal(0))
    return {'currency': value['currency'], 'enabled': value['enabled'],
            'prizes': value['prizes'], 'total': format_reward(pool, value['currency']),
            'formatted': {k: format_reward(v, value['currency']) for k, v in value['prizes'].items()}}


def payout_for_rows(rows, rewards):
    """Per-player advertised reward by *provider rank*, split evenly on ties.

    EmpireDrop's ranking may skip ranks after ties. We do not renumber its
    official results, and we do not imply that a prize has been paid.
    """
    count = Counter(row.get('rank') for row in rows)
    observed = defaultdict(int)
    for row in rows:
        rank = row.get('rank')
        val = rewards['prizes'].get(str(rank))
        if rewards['enabled'] and val is not None and count[rank] > 0:
            # Divide *integer cents* and distribute any leftover cents in
            # provider order, so displayed shares always sum to the rank prize.
            cents = int(Decimal(val) * 100)
            base, extra = divmod(cents, count[rank])
            share = base + int(observed[rank] < extra)
            observed[rank] += 1
            yield {**row, 'prize': format_reward(Decimal(share) / 100, rewards['currency'])}
        else:
            yield {**row, 'prize': '—'}


def mask_public_username(name):
    """Display exactly two prefix *slots* and six trailing asterisks.

    The partner API anonymizes ``user.name`` before we receive it. The second
    character of ``s********z`` is a provider mask, NOT a known letter. Using
    the raw first two characters would render ``s*******`` (seven asterisks)
    rather than the public board's consistent eight-character display.

    Use a visible bullet for a character the provider has already hidden.
    Example: ``s********z`` -> ``s•******``; ``Re********tie`` -> ``Re******``.
    Never search for visible suffix characters to invent an unmasked prefix.
    Admin keeps the original, provider-masked name for reference.
    """
    clean = str(name or '').strip()
    masked = {'*', '＊', '•', '●', '∙', '·'}
    prefix = []
    for position in (0, 1):
        char = clean[position] if position < len(clean) else ''
        prefix.append('•' if not char or char in masked or not char.isprintable() else char)
    return ''.join(prefix) + '******'
