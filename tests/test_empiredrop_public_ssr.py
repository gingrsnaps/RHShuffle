"""Server-rendered EmpireDrop standings regression coverage.

The public HTML must show all provider-returned participants on first paint,
not depend entirely on JavaScript. These tests use fake player data only.
"""
import re
import unittest
from pathlib import Path
from jinja2 import Environment, StrictUndefined, select_autoescape

INDEX = (Path(__file__).resolve().parents[1] / 'templates/index.html').read_text(encoding='utf-8')
# Render the actual fragment (the complete page also requires the complete Shuffle context).
FRAGMENT = INDEX[INDEX.index('{# Server-render verified standings'): INDEX.index('<p class="leaderboard-foot">Names masked')]


def render(rows, limit=15, enabled=False):
    env = Environment(autoescape=select_autoescape(['html']), undefined=StrictUndefined)
    tmpl = env.from_string(FRAGMENT)
    return tmpl.render(data={'empiredrop':{
        'rows':rows,
        'race_meta':{'ranks_limit':limit},
        'prizes':{'enabled':enabled, 'formatted':{str(i):'€1.00' for i in range(1,16)}}
    }})


def sample(n):
    return [{'rank':i, 'username':f'P{i:02}******',
             'wager':f'€{i*100}.00', 'prize':'—'} for i in range(1,n+1)]


class InitialHTMLTests(unittest.TestCase):
    def test_ten_players_are_in_first_response_html(self):
        html = render(sample(10), limit=10)
        for i in range(1,11):
            attr='data-empire-name' if i<=3 else 'data-empire-row-name'
            self.assertIn(f'{attr}="{i}">P{i:02}******', html)
            wager='data-empire-wager' if i<=3 else 'data-empire-row-wager'
            self.assertIn(f'{wager}="{i}">€{i*100}.00', html)
        for i in range(11,16):
            self.assertNotIn(f'data-empire-row-name="{i}"', html)
        self.assertIn('Showing 10 of 10 leaderboard positions',html)

    def test_fifteen_provider_players_display_only_top_ten(self):
        html=render(sample(15),limit=15,enabled=True)
        for i in range(1,11):
            self.assertIn(f'P{i:02}******',html)
        for i in range(11,16):
            self.assertNotIn(f'P{i:02}******',html)
        self.assertIn('Top 10 of 15 supplied by EmpireDrop',html)
        self.assertNotIn('Not reported by EmpireDrop',html)

    def test_tied_ranks_and_escaping(self):
        rows=sample(3)
        rows[2]['rank']=2
        rows[1]['username']='Q<unsafe>'
        html=render(rows, limit=3)
        self.assertIn('data-empire-place="3">02',html)
        self.assertIn('Q&lt;unsafe&gt;',html)
        self.assertNotIn('Q<unsafe>',html)

if __name__=='__main__':unittest.main()
