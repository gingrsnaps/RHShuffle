"""Disposable localhost-only visual fixture. Never starts provider workers."""
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flask import jsonify
from race import calculate, empty, normalize
from wager_backend import create_app
from waitress import create_server

FIXED_TIME = 1791028800  # October 3, 2026, noon UTC.
CLOCK = [FIXED_TIME]

if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
        'APP_ENV':'test', 'ADMIN_BOOTSTRAP_PASS':'visual-fixture-password',
        'SUPERADMIN_USER':'gingrsnaps', 'SESSION_COOKIE_SECURE':'never'}, clear=True), patch('time.time', side_effect=lambda: CLOCK[0]):
        app = create_app(Path(directory), testing=True)
        runtime, boss = app.extensions['runtime'], app.extensions['boss']
        admin = runtime.admin
        admin['site_settings'].update(start_time=FIXED_TIME-86400, end_time=FIXED_TIME+4*86400, community_url='https://example.test/community')
        rows = [dict(username='CommunityPlayer%02d'%n, weightedWagerAmount=str(150000-n*3200), campaignCode='Red') for n in range(30)]
        snapshot = calculate({**empty(admin['site_settings']), **normalize(rows, admin['site_settings']), 'updated_at':FIXED_TIME, 'ok':True}, admin, runtime.config)
        runtime.commit(admin, runtime.revision, snapshot=snapshot)
        with patch.object(runtime.providers, 'shuffle', return_value=rows):
            runtime.history.check(FIXED_TIME)

        @app.post('/__fixture__/progress/<int:percent>')
        def progress(percent):
            if percent not in {0,25,75,100}:
                return jsonify(error='Unsupported test state'), 400
            state = boss.summary()
            boss.control('remaining_health', state['raid_id'], state['max_hp']*(100-percent)//100, health_revision=state['health_revision'], actor='Visual fixture')
            return jsonify(ok=True)

        @app.post('/__fixture__/advance')
        def advance_clock():
            CLOCK[0] += 2
            return jsonify(ok=True)

        server = create_server(app, host='127.0.0.1', port=0, threads=6)
        print(json.dumps({'port':server.effective_port}), flush=True)
        try:
            server.run()
        finally:
            server.close()
