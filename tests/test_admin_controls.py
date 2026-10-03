"""Exercise account/log controls in addition to the existing race/boss suites."""
import copy
import re
import unittest

import test_app


class AdminControlTests(unittest.TestCase):
    setUp = test_app.AppTests.setUp
    action = test_app.AppTests.action

    def test_account_add_password_reset_removal_and_logout(self):
        password = 'new-private-test-password'
        self.assertEqual(self.action('add_account', username='helper', new_password=password, confirm_password=password).status_code, 303)
        helper = self.app.test_client()
        csrf = re.search('name="csrf" value="([^"]+)"', helper.get('/admin').text).group(1)
        self.assertEqual(helper.post('/admin', data={'csrf':csrf, 'username':'helper', 'password':password}).status_code, 303)
        for tab in ('overview','race','players','boss','settings'):
            response = helper.get('/admin?tab='+tab)
            self.assertEqual(response.status_code, 200)
            self.assertIn('CONTROL CENTER', response.text)
        self.assertEqual(helper.get('/admin/recovery-backup').status_code, 403)
        self.assertEqual(self.action('reset_password', username='helper', new_password=password+'2', confirm_password=password+'2').status_code, 303)
        self.assertEqual(helper.get('/admin/status').status_code, 401)
        self.assertEqual(self.action('remove_account', username='helper').status_code, 303)
        self.assertNotIn('helper', self.r.admin['users'])
        self.assertEqual(self.client.post('/admin/logout', data={'csrf':'test-token'}).status_code, 303)
        self.assertEqual(self.client.get('/admin/status').status_code, 401)

    def test_ban_unban_and_clear_logs(self):
        visitor = self.app.test_client()
        visitor.environ_base['REMOTE_ADDR'] = '192.0.2.23'
        self.assertEqual(self.action('ban_ip', ip='192.0.2.23').status_code, 303)
        self.assertEqual(visitor.get('/history').status_code, 403)
        self.assertEqual(self.action('unban_ip', ip='192.0.2.23').status_code, 303)
        self.assertEqual(visitor.get('/history').status_code, 200)
        for action in ('clear_access', 'clear_audit'):
            self.assertEqual(self.action(action).status_code, 303)
        self.assertEqual([entry['action'] for entry in self.r.admin['audit_log']], ['clear_audit'])

    def test_admin_cannot_block_own_forwarded_address_on_app_platform(self):
        self.r.config.proxy = True
        response = self.client.post('/admin/action', data={
            'csrf':'test-token', 'action':'ban_ip', 'ip':'192.0.2.51',
            'tab':'settings', 'revision':self.r.revision},
            headers={'DO-Connecting-IP':'192.0.2.51'})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn('192.0.2.51', self.r.admin['banned_ips'])
        self.assertIn('cannot block the address', response.text)

    def test_every_general_admin_write_needs_session_and_csrf(self):
        before = copy.deepcopy(self.r.admin)
        guest = self.app.test_client()
        for action in ('refresh','save_race','override','add_account','remove_account','reset_password','password','preview_restore','restore','ban_ip','unban_ip','clear_audit','clear_access'):
            with self.subTest(action=action):
                response = guest.post('/admin/action', data={'action':action}, headers={'Accept':'application/json'})
                self.assertEqual(response.status_code, 401)
                response = self.client.post('/admin/action', data={'action':action}, headers={'Accept':'application/json'})
                self.assertEqual(response.status_code, 400)
        self.assertEqual(self.r.admin, before)


if __name__ == '__main__':
    unittest.main()
