"""Disposable, synthetic eight-game fixture. Never starts provider workers."""
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fairness import GAMES, VERSION
from wager_backend import create_app
from waitress import create_server

if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {
        'APP_ENV':'test', 'ADMIN_BOOTSTRAP_PASS':'fixture-only',
        'SUPERADMIN_USER':'fixtureadmin', 'SESSION_COOKIE_SECURE':'never',
        'TRUST_APP_PLATFORM':'1',
    }, clear=True):
        app = create_app(Path(folder), testing=True)
        game = app.extensions['gaming']
        options = dict(dice=dict(chance=50,side='under'), keno=dict(picks=list(range(1,11)),risk='medium'),
                       plinko=dict(rows=16,risk='high'), blackjack=dict(decks=6), limbo=dict(target=200),
                       coinflip=dict(side='heads'), poker=dict(variant='texas_holdem',button='player'), baccarat=dict(decks=8,side='banker'))
        for index in range(7):
            identity, name, ip = 'fixture-'+str(index), 'TestPlayer'+str(index+1), '192.0.2.'+str(index+1)
            for item in GAMES:
                wallet=game.view(identity,name,client_ip=ip)
                body=dict(rules_version=VERSION, game=item, request_id=identity+'-'+item,
                          season=wallet['season']['id'], nonce=wallet['nonce'], commitment=wallet['commitment'],
                          client_seed='test-only', client_salt='ab'*16, wager=100, options=options[item])
                result=game.bet(identity,name,body,client_ip=ip)
                if not result['receipt'] and item == 'blackjack':
                    hand=result['wallet']['blackjack']
                    game.blackjack_action(identity,name,dict(round_id=hand['round_id'],step=0,action='stand',action_id='fixture-stand'),client_ip=ip)
                while not result['receipt'] and item == 'poker':
                    hand=result['wallet']['poker']
                    result=game.poker_action(identity,name,dict(variant='texas_holdem',round_id=hand['round_id'],step=hand['step'],move=dict(action='check' if hand['legal']['check'] else 'call',amount=0),action_id='fixture-move-'+str(hand['step'])),client_ip=ip)
        if len(sys.argv) == 3 and sys.argv[1] == '--write-fixtures':
            # DOM tests can generate their inputs without a browser or HTTP server.
            destination = Path(sys.argv[2])
            destination.mkdir(parents=True, exist_ok=True)
            client = app.test_client()
            with client.session_transaction() as session:
                session.update(user='fixtureadmin', auth_version=1, csrf='fixture-token')
            page, state = client.get('/admin/gaming'), client.get('/admin/gaming/status')
            assert page.status_code == state.status_code == 200
            (destination/'admin.html').write_text(page.text, encoding='utf-8')
            (destination/'state.json').write_text(json.dumps(state.json), encoding='utf-8')
            app.extensions['runtime'].store.close()
            raise SystemExit(0)
        server=create_server(app,host='127.0.0.1',port=0,threads=6)
        print(json.dumps({'port':server.effective_port}),flush=True)
        try:server.run()
        finally:server.close()
