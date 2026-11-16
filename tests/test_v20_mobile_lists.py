from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v20_release_and_stylesheet():
    assert '2026.11.16-compact-mobile-lists-v20' in (ROOT/'config.py').read_text()
    base=(ROOT/'templates/base.html').read_text()
    assert 'v20-system.css' in base
    assert 'v19-system.css' not in base

def test_public_mobile_standings_are_grouped_not_square_cards():
    css=(ROOT/'static/v20-system.css').read_text()
    assert '.responsive-results tbody{display:block}' in css
    assert 'border-bottom:1px solid #302a33' in css
    assert 'border-radius:0;background:transparent' in css
    assert 'grid-template-columns:38px minmax(0,1fr) max-content' in css
    assert 'content:"Prize · "' in css
    assert css.count('/* V20 compact grouped standings and mobile-first release. */') == 1

def test_mobile_podium_prioritizes_first_place():
    css=(ROOT/'static/v20-system.css').read_text()
    assert '.podium-card.place-1{grid-column:1/-1;order:1!important}' in css
    assert '.podium-card.place-2{order:2!important}' in css
    assert '.podium-card.place-3{order:3!important}' in css

def test_history_and_admin_use_grouped_lists():
    css=(ROOT/'static/v20-system.css').read_text()
    assert '.responsive-history tbody{display:block}' in css
    assert '.admin-responsive-table tbody{display:block}' in css
    assert '.operations-entry:last-child{border-bottom:0!important}' in css
