"""RedHunllef's sole launch command: python wager_backend.py.

App construction has no provider requests or hidden worker startup. The main
function binds one production server, then starts the two automatic jobs once.
"""
from collections import deque
import copy
import csv
from datetime import timedelta
from decimal import Decimal
from functools import wraps
import io
import hashlib
import hmac
import ipaddress
import json
import logging
import re
import secrets
import signal
import sys
import threading
import time

from flask import Flask, Response, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from flask.sessions import SecureCookieSessionInterface
from itsdangerous import BadSignature, URLSafeSerializer, URLSafeTimedSerializer
from werkzeug.exceptions import BadRequest, HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config, RELEASE
from abuse_guard import AbuseGuard
from boss import BossError, CommunityBoss, DEFAULT_HP, rules as boss_rules, validate_boss
from boss_avatar import from_upload, validate_avatar
from presentation import changes, checkpoint_status, export_marker
from store_schema import upgrade_store
from race import calculate, empty, phase, token
from race_support import (DEFAULT_PRIZES, WEIGHTING_RULES, TEXT_LIMITS, URL_FIELDS,
                          canonical_site, clean_overrides, clean_snapshots, csv_text,
                          decimal_amount, eastern_epoch, empty_snapshots, fmt_et,
                          local_input, money, money_input, race_key, validate_site)
from runtime import Runtime
from storage import Conflict, StoreError
from fairness import GAMES, SUPPORTED_VERSIONS, rules as gaming_rules
from gaming import Gaming, GamingError, validate_gaming
from telemetry import Measurements, health_view

LOG = logging.getLogger("redhunllef")
TABS = {"overview":"Overview", "race":"Race", "players":"Players", "boss":"Community boss", "gaming":"Gaming", "settings":"Settings"}


def account(users, name):
    return next(((k, v) for k, v in users.items() if k.casefold() == str(name).casefold()), (None, None))


def filtered(rows, edits, args):
    view, query, order = args.get("view", "all"), args.get("q", "").strip()[:64], args.get("sort", "rank")
    values = edits if view == "overrides" else rows[:15] if view == "top" else rows
    values = [r for r in values if query.casefold() in r["username"].casefold()]
    if order == "name":
        values = sorted(values, key=lambda r: (r["username"].casefold(), r["username"]))
    elif order == "raw":
        values = sorted(values, key=lambda r: (-decimal_amount(r.get("raw_wager") or 0), r["username"].casefold()))
    return values


def create_app(root=None, testing=False):
    config = Config(root)
    runtime = Runtime(config)
    app = Flask(__name__)
    app.config.update(TESTING=testing, SECRET_KEY=config.secret or runtime.admin["secret_key"],
                      MAX_CONTENT_LENGTH=8 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE="Lax", PERMANENT_SESSION_LIFETIME=timedelta(hours=12))
    app.extensions["runtime"] = runtime
    app.extensions["settings"] = config
    measurements = app.extensions['measurements'] = Measurements()
    boss = app.extensions["boss"] = CommunityBoss(runtime.store)
    gaming = app.extensions['gaming'] = Gaming(runtime.store)
    # One launch restores playable points for everyone, without clearing results.
    # Page requests and five-second live updates never run this bulk reset.
    gaming.restart_balances()
    guest_signer = URLSafeTimedSerializer(app.secret_key, salt="community-boss-guest-v1")
    recovery_signer = URLSafeSerializer(app.secret_key, salt="community-boss-recovery-v1")
    abuse = app.extensions["boss_abuse"] = AbuseGuard(app.secret_key)
    review_signer = URLSafeTimedSerializer(app.secret_key, salt="race-review-v1")
    failures, previews, access_log = {}, {}, deque(maxlen=150)
    auth_lock = threading.Lock()
    dummy_hash = generate_password_hash(secrets.token_hex(16))
    # Shipped assets are UTF-8. Never use the host's default text encoding:
    # Windows CP1252 cannot decode some Unicode characters in the browser code.
    assets = token([
        (p.name, p.read_text(encoding="utf-8"))
        for p in sorted((config.root / "static").glob("*"))
        if p.suffix in {".css", ".js"}
    ])

    class Cookies(SecureCookieSessionInterface):
        def get_cookie_secure(self, app):
            if config.secure_cookie in {"1", "true", "always"}:
                return True
            if config.secure_cookie in {"0", "false", "never"}:
                return False
            return request.is_secure
    app.session_interface = Cookies()

    def csrf():
        return session.setdefault("csrf", secrets.token_urlsafe(32))

    def wants_json():
        """Keep fetch failures machine-readable; native pages still render HTML."""
        return request.path.startswith(("/play/api/", "/gaming/api/")) or request.accept_mimetypes.best == "application/json" or request.path in {
            "/data", "/public-state", "/boss-summary", "/history-state", "/config", "/stream", "/admin/status", "/admin/boss/status", "/admin/gaming/status", "/admin/diagnostics", "/admin/health-report", "/healthz", "/readyz"
        }

    def json_error(message, status, code=None):
        body = dict(ok=False, error=message, status=status, release=RELEASE,
                    request_id=getattr(g, 'request_id', ''), code=code or 'http_'+str(status))
        return jsonify(body), status

    def require_csrf():
        expected = session.get('csrf')
        supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf', '')
        # A missing session token must never match a known fallback value.
        # Reject malformed Unicode cleanly before constant-time ASCII comparison.
        if (not isinstance(expected, str) or not expected or not expected.isascii() or
            not isinstance(supplied, str) or not supplied or not supplied.isascii() or
            not secrets.compare_digest(supplied, expected)):
            abort(400, description="This form expired. Reload the page and try again.")

    def protected(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not g.user:
                if request.path.endswith(("status", "diagnostics", ".csv", "backup")) or wants_json():
                    return jsonify(error="Your session expired. Sign in again.", login_url=url_for("login")), 401
                return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return wrapped

    @app.before_request
    def before():
        g.began, g.user, g.superadmin = time.perf_counter(), None, False
        g.request_id = secrets.token_hex(8)
        # App Platform supplies the visitor address in DO-Connecting-IP. Never
        # trust this header on a directly exposed/local server.
        address = request.headers.get("DO-Connecting-IP") if config.proxy else request.remote_addr
        try:
            g.client_ip = str(ipaddress.ip_address(address))
        except (ValueError, TypeError):
            g.client_ip = None
        if request.path.startswith("/admin"):
            g.revision, g.admin = runtime.sync()
            name, record = account(g.admin["users"], session.get("user"))
            if name and record.get("auth_version", 1) == session.get("auth_version"):
                g.user = name
                g.superadmin = name.casefold() == g.admin.get("superadmin", config.superadmin).casefold()
            if request.endpoint == 'recovery_preview' and g.superadmin:
                # A complete community export can exceed an ordinary form or
                # avatar. Only authenticated Superadmins get this larger limit.
                request.max_content_length = 64 * 1024 * 1024
        if request.path not in {"/healthz", "/readyz"} and g.client_ip in runtime.admin.get("banned_ips", []):
            abort(403, description="Access from this address has been disabled.")

    @app.after_request
    def after(response):
        response.headers['X-Request-ID'] = getattr(g, 'request_id', '')
        elapsed = (time.perf_counter()-g.began)*1000
        if request.endpoint not in {'static', 'health', 'ready'}:
            measurements.request(request.endpoint, response.status_code, elapsed)
        if response.status_code >= 500:
            LOG.error('REQUEST id=%s route=%s status=%s elapsed_ms=%.1f',
                      g.request_id, request.endpoint or 'unmatched', response.status_code, elapsed)
        response.headers.update({"X-Content-Type-Options":"nosniff", "X-Frame-Options":"DENY",
            "Referrer-Policy":"strict-origin-when-cross-origin", "X-RedHunllef-Release":RELEASE,
            "Content-Security-Policy":"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
            "Cache-Control":"public, max-age=31536000, immutable" if request.path.startswith("/static/") and request.args.get("v") == assets else "no-store"})
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        if request.path == "/public-state" and response.status_code in {200, 304}:
            response.headers["Cache-Control"] = "public, no-cache"
        if request.endpoint == 'boss_avatar_image' and response.status_code in {200, 304}:
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        if request.path.startswith("/admin"):
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        if getattr(g, "new_guest", None):
            response.set_cookie("rh_raider", guest_signer.dumps(g.new_guest), max_age=365*86400,
                                secure=app.session_interface.get_cookie_secure(app), httponly=True, samesite="Lax")
        if request.path not in {"/data", "/public-state", "/boss-summary", "/history-state", "/config", "/stream", "/admin/status", "/admin/boss/status", "/healthz", "/readyz"} and not request.path.startswith(("/static/", "/play/api/")):
            with auth_lock:
                access_log.appendleft(dict(time=int(time.time()), method=request.method, path=request.path[:120], status=response.status_code,
                                           ip=g.client_ip, ms=round((time.perf_counter()-g.began)*1000)))
        return response

    @app.context_processor
    def context():
        return dict(release=RELEASE, asset_version=assets, csrf=csrf, money=money, fmt_et=fmt_et,
                    local_input=local_input, tabs=TABS, weighting=WEIGHTING_RULES,
                    local_storage=not runtime.store.pg, hosted_local=config.production and not runtime.store.pg,
                    boss_rules=boss_rules())

    @app.errorhandler(StoreError)
    def storage_error(error):
        LOG.error("STORAGE %s", str(error))
        if wants_json():
            return json_error(str(error), 503)
        return render_template("error.html", title="Connection interrupted", message=str(error)), 503

    @app.errorhandler(HTTPException)
    def page_error(error):
        LOG.warning("HTTP %s %s returned %s (%s).", request.method, request.endpoint or "unmatched route", error.code, error.name)
        if request.endpoint in {'boss_profile', 'boss_profile_form'} and not wants_json():
            return render_play(name_error=error.description, name_draft=request.form.get('username', '')[:64]), error.code
        if wants_json():
            return json_error(error.description, error.code, getattr(error, 'problem_code', None))
        return render_template("error.html", title="Page unavailable" if error.code == 404 else "Request could not be completed",
                               message=error.description), error.code

    @app.errorhandler(500)
    def internal_error(error):
        if wants_json():
            return json_error("The backend could not complete this request. Check the runtime logs and try again.", 500)
        return render_template("error.html", title="Something interrupted this request", message="Reload and try again. Existing saved data remains in place."), 500

    @app.get("/")
    def index():
        return render_template("index.html", data=public_snapshot())

    @app.get('/history')
    def public_history():
        # This request reads a small saved snapshot; it never calls Shuffle.
        return render_template('history.html', data=runtime.public(),
                               history=runtime.history.public(request.args.get('week')))

    @app.get('/boss-summary')
    def public_boss_summary():
        # Anonymous local snapshot: never contacts a provider or creates a player.
        return jsonify(boss=boss.summary(), server_time=time.time(), release=RELEASE)

    @app.get('/history-state')
    def history_state():
        return jsonify(release=RELEASE, **runtime.history.public(request.args.get('week')))

    @app.post('/admin/history/refresh')
    @protected
    def refresh_history():
        require_csrf()
        runtime.history.request_refresh()
        if runtime.started:
            runtime.history.start()
        LOG.info('HISTORY Admin queued completed-week checks; provider retry windows remain enforced.')
        return admin_saved('History check queued. Saved results stay visible; provider retry times still apply.',
                           'overview', 'historyConnection')

    def public_snapshot():
        value = runtime.public()
        value["boss"] = boss.summary()
        return value

    @app.get("/public-state")
    def public_state():
        # The representation excludes the moving clock, so its strong ETag
        # really describes identical bytes. Both 200 and 304 carry fresh time.
        value = public_snapshot()
        server_time = value.pop("server_time")
        response = jsonify(value)
        response.set_etag(token(value))
        response.headers["X-Server-Time"] = str(server_time)
        return response.make_conditional(request)

    def guest():
        if not hasattr(g, "guest"):
            try:
                value = guest_signer.loads(request.cookies.get("rh_raider", ""), max_age=365*86400)
                if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{32}", value):
                    raise BadSignature("Invalid raider identifier")
                g.guest = value
            except BadSignature:
                g.guest = g.new_guest = secrets.token_hex(16)
        return g.guest

    def player_csrf():
        """Bind game writes to the signed raider, independently of admin login.

        The secret-bearing cookie stays HttpOnly. A different browser cannot
        reuse this token, and expiring/logging out of admin does not break play.
        """
        secret = app.secret_key.encode() if isinstance(app.secret_key, str) else app.secret_key
        return hmac.new(secret, ('boss-write-v1:' + guest()).encode(), hashlib.sha256).hexdigest()

    def require_player_csrf():
        guest()
        if getattr(g, 'new_guest', None):
            failure = BadRequest(description='Your browser did not return the player cookie. Open the game directly on its HTTPS site, allow site cookies, then reload. Use http://localhost:8080 for local testing.')
            failure.problem_code = 'player_cookie_required'
            raise failure
        supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf', '')
        if isinstance(supplied, str) and supplied.isascii() and hmac.compare_digest(supplied, player_csrf()):
            return
        # Previously open game pages remain compatible while the new assets load.
        # Admin endpoints still accept only their authenticated session token.
        try:
            require_csrf()
        except BadRequest as failure:
            failure.problem_code = 'csrf_expired'
            raise

    def render_play(**values):
        return render_template('boss.html', data=runtime.public(),
                               boss_data=boss.status(guest(), g.client_ip), player_csrf=player_csrf(), **values)

    def gaming_wallet():
        identity = guest()
        profile = boss.status(identity, g.client_ip)['you']
        return gaming.view(identity, profile['display_name'] if profile['identity_ready'] else '', client_ip=g.client_ip)

    def gaming_player_name():
        # A saved boss profile alone does not bypass Gaming's community-name step.
        wallet = gaming_wallet()
        if wallet.get('play_blocked'):
            issue = wallet['play_blocked']
            raise GamingError(issue['message'], issue['code'], 409)
        if wallet['needs_profile']:
            raise GamingError('Save your community name on Gaming before playing.', 'community_name_required', 409)
        return wallet['name']

    @app.get('/gaming')
    def gaming_home():
        return render_template('gaming.html', data=runtime.public(), wallet=gaming_wallet(),
                               game=None, game_rules=gaming_rules(), player_token=player_csrf())

    @app.get('/gaming/fairness')
    def gaming_fairness():
        return render_template('gaming_fairness.html', data=runtime.public())

    @app.get('/gaming/<game>')
    def gaming_game(game):
        if game not in GAMES: abort(404)
        return render_template('gaming.html', data=runtime.public(), wallet=gaming_wallet(),
                               game=game, game_rules=gaming_rules(), player_token=player_csrf())

    @app.get('/gaming/api/state')
    def gaming_state():
        value = dict(ok=True, wallet=gaming_wallet(), player_csrf=player_csrf(), release=RELEASE)
        response = jsonify(value)
        response.set_etag(token(value))
        return response.make_conditional(request)

    @app.post('/gaming/api/refresh')
    def gaming_refresh():
        # Reset only the signed player's wallet, with the same CSRF rules as bets.
        require_player_csrf()
        try:
            result = gaming.refresh_balance(guest(), gaming_player_name(),
                                             request.get_json(silent=True), client_ip=g.client_ip)
            return jsonify(**result, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_refresh'))

    @app.post('/gaming/api/profile')
    def gaming_profile():
        require_player_csrf()
        body = request.get_json(silent=True)
        if not isinstance(body, dict): return json_error('Enter a valid player name.', 422)
        try:
            profile = boss.register(guest(), g.client_ip, None, body.get('username'))['you']
            wallet = gaming.confirm_community_name(guest(), profile['display_name'], client_ip=g.client_ip)
            return jsonify(ok=True, wallet=wallet, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_name'))

    @app.post('/gaming/api/bet')
    def gaming_bet():
        require_player_csrf()
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or body.get('rules_version') not in SUPPORTED_VERSIONS:
            return json_error('Reload to use the current game rules.', 409, 'release_mismatch')
        try:
            result = gaming.bet(guest(), gaming_player_name(), body, client_ip=g.client_ip)
            return jsonify(**result, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_bet'))

    @app.post('/gaming/api/blackjack/action')
    def gaming_blackjack_action():
        require_player_csrf()
        body = request.get_json(silent=True)
        try:
            result = gaming.blackjack_action(guest(), gaming_player_name(),
                                             body, client_ip=g.client_ip)
            return jsonify(**result, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_move'))

    @app.post('/gaming/api/poker/action')
    def gaming_poker_action():
        require_player_csrf()
        try:
            result = gaming.poker_action(guest(), gaming_player_name(),
                                         request.get_json(silent=True), client_ip=g.client_ip)
            return jsonify(**result, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_move'))

    @app.get('/gaming/api/receipts')
    def gaming_receipts():
        # Owner's revealed receipts only. Active server seeds never leave storage.
        return Response(json.dumps(gaming_wallet()['receipts'], indent=2), mimetype='application/json',
                        headers={'Content-Disposition':'attachment; filename=redpoints-receipts.json'})

    @app.get('/admin/gaming')
    @protected
    def admin_gaming_page():
        return render_admin('gaming')

    @app.get('/admin/gaming/status')
    @protected
    def admin_gaming_status():
        response = jsonify(ok=True, **gaming.leaders(), release=RELEASE, visitor_ip_configured=not config.production or config.proxy)
        response.set_etag(token(response.get_json()))
        return response.make_conditional(request)

    @app.post('/admin/gaming/grant')
    @protected
    def admin_gaming_grant():
        require_csrf()
        body = request.get_json(silent=True) if request.is_json else request.form
        try:
            result = gaming.grant_everyone(body.get('request_id') if body else None, g.user)
            message = (f"{'Already granted' if result['duplicate'] else 'Granted'} +100,000 RedPoints "
                       f"to {result['players']:,} Gaming {'wallet' if result['players'] == 1 else 'wallets'}. Game winnings and records are unchanged.")
            if not result['players']:
                message = 'No Gaming wallets exist yet. Players receive 100,000 when they save their community name.'
            if wants_json():
                return jsonify(ok=True, **gaming.leaders(), grant=result, message=message,
                               next_request_id=secrets.token_hex(16), release=RELEASE)
            flash(message)
            return redirect(url_for('admin_gaming_page', _anchor='gamingFunding'), 303)
        except ValueError as exc:
            if wants_json():
                return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_grant'))
            return render_admin('gaming', errors={'gaming':str(exc)}, status=getattr(exc, 'status', 422))

    @app.get("/play")
    def play():
        return render_play()

    @app.get("/play/api/state")
    def boss_state():
        return jsonify(ok=True, state=boss.status(guest(), g.client_ip), csrf=csrf(),
                       player_csrf=player_csrf(), player_cookie_ready=not bool(getattr(g, 'new_guest', None)))

    def guard_key(identity, category):
        # Rejected requests belong to a signed browser, not every person behind
        # its proxy. One bad client must never lock a shared community network.
        return abuse.key(identity, '')

    def throttled(category, identity, alias):
        wait = abuse.retry_after(category, guard_key(identity, category))
        if not wait: return None
        response = jsonify(ok=False, code='request_throttle',
                           error=f'Too many rejected requests. Wait {wait} seconds, then try again.')
        response.headers['Retry-After'] = str(wait)
        return response, 429

    @app.post('/play/api/recovery-code')
    def boss_recovery_code():
        require_player_csrf()
        identity = guest()
        limited = throttled('registration', identity, '')
        if limited: return limited
        try:
            code = recovery_signer.dumps({'guest': identity, 'nonce': secrets.token_hex(16)})
            boss.save_recovery(identity, hashlib.sha256(code.encode()).hexdigest())
            return jsonify(ok=True, code=code, state=boss.status(identity, g.client_ip), csrf=csrf(), player_csrf=player_csrf())
        except BossError as exc:
            abuse.rejected('registration', guard_key(identity, 'registration'), 'Player setup')
            return json_error(str(exc), exc.status)

    @app.post('/play/api/recover')
    def boss_recover():
        require_player_csrf()
        identity = guest()
        limited = throttled('recovery', identity, '')
        if limited: return limited
        body = request.get_json(silent=True) or {}
        try:
            code = body.get('code', '') if isinstance(body, dict) else ''
            if not isinstance(code, str) or not 20 <= len(code) <= 512:
                raise BadSignature('Invalid recovery code')
            decoded = recovery_signer.loads(code)
            original = decoded.get('guest') if isinstance(decoded, dict) else None
            if not isinstance(original, str) or not re.fullmatch(r'[a-f0-9]{32}', original):
                raise BadSignature('Invalid recovery code')
            value = boss.recover_profile(original, g.client_ip, hashlib.sha256(code.encode()).hexdigest(), body.get('raid_id'))
            g.guest = g.new_guest = original
            return jsonify(ok=True, state=value, csrf=csrf(), player_csrf=player_csrf())
        except (BadSignature, BossError) as exc:
            abuse.rejected('recovery', guard_key(identity, 'recovery'), 'Profile recovery')
            return json_error('That recovery code is invalid or was replaced.' if isinstance(exc, BadSignature) else str(exc),
                              getattr(exc, 'status', 400))

    @app.post('/play/profile', endpoint='boss_profile_form')
    @app.post('/play/api/profile')
    def boss_profile():
        require_player_csrf()
        identity = guest()
        native = not wants_json()
        limited = throttled('registration', identity, '')
        if limited:
            if not native:
                return limited
            response, status = limited
            return render_play(name_error=response.get_json()['error'], name_draft=request.form.get('username', '')[:64]), status
        body = request.form if native else request.get_json(silent=True)
        if native:
            body = body.to_dict()
        if not isinstance(body, dict):
            abuse.rejected('registration', guard_key(identity, 'registration'), 'Player setup')
            return json_error('Send a valid username request.', 400)
        try:
            view = boss.register(identity, g.client_ip, body.get('raid_id'), body.get('username'))
            LOG.info('BOSS Player name saved; browser identity retained (%s).', RELEASE)
            if native:
                return redirect(url_for('play', saved='1', _anchor='yourTurn'), code=303)
            return jsonify(ok=True, state=view, csrf=csrf(), player_csrf=player_csrf())
        except (ValueError, BossError) as exc:
            abuse.rejected('registration', guard_key(identity, 'registration'), 'Player setup')
            status = getattr(exc, 'status', 422)
            LOG.warning('BOSS Player name rejected (%s); existing player was kept.', getattr(exc, 'code', 'invalid_name'))
            if native:
                return render_play(name_error=str(exc), name_draft=str(body.get('username', ''))[:64]), status
            response = jsonify(ok=False, error=str(exc), code=getattr(exc, 'code', 'invalid_name'), state=boss.status(identity, g.client_ip))
            if getattr(exc, 'retry_after', 0):
                response.headers['Retry-After'] = str(exc.retry_after)
            return response, status

    def boss_admin_view():
        value = boss.admin_status()
        value["abuse_flags"] = abuse.status()
        with runtime.lock:
            # This is a spelling match only. No provider IP mapping or account
            # ownership proof exists in the current Shuffle leaderboard contract.
            names = {r['username'].casefold() for r in runtime.shuffle['rows']}
        for row in value['admin_leaders']:
            row['shuffle_name_in_feed'] = row['name_provided'] and row['name'].casefold() in names
        return value

    @app.get('/admin/boss/status')
    @protected
    def boss_admin_state():
        return jsonify(ok=True, state=boss_admin_view(), csrf=csrf())

    @app.get('/play/avatar/<digest>.png')
    def boss_avatar_image(digest):
        if not re.fullmatch(r'[a-f0-9]{64}', digest):
            abort(404)
        data = boss.avatar_image(digest)
        if data is None:
            abort(404)
        response = Response(data, mimetype='image/png')
        response.set_etag(digest)
        return response.make_conditional(request)

    @app.get("/play/api/contributors")
    def boss_contributors():
        # Keep a host restart from mixing one raid's ID with another's recap.
        with boss.lock:
            current = boss.summary()
            if request.args.get("raid_id") != current["raid_id"] or current["status"] != "victory":
                return json_error("The victory recap belongs to a completed raid. Refresh to see the current raid.", 409)
            return jsonify(ok=True, raid_id=current["raid_id"], health_revision=current["health_revision"],
                           contributors=boss.contributors())

    @app.post("/play/api/attack")
    def boss_attack():
        require_player_csrf()
        identity = guest()
        body = request.get_json(silent=True)
        view = boss.status(identity, g.client_ip)
        valid_body = (isinstance(body, dict) and isinstance(body.get('style'), str)
                      and body['style'] in boss_rules()['styles'])
        receipt = body.get('request_id') if isinstance(body, dict) else None
        valid_body = valid_body and isinstance(receipt, str) and bool(re.fullmatch(r'[A-Za-z0-9_-]{8,64}', receipt)) and body.get('raid_id') == view['raid_id']
        retry = valid_body and receipt == view['you']['last_request']
        if not (valid_body and view['you']['can_attack']) and not retry:
            limited = throttled('attack', identity, view['you']['name'])
            if limited: return limited
        if not isinstance(body, dict):
            abuse.rejected('attack', guard_key(identity, 'attack'), view['you']['name'])
            return json_error("Send a valid attack request.", 400)
        try:
            return jsonify(boss.attack(identity, g.client_ip, body.get("style"), body.get("raid_id"), body.get("request_id"), require_profile=True))
        except BossError as exc:
            abuse.rejected('attack', guard_key(identity, 'attack'), view['you']['name'])
            response = jsonify(ok=False, error=str(exc), code=exc.code, state=boss.status(identity, g.client_ip))
            if exc.retry_after:
                response.headers["Retry-After"] = str(exc.retry_after)
            return response, exc.status

    @app.get("/data")
    def data():
        return jsonify(runtime.public())

    @app.get("/config")
    def public_config():
        return jsonify(runtime.public()["site"])

    @app.get("/stream")
    def stream():
        return jsonify(runtime.public()["stream"])

    @app.get("/healthz")
    def health():
        return jsonify(ok=True, release=RELEASE)

    @app.get("/readyz")
    def ready():
        check = runtime.store.readiness()
        return jsonify(ok=check['ok'], release=RELEASE, checked_at=check['checked_at']), 200 if check['ok'] else 503

    def recovery_status():
        with runtime.lock:
            return checkpoint_status(runtime.store.checkpoint(), runtime.admin, runtime.shuffle["rows"], boss.summary(), gaming.recovery())

    def render_admin(tab=None, draft=None, errors=None, confirm_race=False, restore=None, status=200,
                     change_review=None, review_token=None, recovery_review=None):
        if status >= 400 and wants_json():
            return json_error(' '.join((errors or {}).values()) or 'This change could not be saved.', status)
        tab = tab or request.args.get("tab", "overview")
        if tab not in TABS:
            tab = "overview"
        values = runtime.status()
        values['gaming'] = gaming.leaders()
        values['health'] = health_view(runtime, measurements, values)
        values["checkpoint"] = recovery_status() if g.superadmin else None
        visible = filtered(values["rows"], values["edits"], request.args)
        form = copy.deepcopy(g.admin["site_settings"])
        form.update(start_et=local_input(form["start_time"]), end_et=local_input(form["end_time"]))
        form.update({"prize_"+k: v for k, v in form["prizes"].items()})
        if draft:
            form.update(draft)
        receipt = session.pop('admin_receipt', None) if request.method == 'GET' else None
        if receipt and (receipt.get('user') != g.user or receipt.get('tab') != tab or time.time()-receipt.get('at', 0) > 120):
            receipt = None
        return render_template("admin.html", data=values, tab=tab, form=form, errors=errors or {},
                               revision=(draft or {}).get("revision", g.revision), admin=g.admin, user=g.user,
                               superadmin=g.superadmin, participants=visible, confirm_race=confirm_race, restore=restore,
                               access_log=list(access_log), defaults=DEFAULT_PRIZES, limit=config.limit,
                               boss_data=boss_admin_view() if tab == "boss" else None,
                               change_review=change_review, review_token=review_token,
                               recovery_review=recovery_review, admin_receipt=receipt,
                               gaming_grant_id=secrets.token_hex(16)), status

    def admin_saved(message, tab, target):
        """A receipt is created only after the state commit succeeds.

        JSON writes redirect once to the native page; invalid writes stay in the
        original form so the browser can retain drafts and selected upload files.
        Never save passwords or form bodies in a receipt or log.
        """
        session['admin_receipt'] = dict(message=message, user=g.user, tab=tab,
                                        target=target, at=int(time.time()))
        destination = url_for('login', tab=tab, _anchor='feedback-'+target)
        if wants_json():
            return jsonify(ok=True, message=message, redirect=destination, release=RELEASE)
        return redirect(destination, 303)

    @app.post("/admin/boss/action")
    @protected
    def boss_control():
        # g.user is populated only from a current administrator account and its
        # auth_version, never from a guest cookie or a client-supplied role flag.
        # Keep every boss configuration write behind this guard, including image decoding.
        require_csrf()
        try:
            action = request.form.get("action", "")
            if action == "restart" and request.form.get("confirm_restart") != "yes":
                raise ValueError("Confirm that you want to archive the current raid and start a new one.")
            if action in {'health', 'remaining_health'} and request.form.get('confirm_health') != 'yes':
                raise ValueError('Confirm that you want to change this raid\'s health.')
            if action in {'avatar', 'avatar_reset'}:
                boss.set_avatar(request.form.get('raid_id'), from_upload(request.files.get('avatar')) if action == 'avatar' else None, actor=g.user)
            elif action == 'release_player':
                if request.form.get('confirm_release') != 'yes':
                    raise ValueError('Confirm the connection release.')
                boss.release_profile(request.form.get('raid_id'), request.form.get('player_name'), actor=g.user)
            elif action == 'household':
                boss.household(request.form.get('raid_id'), request.form.get('player_name'), int(request.form.get('slots', '')), actor=g.user)
            elif action == 'settings':
                try:
                    values = dict(name=request.form.get('boss_name', ''),
                                  damage=int(request.form.get('base_damage', '')),
                                  weak_damage=int(request.form.get('weak_damage', '')),
                                  burst_bonus=int(request.form.get('burst_bonus', '')))
                    settings_revision = int(request.form.get('settings_revision', '-1'))
                except ValueError:
                    raise ValueError('Enter whole numbers for damage and reload if this form is out of date.') from None
                boss.configure(request.form.get('raid_id'), values, settings_revision, actor=g.user)
            else:
                boss.control(action, request.form.get("raid_id"), int(request.form.get("health", DEFAULT_HP)),
                             health_revision=int(request.form.get('health_revision', '-1')) if action in {'health', 'remaining_health'} else None, actor=g.user)
            message = {'restart':'New community raid is ready.', 'pause':'Community raid paused.', 'resume':'Community raid resumed.',
                   'health':'Maximum HP updated. Saved damage and cooldowns were kept.',
                   'remaining_health':'Remaining HP updated. Saved damage and cooldowns were kept.',
                   'household':'Shared connection allowance saved. Each approved player keeps a 30-second cooldown.',
                   'release_player':'Connection released. The original browser retains its name and achievements.',
                   'settings':'Boss name and damage settings saved. New damage values apply to future hits.',
                   'avatar':'Boss avatar updated.', 'avatar_reset':'Original boss avatar restored.'}[action]
            saved = boss.summary()
            if action in {'health', 'remaining_health', 'restart'}:
                message += f" Remaining HP: {saved['hp']:,}; maximum HP: {saved['max_hp']:,}."
            elif action == 'settings':
                message += f" Name: {values['name']}; base: {values['damage']:,}; weakness: {values['weak_damage']:,}; burst: {values['burst_bonus']:,}."
            LOG.info('BOSS Admin action %s accepted for account %r.', action, g.user)
            target = {'avatar':'avatarHeading', 'avatar_reset':'avatarHeading', 'health':'healthHeading',
                      'remaining_health':'healthHeading', 'settings':'bossSettingsHeading', 'restart':'bossRestart'}.get(action, 'bossControls')
            return admin_saved(message, 'boss', target)
        except ValueError as exc:
            return render_admin("boss", errors={"boss":str(exc)}, status=422)

    @app.route("/admin", methods=["GET", "POST"])
    @app.route("/admin/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_admin() if g.user else render_template("login.html", error="")
        require_csrf()
        name, password = request.form.get("username", "").strip()[:64], request.form.get("password", "")
        key = g.client_ip or request.remote_addr or "unknown"
        with auth_lock:
            cutoff = time.monotonic() - 600
            for ip in list(failures):
                failures[ip] = [t for t in failures[ip] if t > cutoff]
                if not failures[ip]:
                    del failures[ip]
            if len(failures) >= 2000 and key not in failures:
                return render_template("login.html", error="Too many sign-in attempts. Please try again later."), 429
            if len(failures.get(key, [])) >= 5:
                return render_template("login.html", error="Too many sign-in attempts. Wait ten minutes and try again."), 429
            failures.setdefault(key, []).append(time.monotonic())
        canonical, record = account(g.admin["users"], name)
        valid = check_password_hash(record["pw_hash"] if record else dummy_hash, password[:256])
        if not valid or not canonical or len(password) > 256:
            return render_template("login.html", error="The username or password is incorrect."), 401
        with auth_lock:
            failures.pop(key, None)
        session.clear()
        session.update(user=canonical, auth_version=record.get("auth_version", 1), csrf=secrets.token_urlsafe(32))
        session.permanent = True
        LOG.info("ADMIN Sign-in successful.")
        return redirect(url_for("login", tab="overview"), 303)

    @app.post("/admin/logout")
    def logout():
        require_csrf()
        session.clear()
        return redirect(url_for("login"), 303)

    @app.get("/admin/status")
    @protected
    def status():
        value = runtime.status()
        value['gaming'] = gaming.leaders()
        value['health'] = health_view(runtime, measurements, value)
        value["checkpoint"] = recovery_status() if g.superadmin else None
        rows, edits = value.pop("rows"), value.pop("edits")
        # Other tabs have no participant table; keep their minute responses small.
        if request.args.get("tab", "players") == "players":
            value["participants"] = filtered(rows, edits, request.args)
        if request.args.get("code_red") != "1":
            value.pop("red", None)
        return jsonify(value)

    @app.get("/admin/diagnostics")
    @protected
    def diagnostics():
        value = runtime.status()
        safe = dict(diagnostics=value["diagnostics"], jobs=value["jobs"], freshness=value["freshness"],
                    history=value['history'], generated_at=int(time.time()))
        return Response(json.dumps(safe, indent=2), mimetype="application/json",
                        headers={"Content-Disposition":"attachment; filename=redhunllef-diagnostics.json"})

    @app.get('/admin/health-report')
    @protected
    def health_report():
        # All fields are chosen by health_view. Never dump runtime/state objects.
        return jsonify(health_view(runtime, measurements, runtime.status()))

    def safe_backup():
        with runtime.lock:
            saved, current = runtime.shuffle, runtime.admin
            return dict(backup_version=3, generated_at=int(time.time()), site_settings=copy.deepcopy(current["site_settings"]),
                        overrides=copy.deepcopy(current["overrides"]), race_history=copy.deepcopy(current["race_history"]),
                        leaderboard_snapshots=dict(race_key=saved["key"], last_top15=copy.deepcopy(saved["rows"][:15]),
                                                   prev_top15=copy.deepcopy(saved.get("previous_top", [])), updated_at=saved["updated_at"]))

    @app.get("/admin/backup")
    @protected
    def backup():
        return Response(json.dumps(safe_backup(), indent=2), mimetype="application/json",
                        headers={"Content-Disposition":"attachment; filename=redhunllef-race-backup.json"})

    @app.get("/admin/recovery-backup")
    @protected
    def recovery_backup():
        # A full account export is private to the Superadmin. It uses the same
        # validated seed format as startup and is never part of public feeds.
        if not g.superadmin:
            abort(403, description="Only the Superadmin can download private account recovery files.")
        # One transaction captures accounts, game stakes and receipts at the same
        # instant. Separate reads could otherwise straddle a settling game.
        with runtime.lock, runtime.store.connection(transaction=True) as conn:
            value = copy.deepcopy(conn['admin'])
            saved = conn['live']['shuffle']
            value['leaderboard_snapshots'] = dict(race_key=saved['key'], last_top15=copy.deepcopy(saved['rows'][:15]),
                prev_top15=copy.deepcopy(saved.get('previous_top', [])), updated_at=saved['updated_at'])
            value['community_boss'] = copy.deepcopy(conn['boss'])
            value['community_boss_avatar'] = copy.deepcopy(conn.get('avatar'))
            value['weekly_history'] = copy.deepcopy(conn['live'].get('weekly_history'))
            value['redpoints'] = copy.deepcopy(conn.get('gaming'))
            marker = export_marker(conn['admin'], value["leaderboard_snapshots"], value["community_boss"], int(time.time()), value["redpoints"])
            value["recovery_export"] = marker
            conn['checkpoint'] = marker
        return Response(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), mimetype="application/json",
                        headers={"Content-Disposition":"attachment; filename=recovery.seed.json"})

    @app.post("/admin/recovery-preview")
    @protected
    def recovery_preview():
        require_csrf()
        if not g.superadmin:
            abort(403)
        try:
            upload = request.files.get("recovery")
            if not upload:
                raise ValueError("Choose a private recovery JSON file.")
            value, _ = upgrade_store(json.load(upload), config.site, {})
            if not value["users"]:
                raise ValueError("The recovery file contains no administrator accounts.")
            game = validate_boss(value["community_boss"]) if value.get("community_boss") is not None else None
            avatar = validate_avatar(value.get('community_boss_avatar'))
            redpoints = validate_gaming(value.get('redpoints'))
            review = dict(accounts=len(value["users"]), overrides=len(value["overrides"]),
                          history=len(value["race_history"]), rows=len(value["leaderboard_snapshots"]["last_top15"]),
                          start=fmt_et(value["site_settings"]["start_time"]), end=fmt_et(value["site_settings"]["end_time"]),
                          game=game and dict(hp=game["hp"], max_hp=game["max_hp"], raiders=len(game["players"]), attacks=game["total_attacks"]),
                          avatar=bool(avatar), redpoints=len(redpoints['players']) if redpoints else 0)
            with runtime.store.connection() as conn:
                old_players = (conn.get('gaming') or {}).get('players', {})
                new_players = (redpoints or {}).get('players', {})
                review['comparison'] = dict(
                    accounts_before=len(conn['admin']['users']), wallets_before=len(old_players),
                    accounts_added=sorted(set(value['users'])-set(conn['admin']['users'])),
                    accounts_removed=sorted(set(conn['admin']['users'])-set(value['users'])),
                    accounts_changed=sum(conn['admin']['users'][key] != value['users'][key]
                                         for key in set(value['users']) & set(conn['admin']['users'])),
                    wallets_added=len(set(new_players)-set(old_players)),
                    wallets_removed=len(set(old_players)-set(new_players)),
                    wallets_changed=sum(old_players[key] != new_players[key] for key in set(new_players)&set(old_players)),
                    pending_before=sum(bool(p.get('poker') or p.get('blackjack')) for p in old_players.values()),
                    pending_after=sum(bool(p.get('poker') or p.get('blackjack')) for p in new_players.values()))
            return render_admin("settings", recovery_review=review)
        except (ValueError, RuntimeError, UnicodeDecodeError) as exc:
            return render_admin("settings", errors={"recovery":str(exc)}, status=422)

    @app.get("/admin/export.csv")
    @protected
    def export():
        value = runtime.status()
        rows = filtered(value["rows"], value["edits"], request.args)
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(["rank", "username", "weighted_wager", "original_weighted_wager", "raw_wager", "prize", "source", "last_source_update_et", "data_state"])
        for row in rows:
            writer.writerow([row["rank"] or "", csv_text(row["username"]), row["weighted_wager"], row["original_weighted_wager"],
                             row["raw_wager"], value["site"]["prizes"].get(str(row["rank"]), ""), row["source"],
                             fmt_et(value["freshness"]["updated_at"]), value["freshness"]["state"]])
        return Response("\ufeff" + output.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition":"attachment; filename=redhunllef-" + value["freshness"]["state"] + ".csv"})

    def validate_backup(upload):
        try:
            value = json.load(upload)
        except (ValueError, UnicodeDecodeError):
            raise ValueError("Choose a valid JSON backup.") from None
        if not isinstance(value, dict) or value.get("backup_version") not in {1, 2, 3}:
            raise ValueError("This backup version is not supported.")
        if not isinstance(value.get("site_settings"), dict):
            raise ValueError("The backup has no valid race settings.")
        site = canonical_site(value["site_settings"], config.site)
        if validate_site(site):
            raise ValueError("The backup contains invalid dates, prizes, or links.")
        overrides = clean_overrides(value.get("overrides", {}))
        snapshots = clean_snapshots(value.get("leaderboard_snapshots", {}), race_key(site))
        history = value.get("race_history", [])
        if not isinstance(history, list):
            raise ValueError("Race history must be a list.")
        for entry in history:
            if not isinstance(entry, dict) or not isinstance(entry.get("site_settings"), dict):
                raise ValueError("An archived race is invalid.")
            old_site = canonical_site(entry["site_settings"], config.site)
            if validate_site(old_site):
                raise ValueError("An archived race has invalid settings.")
            clean_overrides(entry.get("overrides", {}))
            clean_snapshots(entry.get("leaderboard_snapshots", {}), race_key(old_site))
        return dict(site_settings=site, overrides=overrides, leaderboard_snapshots=snapshots, race_history=history)

    @app.post("/admin/action")
    @protected
    def action():
        require_csrf()
        action_name, tab = request.form.get("action"), request.form.get("tab", "overview")
        if action_name == "refresh":
            name = request.form.get("service") or None
            if name not in {None, "shuffle", "kick"}:
                abort(400)
            receipt = runtime.request_refresh(name)
            LOG.info("REFRESH Check requested for %s; provider retry delays still apply.", name or "Shuffle and Kick")
            if wants_json():
                return jsonify(ok=True, message="Refresh queued. Its progress and result appear below.",
                               **receipt, jobs=runtime.job_status()), 202
            flash("Check requested. Results update automatically.")
            return redirect(url_for("login", tab=tab), 303)
        try:
            expected = int(request.form.get("revision", "0"))
            if expected != g.revision:
                raise Conflict("Another administrator changed saved settings. Reload and review your edits.")
            candidate, snapshot, reason, detail = copy.deepcopy(g.admin), None, None, "Changes saved."
            if action_name == "save_race":
                site = copy.deepcopy(candidate["site_settings"])
                site.update({k: request.form.get(k, "").strip() for k in (*TEXT_LIMITS, *URL_FIELDS, "kick_channel_slug")})
                errors = {}
                for key in ("start", "end"):
                    try:
                        site[key + "_time"] = eastern_epoch(request.form.get(key + "_et"))
                    except ValueError as exc:
                        errors[key + "_et"] = str(exc)
                site["prizes"] = {str(n): request.form.get("prize_" + str(n), "") for n in range(1, 16)}
                errors.update(validate_site(site))
                if errors:
                    return render_admin("race", dict(request.form), errors, status=422)
                site["prizes"] = {k: str(money_input(v)) for k, v in site["prizes"].items()}
                changed_race = race_key(site) != race_key(candidate["site_settings"])
                review = changes(candidate["site_settings"], site)
                expected_review = dict(user=g.user, revision=expected, site=site)
                try:
                    confirmed = request.form.get("confirm_race") == "yes" and review_signer.loads(request.form.get("review_token", ""), max_age=900) == expected_review
                except BadSignature:
                    confirmed = False
                if review and not confirmed:
                    return render_admin("race", dict(request.form), confirm_race=True, change_review=review,
                                        review_token=review_signer.dumps(expected_review))
                if changed_race:
                    old = safe_backup()
                    if candidate["site_settings"]["start_time"]:
                        candidate["race_history"].append({k: old[k] for k in ("site_settings", "overrides", "leaderboard_snapshots")} | {"archived_at":int(time.time())})
                    candidate["overrides"], reason = {}, "before-race-change"
                candidate["site_settings"] = site
                snapshot = empty(site) if changed_race else calculate(runtime.shuffle, candidate, config)
                detail = "Race published. A fresh check is queued for the saved dates; watch its progress below."
            elif action_name == "override":
                name, amount = request.form.get("username", "").strip(), request.form.get("amount", "").strip()
                if not name or len(name) > 64:
                    raise ValueError("Enter the exact full username, up to 64 characters.")
                if amount:
                    candidate["overrides"][name] = str(money_input(amount))
                else:
                    candidate["overrides"].pop(name, None)
                snapshot = calculate(runtime.shuffle, candidate, config)
                detail = f"Override saved for {name}: {money(candidate['overrides'][name])}." if amount else f"Override removed for {name}; source weighting restored."
            elif action_name in {"add_account", "remove_account", "reset_password", "password"}:
                if action_name != "password" and not g.superadmin:
                    abort(403)
                name = request.form.get("username", "").strip() if action_name != "password" else g.user
                canonical, record = account(candidate["users"], name)
                if action_name == "remove_account":
                    if not canonical or canonical.casefold() == candidate.get("superadmin", config.superadmin).casefold():
                        raise ValueError("The protected Superadmin account cannot be removed.")
                    del candidate["users"][canonical]
                    reason = "before-account-removal"
                else:
                    password = request.form.get("new_password", "")
                    if not 12 <= len(password) <= 256 or password != request.form.get("confirm_password"):
                        raise ValueError("Use matching passwords with 12–256 characters.")
                    if action_name == "add_account":
                        if canonical or not re.fullmatch(r"[A-Za-z0-9_]{3,32}", name):
                            raise ValueError("Choose an unused username with 3–32 letters, numbers, or underscores.")
                        canonical, record = name, dict(auth_version=0, created_at=int(time.time()))
                    elif not record:
                        raise ValueError("That account does not exist.")
                    if action_name == "password" and not check_password_hash(record["pw_hash"], request.form.get("current_password", "")[:256]):
                        raise ValueError("The current password is incorrect.")
                    record.update(pw_hash=generate_password_hash(password), auth_version=record.get("auth_version", 1) + 1)
                    candidate["users"][canonical] = record
                    reason = "before-password-change" if action_name != "add_account" else None
                detail = f"Account updated: {name}. Removed or reset accounts lose their previous sessions."
            elif action_name == "preview_restore":
                upload = request.files.get("backup")
                if not upload:
                    raise ValueError("Choose a backup file.")
                value = validate_backup(upload)
                identifier = secrets.token_urlsafe(32)
                with auth_lock:
                    for key in list(previews):
                        if previews[key]["expires"] < time.time():
                            del previews[key]
                    if len(previews) >= 20:
                        raise ValueError("Too many pending restores. Wait ten minutes and try again.")
                    previews[identifier] = dict(value=value, user=g.user, expires=time.time()+600, revision=expected)
                return render_admin("settings", restore=dict(token=identifier, start=fmt_et(value["site_settings"]["start_time"]),
                                    end=fmt_et(value["site_settings"]["end_time"]), rows=len(value["leaderboard_snapshots"]["last_top15"]),
                                    overrides=len(value["overrides"]), history=len(value["race_history"]),
                                    changes=changes(g.admin["site_settings"], value["site_settings"])))
            elif action_name == "restore":
                with auth_lock:
                    preview = previews.get(request.form.get("restore_token"))
                    if not preview or preview["expires"] < time.time() or preview["user"] != g.user or preview["revision"] != expected:
                        raise ValueError("Restore preview expired or settings changed. Review the backup again.")
                    value = copy.deepcopy(preview["value"])
                candidate.update({k: value[k] for k in ("site_settings", "overrides", "race_history")})
                saved = value["leaderboard_snapshots"]
                snapshot = empty(candidate["site_settings"])
                snapshot.update(rows=saved["last_top15"], previous_top=saved["prev_top15"], updated_at=saved["updated_at"] or 0,
                                count=len(saved["last_top15"]), snapshot_only=bool(saved["last_top15"]),
                                source=[dict(username=r["username"], weighted=r["original_weighted_wager"], raw=r["raw_wager"], row_count=r["row_count"]) for r in saved["last_top15"]])
                reason, detail = "before-restore", "Backup restored. Accounts preserved; a private recovery copy was saved."
            elif action_name in {"ban_ip", "unban_ip"}:
                ip = str(ipaddress.ip_address(request.form.get("ip", "")))
                if action_name == "ban_ip" and ip == g.client_ip:
                    raise ValueError("You cannot block the address you are using.")
                candidate["banned_ips"] = sorted(set(candidate["banned_ips"]) | {ip}) if action_name == "ban_ip" else [x for x in candidate["banned_ips"] if x != ip]
            elif action_name == "clear_audit":
                if not g.superadmin:
                    abort(403)
                candidate["audit_log"], reason = [], "before-clearing-audit"
            elif action_name == "clear_access":
                with auth_lock:
                    access_log.clear()
            else:
                raise ValueError("This action is not supported.")
            candidate["updated_at"] = int(time.time())
            candidate["audit_log"].append(dict(ts_et=fmt_et(candidate["updated_at"]), admin_user=g.user, action=action_name, detail=detail))
            candidate["audit_log"] = candidate["audit_log"][-250:]
            runtime.commit(candidate, expected, snapshot=snapshot, reason=reason)
            if action_name in {"password", "reset_password"}:
                _, current = account(candidate["users"], g.user)
                session["auth_version"] = current["auth_version"]
            if action_name in {"save_race", "restore"}:
                runtime.request_refresh()
                LOG.info("RACE Published revision %s: %s -> %s; fresh provider checks queued.", runtime.revision,
                         fmt_et(candidate["site_settings"]["start_time"]), fmt_et(candidate["site_settings"]["end_time"]))
            LOG.info("ADMIN %s completed.", action_name)
            if action_name == 'save_race':
                detail = f"Race saved: {candidate['site_settings']['race_title']}. {fmt_et(site['start_time'])} → {fmt_et(site['end_time'])}. Fresh source check queued."
            target = {'save_race':'raceForm', 'override':'override', 'password':'accountSecurity',
                      'add_account':'accounts', 'remove_account':'accounts', 'reset_password':'accounts',
                      'restore':'backups'}.get(action_name, 'accessControls')
            return admin_saved(detail, tab if tab in TABS else 'overview', target)
        except (ValueError, Conflict) as exc:
            return render_admin(tab, dict(request.form) if tab == "race" else None,
                                errors={"form":str(exc)}, status=409 if isinstance(exc, Conflict) else 422)

    return app


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        from release_check import check_release
        checked = check_release(strict='--check' in sys.argv)
        if not checked['ok']:
            raise RuntimeError('Release check failed: '+'; '.join(checked['problems']))
        for warning in checked['warnings']:
            LOG.warning('RELEASE %s', warning)
        if '--check' in sys.argv:
            LOG.info('RELEASE Checked %s Python modules and %s templates. No accounts or game state changed.', checked['python_modules'], checked['templates'])
            return 0
        app = create_app()
        config, runtime = app.extensions["settings"], app.extensions["runtime"]
        from waitress import create_server
        options = dict(host="0.0.0.0", port=config.port, threads=6, ident="RedHunllef", expose_tracebacks=False,
                       max_request_body_size=64*1024*1024, channel_timeout=60, clear_untrusted_proxy_headers=True)
        if config.proxy:
            # App Platform is the only trusted ingress. Do not enable this on
            # a directly exposed host. Waitress applies proxy interpretation once.
            options.update(trusted_proxy="*", trusted_proxy_count=1,
                           trusted_proxy_headers={"x-forwarded-proto", "x-forwarded-for"})
        server = create_server(app, **options)
        LOG.info("START RedHunllef %s listening on 0.0.0.0:%s; storage=%s.", RELEASE, config.port, "local JSON")
        LOG.info('HEALTH /healthz checks the process; /readyz checks local reads and writes. Provider delays appear separately in Admin Overview.')
        LOG.info("BOSS Shared raid at /play; screens update every 5s, attacks every 30s, no daily cap. Identity and cooldowns follow signed browser cookies, never shared IPs. Names are self-reported; public feeds stay anonymous. Host controls: /admin?tab=boss.")
        if not runtime.store.pg:
            LOG.info("STORAGE Local file ready; no external database is required.")
            if config.production:
                LOG.warning("STORAGE On App Platform, local changes are lost on redeploy/container replacement. Download the private recovery file from Settings after important changes.")
        for key, details in config.diagnostics().items():
            LOG.info("CONFIG %s: %s (%s).", key, "configured" if details["configured"] else "missing", details["source"])
        LOG.info("RACE Saved window: %s → %s. State=%s.", fmt_et(runtime.admin["site_settings"]["start_time"]),
                 fmt_et(runtime.admin["site_settings"]["end_time"]), phase(runtime.admin["site_settings"]))
        def shutdown(*_):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, shutdown)
        runtime.start()
        try:
            server.run()
        finally:
            runtime.stop()
            server.close()
            runtime.store.close()
        return 0
    except KeyboardInterrupt:
        return 0
    except (StoreError, ValueError, RuntimeError) as exc:
        LOG.error("STARTUP %s", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
