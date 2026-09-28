"""Host edits must preserve raid progress and validate real image bytes."""
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, PngImagePlugin

from boss import BossError, DEFAULT_HP, fresh_raid, validate_boss
from boss_avatar import image_bytes
from wager_backend import create_app


def picture(fmt='PNG', size=(900, 450)):
    stream = io.BytesIO()
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text('Comment', 'Private image metadata')
    Image.new('RGB', size, '#d82832').save(stream, format=fmt, pnginfo=metadata)
    return stream.getvalue()


class BossAdminTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        environment = patch.dict(os.environ, {
            'APP_ENV': 'test', 'ADMIN_BOOTSTRAP_PASS': 'test-only-password',
        }, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        self.app = create_app(self.root, testing=True)
        self.runtime = self.app.extensions['runtime']
        self.boss = self.app.extensions['boss']
        self.addCleanup(self.runtime.store.close)
        self.client = self.app.test_client()
        self.client.environ_base['REMOTE_ADDR'] = '192.0.2.1'
        self.csrf = self.client.get('/play/api/state').json['csrf']
        with self.client.session_transaction() as session:
            session.update(user='gingrsnaps', auth_version=1)

    def form(self, action, **fields):
        state = self.boss.status()
        return dict(csrf=self.csrf, action=action, raid_id=state['raid_id'],
                    health_revision=str(state['health_revision']), settings_revision=str(state['settings_revision']), **fields)

    def post(self, action, **fields):
        return self.client.post('/admin/boss/action', data=self.form(action, **fields))

    def upload(self, raw=None, filename='boss.png'):
        return self.post('avatar', avatar=(io.BytesIO(raw if raw is not None else picture()), filename))

    def hit(self, guest='one', ip='192.0.2.1'):
        state = self.boss.status(guest, ip)
        return self.boss.attack(guest, ip, state['weakness'], state['raid_id'], 'request-' + guest)

    def test_png_jpg_jpeg_webp_are_decoded_resized_and_cacheable_without_metadata(self):
        for fmt, filename in [('PNG', 'boss.png'), ('JPEG', '../../boss.JPG'), ('JPEG', 'boss.jpeg'), ('WEBP', 'boss.webp')]:
            with self.subTest(fmt=fmt):
                self.assertEqual(self.upload(picture(fmt), filename).status_code, 303)
                view = self.boss.status()
                self.assertTrue(view['avatar_custom'])
                response = self.client.get(view['avatar_url'])
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, 'image/png')
                self.assertIn('immutable', response.headers['Cache-Control'])
                self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
                with Image.open(io.BytesIO(response.data)) as saved:
                    self.assertEqual(saved.size, (512, 256))
                    self.assertNotIn('Comment', saved.info)
                    self.assertNotIn('exif', saved.info)
                cached = self.client.get(view['avatar_url'], headers={'If-None-Match': response.headers['ETag']})
                self.assertEqual(cached.status_code, 304)
                self.assertEqual(cached.data, b'')
                self.assertIn(view['avatar_url'], self.client.get('/play').text)
                self.assertIn(view['avatar_url'], self.client.get('/').text)
                self.assertIn(view['avatar_url'], self.client.get('/admin?tab=boss').text)
                self.assertNotIn('community_boss_avatar', self.client.get('/play/api/state').text)
                self.assertNotIn(self.boss.avatar_document['data'], self.client.get('/public-state').text)

    def test_invalid_images_cannot_replace_existing_avatar_or_raid(self):
        self.upload()
        before = self.boss.recovery()
        gif = picture('GIF', (20, 20))
        for raw, filename in [(b'', 'boss.png'), (b'<script>alert(1)</script>', 'boss.png'),
                              (gif, 'boss.png'), (picture()[:40], 'boss.png'),
                              (picture(), 'boss.svg'), (b'x' * (4 * 1024 * 1024 + 1), 'boss.jpg')]:
            with self.subTest(filename=filename, length=len(raw)):
                self.assertEqual(self.upload(raw, filename).status_code, 422)
                self.assertEqual(self.boss.recovery(), before)
        with patch('boss_avatar.MAX_PIXELS', 100):
            self.assertEqual(self.upload(picture(size=(11, 10))).status_code, 422)
        frames = [Image.new('RGBA', (10, 10), color) for color in ('red', 'blue')]
        animation = io.BytesIO()
        frames[0].save(animation, format='PNG', save_all=True, append_images=frames[1:], duration=100, loop=0)
        self.assertEqual(self.upload(animation.getvalue()).status_code, 422)
        animation = io.BytesIO()
        frames[0].save(animation, format='WEBP', save_all=True, append_images=frames[1:], duration=100, loop=0)
        self.assertEqual(self.upload(animation.getvalue(), 'boss.webp').status_code, 422)
        self.assertEqual(self.boss.recovery(), before)

    def test_avatar_changes_keep_progress_accounts_and_cooldowns(self):
        self.hit()
        raid = self.boss.export()
        admin = self.runtime.store.admin()
        self.assertEqual(self.upload().status_code, 303)
        current = self.boss.export()
        for field in ('id', 'hp', 'max_hp', 'total_damage', 'total_attacks', 'players', 'networks'):
            self.assertEqual(current[field], raid[field])
        self.assertEqual(self.runtime.store.admin(), admin)
        with self.assertRaises(BossError) as blocked:
            self.hit('two', '192.0.2.1')
        self.assertEqual(blocked.exception.code, 'cooldown')
        image_url = self.boss.status()['avatar_url']
        self.boss.control('restart', current['id'])
        self.boss.loaded_at = 0
        self.assertEqual(self.boss.status()['avatar_url'], image_url)
        self.assertEqual(self.post('avatar_reset').status_code, 303)
        self.assertEqual(self.boss.status()['avatar_url'], '/static/redlogo.png')
        self.assertEqual(self.client.get(image_url).status_code, 404)

    def test_explicit_health_edit_uses_latest_damage_and_keeps_allowances(self):
        self.hit()
        form = self.form('health', health='3000000', confirm_health='yes')
        self.hit('two', '192.0.2.2')  # A hit after the host opened the form is not lost.
        before = self.boss.export()
        self.assertEqual(self.client.post('/admin/boss/action', data=form).status_code, 303)
        current = self.boss.export()
        self.assertEqual(current['hp'], 3_000_000 - 300)
        self.assertEqual(current['health_revision'], 1)
        for field in ('id', 'total_damage', 'total_attacks', 'players', 'networks'):
            self.assertEqual(current[field], before[field])
        self.assertEqual(self.post('health', health='2000000', confirm_health='yes').status_code, 303)
        self.assertEqual(self.boss.status()['hp'], 2_000_000 - 300)
        with patch('boss.time.time', return_value=current['started_at'] + 7 * 86400):
            self.boss.loaded_at = 0
            self.assertEqual(self.boss.status()['hp'], 2_000_000 - 300)
        validate_boss(self.boss.export())

    def test_health_edit_requires_confirmation_valid_range_and_current_revision(self):
        before = self.boss.export()
        for fields in ({'health': '3000000'}, {'health': 'oops', 'confirm_health': 'yes'},
                       {'health': '0', 'confirm_health': 'yes'}, {'health': '100000001', 'confirm_health': 'yes'}):
            self.assertEqual(self.post('health', **fields).status_code, 422)
            self.assertEqual(self.boss.export(), before)
        old = self.form('health', health='3000000', confirm_health='yes')
        self.assertEqual(self.post('health', health='4000000', confirm_health='yes').status_code, 303)
        self.assertEqual(self.client.post('/admin/boss/action', data=old).status_code, 422)
        self.assertEqual(self.boss.status()['max_hp'], 4_000_000)
        self.boss.control('restart', before['id'])
        self.assertEqual(self.client.post('/admin/boss/action', data=old).status_code, 422)
        self.assertEqual(self.boss.status()['max_hp'], DEFAULT_HP)

    def test_completed_raid_only_reopens_after_explicit_health_edit(self):
        small = fresh_raid(health=50)
        with self.runtime.store.connection(transaction=True) as conn:
            self.boss._write(conn, small, new_raid=True)
        self.boss.loaded_at = 0
        self.hit()
        self.assertEqual(self.boss.status()['status'], 'victory')
        self.upload()
        self.assertEqual(self.boss.status()['hp'], 0)
        self.assertEqual(self.post('health', health='100000', confirm_health='yes').status_code, 303)
        self.assertEqual(self.boss.status()['hp'], 99_950)
        self.assertEqual(self.boss.status()['status'], 'active')
        self.assertEqual(self.boss.status()['total_damage'], 50)
        validate_boss(self.boss.export())

    def test_private_recovery_and_cold_start_keep_avatar_and_health_edits(self):
        self.hit()
        self.upload()
        self.post('health', health='3000000', confirm_health='yes')
        self.post('settings', boss_name='The Scarlet Beast', base_damage='120', weak_damage='180', burst_bonus='90')
        saved = self.boss.recovery()
        checkpoint = self.client.get('/admin/recovery-backup').json
        for field in saved:
            self.assertEqual(checkpoint[field], saved[field])
        # Existing state takes precedence, even with a malformed new seed.
        (self.root / 'private').mkdir(exist_ok=True)
        (self.root / 'private/recovery.seed.json').write_text('{}', encoding='utf-8')
        restarted = create_app(self.root, testing=True)
        self.addCleanup(restarted.extensions['runtime'].store.close)
        self.assertEqual(restarted.extensions['boss'].recovery(), saved)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'private').mkdir()
            (root / 'private/recovery.seed.json').write_text(json.dumps(checkpoint), encoding='utf-8')
            restored = create_app(root, testing=True)
            self.addCleanup(restored.extensions['runtime'].store.close)
            self.assertEqual(restored.extensions['boss'].recovery(), saved)
            url = restored.extensions['boss'].status()['avatar_url']
            self.assertEqual(restored.test_client().get(url).data, image_bytes(saved['community_boss_avatar']))
            restored.extensions['runtime'].store.close()
        preview = self.client.post('/admin/recovery-preview', data={
            'csrf': self.csrf, 'recovery': (io.BytesIO(json.dumps(checkpoint).encode()), 'checkpoint.json'),
        })
        self.assertEqual(preview.status_code, 200)
        self.assertIn('Custom image included', preview.text)
        checkpoint['community_boss_avatar']['sha256'] = '0' * 64
        response = self.client.post('/admin/recovery-preview', data={
            'csrf': self.csrf, 'recovery': (io.BytesIO(json.dumps(checkpoint).encode()), 'checkpoint.json'),
        })
        self.assertEqual(response.status_code, 422)
        self.assertIn('checksum', response.text)
        self.assertEqual(self.boss.recovery(), saved)

    def test_upload_and_health_require_admin_and_csrf(self):
        for action, fields in [('avatar', {'avatar': (io.BytesIO(picture()), 'boss.png')}),
                               ('health', {'health': '3000000', 'confirm_health': 'yes'})]:
            form = self.form(action, **fields)
            form['csrf'] = 'forged'
            self.assertEqual(self.client.post('/admin/boss/action', data=form).status_code, 400)
        self.runtime.admin['users']['helper'] = copy.deepcopy(self.runtime.admin['users']['gingrsnaps'])
        self.runtime.commit(self.runtime.admin, self.runtime.revision)
        with self.client.session_transaction() as session:
            session['user'] = 'helper'
        self.assertIn('id="bossAvatarFile"', self.client.get('/admin?tab=boss').text)
        self.assertEqual(self.upload().status_code, 303)
        self.assertEqual(self.post('health', health='3000000', confirm_health='yes').status_code, 303)
        self.assertEqual(self.client.get('/admin/recovery-backup').status_code, 403)
        before = self.boss.recovery()
        with self.client.session_transaction() as session:
            session.pop('user')
        self.assertEqual(self.upload().status_code, 302)
        self.assertEqual(self.post('health', health='3000000', confirm_health='yes').status_code, 302)
        self.assertEqual(self.boss.recovery(), before)

    def test_every_boss_write_rejects_guests_forged_roles_and_revoked_sessions(self):
        before = self.boss.recovery()
        for mode in ('guest', 'unknown-account', 'revoked', 'bad-cookie', 'bad-csrf', 'missing-token', 'unicode-token'):
            self.client.delete_cookie('session')
            with self.client.session_transaction() as session:
                session.update(csrf=self.csrf, is_admin=True, role='superadmin')
                if mode != 'guest':
                    session.update(user='missing' if mode == 'unknown-account' else 'gingrsnaps',
                                   auth_version=0 if mode == 'revoked' else 1)
                if mode == 'missing-token':
                    session.pop('csrf')
            if mode == 'bad-cookie':
                self.client.set_cookie('session', 'forged-not-signed')
            for action in ('avatar', 'avatar_reset', 'health', 'settings', 'pause', 'resume', 'restart'):
                with self.subTest(mode=mode, action=action), patch('wager_backend.from_upload') as decode:
                    form = self.form(action, health='3000000', confirm_health='yes', confirm_restart='yes',
                                     boss_name='Unauthorized', base_damage='9000', weak_damage='9999', burst_bonus='9999',
                                     role='superadmin', is_admin='true', user='gingrsnaps')
                    if action == 'avatar':
                        form['avatar'] = (io.BytesIO(picture('WEBP')), 'boss.webp')
                    if mode == 'bad-csrf':
                        form['csrf'] = 'forged'
                    if mode == 'missing-token':
                        form['csrf'] = '!'
                    if mode == 'unicode-token':
                        form['csrf'] = '🔥'
                    response = self.client.post('/admin/boss/action', data=form, headers={
                        'Accept': 'application/json', 'X-Admin': 'true', 'X-User': 'gingrsnaps',
                    })
                    self.assertEqual(response.status_code, 400 if mode in {'bad-csrf', 'missing-token', 'unicode-token'} else 401)
                    decode.assert_not_called()
                    self.assertEqual(self.boss.recovery(), before)

    def test_regular_admin_can_sign_in_and_manage_boss_but_not_export_accounts(self):
        self.runtime.admin['users']['helper'] = copy.deepcopy(self.runtime.admin['users']['gingrsnaps'])
        self.runtime.commit(self.runtime.admin, self.runtime.revision)
        self.client.post('/admin/logout', data={'csrf': self.csrf})
        self.csrf = self.client.get('/play/api/state').json['csrf']
        login = self.client.post('/admin', data={'csrf': self.csrf, 'username': 'helper', 'password': 'test-only-password'})
        self.assertEqual(login.status_code, 303)
        self.csrf = self.client.get('/play/api/state').json['csrf']
        page = self.client.get('/admin?tab=boss').text
        self.assertIn('id="bossSettingsForm"', page)
        self.assertIn('image/webp', page)
        self.assertNotIn('Download private recovery file', page)
        self.assertEqual(self.post('settings', boss_name='Ruby Colossus', base_damage='120', weak_damage='180', burst_bonus='75').status_code, 303)
        self.assertEqual(self.upload(picture('WEBP'), 'boss.webp').status_code, 303)
        self.assertEqual(self.post('health', health='3500000', confirm_health='yes').status_code, 303)
        for action in ('pause', 'resume', 'avatar_reset'):
            self.assertEqual(self.post(action).status_code, 303)
        self.assertEqual(self.post('restart', health='2500000', confirm_restart='yes').status_code, 303)
        self.assertEqual(self.boss.status()['name'], 'Ruby Colossus')
        self.assertEqual(self.boss.status()['rules']['weak_damage'], 180)
        self.assertEqual(self.client.get('/admin/recovery-backup').status_code, 403)
        # Deleting an admin invalidates its existing browser session immediately.
        self.runtime.admin['users'].pop('helper')
        self.runtime.commit(self.runtime.admin, self.runtime.revision)
        before = self.boss.export()
        self.assertEqual(self.post('pause').status_code, 302)
        self.assertEqual(self.boss.export(), before)

    def test_damage_settings_apply_to_future_hits_and_public_forgery_has_no_effect(self):
        self.assertEqual(self.post('settings', boss_name='Ruby Colossus', base_damage='300', weak_damage='400', burst_bonus='50').status_code, 303)
        # Keep signed admin cookies within their real 12-hour lifetime while
        # advancing the combat clock through ten one-minute cooldowns.
        with patch('boss.time.time', return_value=self.boss.export()['created_at']) as clock:
            for index in range(10):
                clock.return_value += 60
                state = self.boss.status('player', '192.0.2.10')
                result = self.boss.attack('player', '192.0.2.10', state['weakness'], state['raid_id'], f'damage-hit-{index}')
                self.assertEqual(result['hit']['damage'], 450 if index == 9 else 400)
            saved = self.boss.export()
            self.assertEqual(self.post('settings', boss_name='Ruby Colossus', base_damage='10', weak_damage='20', burst_bonus='0').status_code, 303)
            after = self.boss.export()
            for field in ('id', 'hp', 'players', 'networks', 'total_damage', 'total_attacks'):
                self.assertEqual(after[field], saved[field])
            retry = self.boss.attack('player', '192.0.2.10', 'blade', saved['id'], 'damage-hit-9')
            self.assertTrue(retry['duplicate'])
            self.assertEqual(retry['hit']['damage'], 450)
            guest = self.app.test_client()
            snapshot = guest.get('/play/api/state').json
            forged = guest.post('/play/api/attack', json={
                'raid_id': snapshot['state']['raid_id'], 'style': snapshot['state']['weakness'], 'request_id': 'forged-damage-attempt',
                'damage': 99_999_999, 'hp': 0, 'name': 'Changed', 'settings_revision': 999,
                'settings': {'damage': 9999}, 'role': 'superadmin', 'action': 'health',
            }, headers={'X-CSRF-Token': snapshot['csrf']})
            self.assertEqual(forged.status_code, 200)
            self.assertEqual(forged.json['hit']['damage'], 20)
            self.assertEqual(self.boss.status()['name'], 'Ruby Colossus')
            self.assertEqual(self.boss.status()['hp'], saved['hp'] - 20)
            validate_boss(self.boss.export())  # Old 450-point receipts remain valid.

    def test_name_and_damage_validation_stale_forms_and_storage_write_guard(self):
        values = dict(boss_name='Ruby Colossus', base_damage='100', weak_damage='150', burst_bonus='100')
        before = self.boss.export()
        for invalid in ({'boss_name': ''}, {'boss_name': 'x' * 61}, {'boss_name': 'bad\nname'},
                        {'base_damage': '0'}, {'weak_damage': '99'}, {'weak_damage': '10001'},
                        {'burst_bonus': '-1'}, {'burst_bonus': '0.5'}, {'base_damage': 'true'}):
            self.assertEqual(self.post('settings', **{**values, **invalid}).status_code, 422)
            self.assertEqual(self.boss.export(), before)
        stale = self.form('settings', **values)
        self.assertEqual(self.post('settings', **values).status_code, 303)
        self.assertEqual(self.client.post('/admin/boss/action', data=stale).status_code, 422)
        saved = self.boss.export()
        bypass = copy.deepcopy(saved)
        bypass['settings']['damage'] = 10
        with self.assertRaises(BossError) as blocked:
            with self.runtime.store.connection(transaction=True) as conn:
                self.boss._write(conn, bypass)
        self.assertEqual(blocked.exception.code, 'settings_guard')
        self.assertEqual(self.boss.export(), saved)
        stale = self.form('settings', **values)
        self.post('restart', confirm_restart='yes')
        self.assertEqual(self.client.post('/admin/boss/action', data=stale).status_code, 422)
        self.assertEqual(self.boss.status()['name'], 'Ruby Colossus')

    def test_public_pages_have_no_editor_and_boss_names_render_as_text(self):
        name = '<img src=x onerror=alert(1)>'
        self.post('settings', boss_name=name, base_damage='100', weak_damage='150', burst_bonus='100')
        guest = self.app.test_client()
        for url in ('/', '/play'):
            page = guest.get(url).text
            self.assertIn('&lt;img', page)
            self.assertNotIn(name, page)
            for editor in ('bossAvatarFile', 'bossNameInput', 'bossMaxHealth', 'bossSettingsForm'):
                self.assertNotIn('id="' + editor + '"', page)
            self.assertNotIn('action="/admin/boss/action"', page)
        before = self.boss.recovery()
        self.assertEqual(guest.get('/admin/boss/action?action=health&health=0').status_code, 405)
        self.assertEqual(guest.post('/play/api/state', json={'hp': 0}).status_code, 405)
        self.assertEqual(guest.get('/admin?tab=boss').status_code, 200)
        self.assertNotIn('bossSettingsForm', guest.get('/admin?tab=boss').text)
        self.assertEqual(self.boss.recovery(), before)


if __name__ == '__main__':
    unittest.main()
