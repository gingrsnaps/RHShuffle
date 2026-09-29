"""Username form, cookie ownership and real persistence regressions."""
from html.parser import HTMLParser
import secrets
import unittest

import test_comfort_update as support
from boss import validate_boss
from wager_backend import create_app


class NameForm(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.active = False
        self.attributes, self.fields = {}, {}
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'form':
            self.active = attrs.get('id') == 'playerNameForm'
            if self.active:
                self.attributes = attrs
        if self.active and tag == 'input' and 'name' in attrs:
            self.fields[attrs['name']] = attrs.get('value', '')

    def handle_endtag(self, tag):
        if tag == 'form':
            self.active = False


class UsernameSaveTests(unittest.TestCase):
    setUp = support.ComfortTests.setUp
    player = support.ComfortTests.player
    post = support.ComfortTests.post
    hit = support.ComfortTests.hit

    def save(self, client, value, name):
        return client.post('/play/api/profile', json={
            'username': name, 'raid_id': value['state']['raid_id'],
        }, headers={'X-CSRF-Token': value['player_csrf']})

    def test_actual_html_form_saves_without_javascript_and_survives_reload(self):
        c = self.app.test_client()
        form = NameForm(c.get('/play').text)
        self.assertEqual(form.attributes['method'], 'post')
        self.assertEqual(form.attributes['action'], '/play/profile')
        cookie = c.get_cookie('rh_raider').value
        # This is the browser's native form payload, not a separately invented API request.
        response = c.post(form.attributes['action'], data={**form.fields, 'username': 'Native Raider'})
        self.assertEqual(response.status_code, 303)
        self.assertNotIn('Native', response.headers['Location'])
        page = c.get(response.headers['Location'])
        self.assertIn('Playing as <strong id="playingAs">Native Raider</strong>', page.text)
        self.assertIn('hidden', NameForm(page.text).attributes)
        self.assertEqual(c.get_cookie('rh_raider').value, cookie)
        for _ in range(3):
            self.assertEqual(c.get('/play/api/state').json['state']['you']['display_name'], 'Native Raider')
        restarted = create_app(self.root, testing=True)
        same = restarted.test_client()
        same.set_cookie('rh_raider', cookie)
        self.assertIn('Native Raider', same.get('/play').text)

    def test_expired_page_session_cannot_break_valid_player_cookie(self):
        c = self.player()
        value = c.get('/play/api/state').json
        cookie = c.get_cookie('rh_raider').value
        c.delete_cookie('session')
        self.assertEqual(self.save(c, value, 'Persistent Raider').status_code, 200)
        c.delete_cookie('session')
        hit = c.post('/play/api/attack', json={'raid_id': value['state']['raid_id'],
            'style': 'blade', 'request_id': secrets.token_hex(16)},
            headers={'X-CSRF-Token': value['player_csrf']})
        self.assertEqual(hit.status_code, 200)
        c.delete_cookie('session')
        recovery = c.post('/play/api/recovery-code', headers={'X-CSRF-Token': value['player_csrf']})
        self.assertEqual(recovery.status_code, 200)
        self.assertEqual(c.get_cookie('rh_raider').value, cookie)

    def test_login_rotation_keeps_player_token_but_player_token_cannot_edit_admin(self):
        c = self.player()
        value = c.get('/play/api/state').json
        with c.session_transaction() as session:
            session.update(user='gingrsnaps', auth_version=1, csrf='rotated-admin-token')
        self.assertEqual(self.save(c, value, 'Same Browser').status_code, 200)
        saved = self.b.export()
        response = c.post('/admin/boss/action', data={'csrf': value['player_csrf'],
            'action': 'pause', 'raid_id': value['state']['raid_id']})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.b.export(), saved)

    def test_player_tokens_are_browser_bound_and_missing_cookies_are_explained(self):
        a, b = self.player(), self.player()
        value = a.get('/play/api/state').json
        self.assertEqual(self.save(b, value, 'Forged').status_code, 400)
        bad = {**value, 'player_csrf': '🔥'}
        self.assertEqual(self.save(a, bad, 'Forged').status_code, 400)
        a.delete_cookie('rh_raider')
        response = self.save(a, value, 'Missing Cookie')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['code'], 'player_cookie_required')
        self.assertIn('cookie', response.json['error'])
        self.assertFalse(self.b.export().get('profiles'))

    def test_native_failure_preserves_draft_and_returns_a_working_form(self):
        c = self.player()
        form = NameForm(c.get('/play').text)
        response = c.post('/play/profile', data={**form.fields, 'username': 'Keep my draft', 'csrf': 'expired'})
        self.assertEqual(response.status_code, 400)
        repaired = NameForm(response.text)
        self.assertEqual(repaired.fields['username'], 'Keep my draft')
        self.assertEqual(repaired.attributes['method'], 'post')
        self.assertNotIn('hidden', repaired.attributes)
        self.assertEqual(c.post(repaired.attributes['action'], data=repaired.fields).status_code, 303)
        value = c.get('/play/api/state').json
        self.assertEqual(value['state']['you']['display_name'], 'Keep my draft')

    def test_name_save_does_not_depend_on_the_raid_open_when_form_loaded(self):
        c = self.player()
        value = c.get('/play/api/state').json
        self.b.control('restart', value['state']['raid_id'])
        self.assertEqual(self.save(c, value, 'Next Raid Too').status_code, 200)
        self.assertEqual(c.get('/play/api/state').json['state']['you']['display_name'], 'Next Raid Too')

    def test_reusing_a_name_cannot_claim_or_change_another_players_progress(self):
        a = self.player('Same Name')
        self.hit(a)
        code = self.post(a, '/play/api/recovery-code').json['code']
        before = self.b.export()
        b = self.player('Same Name')
        av, bv = [c.get('/play/api/state').json['state']['you'] for c in (a, b)]
        self.assertNotEqual(av['name'], bv['name'])
        self.assertEqual(bv['damage'], 0)
        self.assertFalse(bv['recovery_saved'])
        self.assertTrue(av['recovery_saved'])
        for key, profile in before['profiles'].items():
            self.assertEqual(self.b.export()['profiles'][key], profile)
        self.assertNotIn(code, b.get('/play/api/state').text)
        self.assertEqual(self.hit(b).status_code, 200)
        validate_boss(self.b.export())
        restarted = create_app(self.root, testing=True)
        self.assertEqual(len(restarted.extensions['boss'].export()['profiles']), 2)

    def test_native_validation_is_escaped_and_does_not_erase_existing_name(self):
        c = self.player('Existing')
        form = NameForm(c.get('/play?edit_name=1').text)
        value = ' <img src=x>\x01 '
        response = c.post('/play/profile', data={**form.fields, 'username': value})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn('<img src=x>', response.text)
        self.assertIn('&lt;img src=x&gt;', response.text)
        self.assertEqual(c.get('/play/api/state').json['state']['you']['display_name'], 'Existing')

    def test_recovery_rotates_player_token_to_recovered_identity(self):
        a = self.player('Owner'); self.hit(a)
        code = self.post(a, '/play/api/recovery-code').json['code']
        b = self.player('Other')
        old = b.get('/play/api/state').json['player_csrf']
        recovered = self.post(b, '/play/api/recover', code=code).json
        self.assertNotEqual(recovered['player_csrf'], old)
        self.assertEqual(self.save(b, recovered, 'Owner').status_code, 200)
        self.assertEqual(self.save(b, {**recovered, 'player_csrf':old}, 'Other').status_code, 400)


if __name__ == '__main__':
    unittest.main()
