"""V14 public race consistency and privacy-safe Gaming activity tests."""
from contextlib import contextmanager
import json
from pathlib import Path
import time
import unittest

from gaming import Gaming, player_key

ROOT = Path(__file__).resolve().parents[1]


class MemoryStore:
    def __init__(self):
        self.value = {}

    @contextmanager
    def connection(self, transaction=False):
        yield self.value


class PublicGamingProjectionTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.game = Gaming(self.store)
        self.now = time.time()

    def player(self, identity, name, visible):
        return self.game.confirm_community_name(identity, name, visible, now=self.now)

    def activity(self, identity, game, *, net, rounds, at=None):
        with self.store.connection(transaction=True) as conn:
            data = conn['gaming']
            player = data['players'][player_key(identity)]
            stats = player['stats'][game]
            stats.update(bets=rounds, wagered=100 * rounds,
                         paid=100 * rounds + net, net=net,
                         biggest_payout=max(0, 100 + net))
            Gaming._touch_activity(data, player, game, self.now if at is None else at,
                                   round_completed=True)

    def test_public_projection_names_only_opted_in_players(self):
        self.player('visible', 'VisiblePlayer', True)
        self.player('private', 'PrivatePlayer', False)
        self.activity('visible', 'dice', net=250, rounds=3)
        self.activity('private', 'plinko', net=9000, rounds=8)

        value = self.game.public_leaderboard(self.now + 1)
        self.assertEqual(value['active_count'], 2)  # aggregate counts include private play
        self.assertEqual([row['name'] for row in value['live_players']], ['VisiblePlayer'])
        self.assertEqual([row['name'] for row in value['weekly_leaders']], ['VisiblePlayer'])
        self.assertEqual([row['name'] for row in value['game_leaders']['dice']], ['VisiblePlayer'])
        self.assertEqual(value['game_leaders']['plinko'], [])

        rendered = json.dumps(value)
        self.assertNotIn('PrivatePlayer', rendered)
        def keys(node):
            if isinstance(node, dict):
                for key, child in node.items():
                    yield str(key).lower()
                    yield from keys(child)
            elif isinstance(node, list):
                for child in node:
                    yield from keys(child)
        projected_keys = set(keys(value))
        for private_field in ('wallet', 'player_tag', 'ip', 'balance', 'receipt',
                              'server_seed', 'recovery', 'funding'):
            self.assertNotIn(private_field, projected_keys)

    def test_reads_do_not_create_activity_and_status_expires(self):
        self.player('quiet', 'QuietPlayer', True)
        self.game.view('quiet', 'QuietPlayer', now=self.now)
        self.assertEqual(self.game.public_leaderboard(self.now + 1)['active_count'], 0)

        self.activity('quiet', 'blackjack', net=10, rounds=1)
        first = self.game.public_leaderboard(self.now + 1)
        self.assertEqual(first['live_players'][0]['status'], 'Playing now')
        # A cached projection remains byte-for-byte stable until a visible status changes.
        self.assertEqual(first, self.game.public_leaderboard(self.now + 2))
        later = self.game.public_leaderboard(self.now + 31)
        self.assertEqual(later['live_players'][0]['status'], 'Recently active')
        expired = self.game.public_leaderboard(self.now + 121)
        self.assertEqual(expired['active_count'], 0)
        self.assertEqual(expired['live_players'], [])

    def test_game_specific_rankings_use_settled_stats(self):
        self.player('one', 'One', True)
        self.player('two', 'Two', True)
        self.activity('one', 'dice', net=50, rounds=4)
        self.activity('two', 'dice', net=75, rounds=2)
        self.activity('one', 'keno', net=100, rounds=1)
        board = self.game.public_leaderboard(self.now + 1)
        self.assertEqual([row['name'] for row in board['game_leaders']['dice']], ['Two', 'One'])
        self.assertEqual([row['name'] for row in board['weekly_leaders']], ['One', 'Two'])
        self.assertEqual(board['weekly_leaders'][0]['rank'], 1)


class PublicTemplateTests(unittest.TestCase):
    def text(self, name):
        return (ROOT / name).read_text(encoding='utf-8')

    def test_race_title_and_provider_cards_are_uniform(self):
        page = self.text('templates/index.html')
        self.assertIn('<h1 id="raceTitle">RedHunllef Wager Race</h1>', page)
        self.assertEqual(page.count('<small>Powered By</small>'), 2)
        self.assertEqual(page.count('class="provider-brand-card'), 2)
        script = self.text('static/empiredrop.js')
        self.assertNotIn("raceTitle').textContent", script)
        self.assertNotIn("raceDescription').textContent", script)

    def test_public_operational_status_is_removed(self):
        page = self.text('templates/index.html')
        for technical in ('sourceTime', 'dataState', 'next check', 'Automatic refresh',
                          'last verified', 'streamStatus'):
            self.assertNotIn(technical.lower(), page.lower())
        self.assertIn('Standings are temporarily unavailable.', self.text('static/app.js'))

    def test_public_gaming_feed_and_filters_exist(self):
        page = self.text('templates/gaming.html')
        backend = self.text('wager_backend.py')
        script = self.text('static/gaming.js')
        self.assertIn('Live Gaming leaderboard', page)
        self.assertIn('data-community-filter="all"', page)
        self.assertIn("'/gaming/api/public-leaderboard'", backend)
        self.assertIn('renderCommunity(value.community)', script)
        self.assertIn('document.hidden', script)
        self.assertIn('public_visibility', backend)


if __name__ == '__main__':
    unittest.main()
