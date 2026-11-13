"""Real HTTP acceptance checks. Run after installing production requirements.

These tests intentionally skip, rather than pretend to pass, if Flask is
unavailable. They never load the bundled real state or make provider requests.
"""
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
pytest.importorskip('flask')
from wager_backend import create_app

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('APP_ENV','local')
    monkeypatch.setenv('SESSION_COOKIE_SECURE','0')
    monkeypatch.setenv('ADMIN_BOOTSTRAP_PASS','V11-test-only-strong-password')
    monkeypatch.delenv('RH_SPACES_ENABLE',raising=False)
    # Use an isolated state root, never the project's private production data.
    (tmp_path/'data').mkdir()
    app=create_app(root=tmp_path,testing=True)
    with app.test_client() as client:
        with client.session_transaction() as sess: sess['csrf']='fixed-test-csrf'
        response=client.post('/admin/login',data={
            'username':'gingrsnaps','password':'V11-test-only-strong-password',
            'csrf':'fixed-test-csrf'},follow_redirects=False)
        assert response.status_code == 303
        yield client

def test_all_visible_admin_workspaces_load(client):
    for tab in ['overview','shuffle','race','players','empiredrop','gaming','settings','activity']:
        r=client.get('/admin?tab='+tab)
        assert r.status_code == 200, (tab,r.status_code)
        assert b'RedHunllef' in r.data

def test_old_admin_links_redirect_to_real_pages(client):
    for section in ['race','players','settings','recovery','wagerers','community','empire','logs']:
        r=client.get('/admin/section/'+section,follow_redirects=True)
        assert r.status_code == 200, section
    assert client.get('/admin/section/not-a-real-section').status_code == 404

def test_registered_route_inventory(client):
    r=client.get('/admin/navigation-status')
    assert r.status_code == 200
    routes={entry['path'] for entry in r.json['registered']}
    assert {'/admin','/admin/action','/admin/empiredrop/refresh','/admin/recovery-backup'} <= routes

def test_forms_reject_bad_post_but_do_not_404(client):
    r=client.post('/admin/action',data={'csrf':'fixed-test-csrf','action':'invalid-unknown-action',
                                        'tab':'settings','revision':'1'})
    assert r.status_code != 404
