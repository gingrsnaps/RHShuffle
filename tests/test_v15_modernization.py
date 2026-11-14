from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def text(path):
    return (ROOT / path).read_text(encoding='utf-8')


def test_v15_style_loads_last_and_public_copy_is_uniform():
    base = text('templates/base.html')
    index = text('templates/index.html')
    assert 'v19-system.css' in base
    assert 'RedPoints Games' in base
    assert 'RedHunllef Wager Race' in index
    assert index.count('Powered By') == 2
    assert 'Compete in the weekly race and climb the standings.' in index


def test_gaming_dashboard_prioritizes_community_and_uses_dialogs():
    page = text('templates/gaming.html')
    assert 'Community Leaderboard' in page
    assert page.index('Community Leaderboard') < page.index('game-cards-v15')
    assert '<dialog id="gamingProfile"' in page
    assert '<dialog id="gamingRecovery"' in page
    assert 'game-nav' not in page
    assert 'Show me on the Community Leaderboard' in page
    assert 'Create Profile & Play' in page


def test_both_provider_schedules_use_shared_calendar_controls():
    shuffle = text('templates/admin_race.html')
    empire = text('templates/admin_empiredrop.html')
    script = text('static/admin-calendar.js')
    assert 'data-calendar-form="shuffle"' in shuffle
    assert 'type="date"' in shuffle and 'type="time"' in shuffle
    assert 'data-calendar-form="empiredrop"' in empire
    assert 'type="date"' in empire and 'type="time"' in empire
    assert 'Sync provider dates' in empire
    assert 'America/New_York' in script
    assert 'dateStyle' not in script


def test_admin_routes_are_direct_and_focused():
    backend = text('wager_backend.py')
    admin = text('templates/admin.html')
    for route in (
        '/admin/leaderboards/shuffle/prizes',
        '/admin/leaderboards/shuffle/source',
        '/admin/leaderboards/empiredrop/schedule',
        '/admin/leaderboards/empiredrop/payouts',
        '/admin/leaderboards/empiredrop/source',
    ):
        assert route in backend
        assert route in admin
    assert "workspace('race', 'schedule')" in backend
    assert "workspace('race', 'prizes')" in backend
    assert "workspace('shuffle', 'shuffleSource')" in backend


def test_public_operational_noise_remains_hidden():
    css = text('static/v19-system.css')
    index = text('templates/index.html')
    assert '.source-status' in css
    assert 'Standings are temporarily unavailable.' in index
    assert 'Next provider check' not in index
    assert 'Automatic refresh' not in index
