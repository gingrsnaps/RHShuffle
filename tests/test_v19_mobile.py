from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_provider_default_is_url_only():
    js=(ROOT/'static/empiredrop.js').read_text()
    assert "localStorage.getItem('rh.public.provider')" not in js
    assert "localStorage.setItem('rh.public.provider'" not in js
    assert "searchParams.get('provider')" in js
    assert "requested === 'empiredrop' ? empireTab : shuffleTab" in js

def test_v19_css_loaded_and_old_layers_consolidated():
    base=(ROOT/'templates/base.html').read_text()
    assert 'v19-system.css' in base
    assert 'v14-modern.css' not in base
    assert 'v15-system.css' not in base
    assert 'v16-system.css' not in base
    css=(ROOT/'static/v19-system.css').read_text()
    assert '.responsive-results thead{display:none}' in css
    assert '.admin-responsive-table thead{display:none}' in css
    assert 'body[data-page="admin"] .calendar-field' in css

def test_mobile_data_labels_present():
    index=(ROOT/'templates/index.html').read_text()
    history=(ROOT/'templates/history.html').read_text()
    assert 'class="responsive-results"' in index
    assert 'data-label="Wagered"' in index
    assert 'class="responsive-history"' in history
    assert 'data-label="Recorded prize"' in history

def test_public_menu_has_mobile_focus_and_scroll_management():
    js=(ROOT/'static/public-control.js').read_text()
    assert 'public-menu-open' in js
    assert "event.key === 'Tab'" in js
    assert 'lastFocused' in js

def test_release_updated():
    config=(ROOT/'config.py').read_text()
    assert '2026.11.14-shuffle-first-mobile-v19' in config
