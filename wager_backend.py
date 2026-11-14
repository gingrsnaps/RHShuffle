"""RedHunllef's sole launch command: python wager_backend.py.

App construction has no provider requests or hidden worker startup. The main
function binds one production server, then starts the two automatic jobs once.
"""
from collections import deque
import copy
import csv
from datetime import datetime, timezone, timedelta
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
from empiredrop import validate_settings, EDITABLE, schedule as empire_schedule, CODE as EMPIRE_CODE
from empiredrop_races import RACE_EDITABLE, validate_race_settings
from empiredrop_features import validate_rewards, rewards_public
from operations_log import ActivityLog
from provider_admin import summarize_providers
from integrations import ProviderError
from telemetry import Measurements, health_view
from admin_navigation import admin_link, ADMIN_TABS, ADMIN_SECTION_ALIASES

LOG = logging.getLogger("redhunllef")
TABS = {"overview":"Overview", "shuffle":"Shuffle standings", "race":"Shuffle schedule", "players":"Shuffle players", "empiredrop":"EmpireDrop", "gaming":"Games & RedPoints", "activity":"Activity & logs", "settings":"Settings"}
if frozenset(TABS) != ADMIN_TABS:
    raise RuntimeError("Admin navigation and rendered tabs disagree")


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
    activity = app.extensions["activity"] = ActivityLog()
    runtime.empiredrop.events = activity
    runtime.activity_log = activity

    def safe_activity(*args, **kwargs):
        """Operational logging must never turn a completed admin write into HTTP 500."""
        try:
            return activity.record(*args, **kwargs)
        except Exception:
            # Arguments are deliberately not logged because they may come from
            # future call sites that contain private operational context.
            LOG.exception('ACTIVITY A structured event could not be recorded.')
            return None
    app.extensions["settings"] = config
    measurements = app.extensions['measurements'] = Measurements()
    gaming = app.extensions['gaming'] = Gaming(runtime.store)
    # One launch restores playable points for everyone, without clearing results.
    # Page requests and automatic status checks never run this bulk reset.
    gaming.restart_balances()
    player_signer = URLSafeTimedSerializer(app.secret_key, salt="redpoints-player-v1")
    legacy_player_signer = URLSafeTimedSerializer(app.secret_key, salt="community-boss-guest-v1")
    recovery_signer = URLSafeSerializer(app.secret_key, salt="redpoints-recovery-v1")
    legacy_recovery_signer = URLSafeSerializer(app.secret_key, salt="community-boss-recovery-v1")
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
        return request.path.startswith("/gaming/api/") or request.accept_mimetypes.best == "application/json" or request.path in {
            "/data", "/public-state", "/history-state", "/config", "/stream", "/admin/status", "/admin/gaming/status", "/admin/empiredrop/status", "/admin/diagnostics", "/admin/health-report", "/admin/operations/events", "/admin/operations/export", "/healthz", "/readyz"
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
                # A complete private recovery export can exceed an ordinary form. Only authenticated Superadmins get this larger limit.
                request.max_content_length = 64 * 1024 * 1024
        if request.path not in {"/healthz", "/readyz"} and g.client_ip in runtime.admin.get("banned_ips", []):
            abort(403, description="Access from this address has been disabled.")

    @app.after_request
    def after(response):
        response.headers['X-Request-ID'] = getattr(g, 'request_id', '')
        if request.path.startswith('/admin'):
            # Admin HTML includes version-specific navigation and private data.
            # Stale CDN/browser HTML caused links to outlive their route version.
            response.headers['Cache-Control'] = 'private, no-store, max-age=0'

        elapsed = (time.perf_counter()-g.began)*1000
        if request.endpoint not in {'static', 'health', 'ready'}:
            measurements.request(request.endpoint, response.status_code, elapsed)
        if response.status_code >= 500:
            safe_activity('system','error','server_error',http_status=response.status_code,
                            duration_ms=round(elapsed))
            LOG.error('REQUEST id=%s route=%s status=%s elapsed_ms=%.1f',
                      g.request_id, request.endpoint or 'unmatched', response.status_code, elapsed)
        response.headers.update({"X-Content-Type-Options":"nosniff", "X-Frame-Options":"DENY",
            "Referrer-Policy":"strict-origin-when-cross-origin", "X-RedHunllef-Release":RELEASE,
            "Content-Security-Policy":"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
            "Cache-Control":"public, max-age=31536000, immutable" if request.path.startswith("/static/") and request.args.get("v") == assets else "no-store"})
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        if request.path in {"/public-state", "/gaming/api/public-leaderboard"} and response.status_code in {200, 304}:
            response.headers["Cache-Control"] = "public, no-cache"
        if request.path.startswith("/admin"):
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        if getattr(g, "new_guest", None):
            response.set_cookie("rh_player", player_signer.dumps(g.new_guest), max_age=365*86400,
                                secure=app.session_interface.get_cookie_secure(app), httponly=True, samesite="Lax")
            if request.cookies.get("rh_raider"):
                response.delete_cookie("rh_raider", secure=app.session_interface.get_cookie_secure(app), samesite="Lax")
        if request.path not in {"/data", "/public-state", "/history-state", "/config", "/stream", "/admin/status", "/healthz", "/readyz"} and not request.path.startswith(("/static/", "/gaming/api/")):
            with auth_lock:
                access_log.appendleft(dict(time=int(time.time()), method=request.method, path=request.path[:120], status=response.status_code,
                                           ip=g.client_ip, ms=round((time.perf_counter()-g.began)*1000)))
        return response

    @app.context_processor
    def context():
        return dict(release=RELEASE, asset_version=assets, csrf=csrf, money=money, fmt_et=fmt_et,
                    admin_link=admin_link,
                    local_input=local_input, tabs=TABS, weighting=WEIGHTING_RULES,
                    local_storage=not runtime.store.pg, hosted_local=config.production and not runtime.store.mirror)

    @app.errorhandler(StoreError)
    def storage_error(error):
        LOG.error("STORAGE %s", str(error))
        if wants_json():
            return json_error(str(error), 503)
        return render_template("error.html", title="Connection interrupted", message=str(error)), 503

    @app.errorhandler(HTTPException)
    def page_error(error):
        # A safe route hint makes 404s actionable without logging query strings,
        # API credentials, usernames, private IDs or arbitrary client path data.
        if error.code == 404:
            known_prefix = next((prefix for prefix in ("/admin", "/gaming", "/history", "/static")
                                 if request.path == prefix or request.path.startswith(prefix + "/")), None)
            safe_path = request.path[:100] if known_prefix and re.fullmatch(r"/[A-Za-z0-9/_-]+", request.path) else "unknown-route"
            LOG.warning("HTTP 404 method=%s path=%s request=%s (unregistered destination)",
                        request.method, safe_path, g.request_id)
        else:
            LOG.warning("HTTP %s %s returned %s (%s).", request.method, request.endpoint or "unmatched route", error.code, error.name)
        if wants_json():
            return json_error(error.description, error.code, getattr(error, 'problem_code', None))
        return render_template("error.html", title="Page unavailable" if error.code == 404 else "Request could not be completed",
                               message=error.description), error.code

    @app.errorhandler(500)
    def internal_error(error):
        original = getattr(error, 'original_exception', None)
        if original is not None:
            LOG.error('REQUEST id=%s endpoint=%s failed with %s.',
                      getattr(g, 'request_id', 'unknown'), request.endpoint or 'unmatched',
                      type(original).__name__,
                      exc_info=(type(original), original, original.__traceback__))
        else:
            LOG.error('REQUEST id=%s endpoint=%s returned HTTP 500.',
                      getattr(g, 'request_id', 'unknown'), request.endpoint or 'unmatched')
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
        return runtime.public()

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
        """Return the signed Gaming identity, migrating the retired player cookie."""
        if not hasattr(g, "guest"):
            value = None
            try:
                value = player_signer.loads(request.cookies.get("rh_player", ""), max_age=365*86400)
            except BadSignature:
                try:
                    value = legacy_player_signer.loads(request.cookies.get("rh_raider", ""), max_age=365*86400)
                    g.new_guest = value  # Reissue under the new cookie/salt.
                except BadSignature:
                    value = g.new_guest = secrets.token_hex(16)
            if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{32}", value):
                value = g.new_guest = secrets.token_hex(16)
            g.guest = value
        return g.guest

    def player_csrf():
        """Bind game writes to the signed player independently of admin login."""
        secret = app.secret_key.encode() if isinstance(app.secret_key, str) else app.secret_key
        return hmac.new(secret, ('redpoints-write-v1:' + guest()).encode(), hashlib.sha256).hexdigest()

    def require_player_csrf():
        guest()
        if getattr(g, 'new_guest', None) and not request.cookies.get(('rh_player')) and not request.cookies.get('rh_raider'):
            failure = BadRequest(description='Your browser did not return the player cookie. Open the game directly on its HTTPS site, allow site cookies, then reload. Use http://localhost:8080 for local testing.')
            failure.problem_code = 'player_cookie_required'
            raise failure
        supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf', '')
        if isinstance(supplied, str) and supplied.isascii() and hmac.compare_digest(supplied, player_csrf()):
            return
        try:
            require_csrf()
        except BadRequest as failure:
            failure.problem_code = 'csrf_expired'
            raise

    def gaming_wallet():
        return gaming.view(guest(), '', client_ip=g.client_ip)

    def gaming_player_name():
        wallet = gaming_wallet()
        if wallet.get('play_blocked'):
            issue = wallet['play_blocked']
            raise GamingError(issue['message'], issue['code'], 409)
        if wallet['needs_profile']:
            raise GamingError('Save your Gaming name before playing.', 'community_name_required', 409)
        return wallet['name']

    @app.get('/gaming')
    def gaming_home():
        return render_template('gaming.html', data=runtime.public(), wallet=gaming_wallet(),
                               community=gaming.public_leaderboard(),
                               game=None, game_rules=gaming_rules(), player_token=player_csrf())

    @app.get('/gaming/fairness')
    def gaming_fairness():
        return render_template('gaming_fairness.html', data=runtime.public())

    @app.get('/gaming/<game>')
    def gaming_game(game):
        if game not in GAMES: abort(404)
        return render_template('gaming.html', data=runtime.public(), wallet=gaming_wallet(),
                               community=gaming.public_leaderboard(),
                               game=game, game_rules=gaming_rules(), player_token=player_csrf())

    @app.get('/gaming/api/state')
    def gaming_state():
        # The Gaming page uses one five-second request for its private wallet and
        # the sanitized public community board. This avoids duplicate polling.
        value = dict(ok=True, wallet=gaming_wallet(), community=gaming.public_leaderboard(),
                     player_csrf=player_csrf(), release=RELEASE)
        response = jsonify(value)
        response.set_etag(token(value))
        return response.make_conditional(request)

    @app.get('/gaming/api/public-leaderboard')
    def gaming_public_leaderboard():
        # Public allowlist only: no wallet IDs, balances, IPs, seeds, receipts,
        # recovery data or admin funding adjustments.
        value = dict(ok=True, **gaming.public_leaderboard(), release=RELEASE)
        response = jsonify(value)
        response.set_etag(token(value))
        response.headers['Cache-Control'] = 'public, no-cache'
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
        if not isinstance(body, dict):
            return json_error('Enter a valid player name.', 422)
        try:
            visibility = body.get('public_visibility')
            # Compatibility for an old cached Gaming asset during a rolling
            # deployment: preserve the existing choice when the field is absent.
            if visibility is None:
                visibility = bool(gaming_wallet().get('public_visibility', False))
            if type(visibility) is not bool:
                return json_error('Choose whether your Gaming name appears publicly.', 422, 'invalid_visibility')
            wallet = gaming.confirm_community_name(guest(), body.get('username'), visibility, client_ip=g.client_ip)
            return jsonify(ok=True, wallet=wallet, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_name'))

    @app.post('/gaming/api/recovery-code')
    def gaming_recovery_code():
        require_player_csrf()
        identity = guest()
        try:
            code = recovery_signer.dumps({'player': identity, 'nonce': secrets.token_hex(16)})
            wallet = gaming.save_recovery(identity, hashlib.sha256(code.encode()).hexdigest())
            return jsonify(ok=True, code=code, wallet=wallet, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 422), getattr(exc, 'code', 'invalid_recovery'))

    @app.post('/gaming/api/recover')
    def gaming_recover():
        require_player_csrf()
        body = request.get_json(silent=True) or {}
        code = body.get('code', '') if isinstance(body, dict) else ''
        if not isinstance(code, str) or not 20 <= len(code) <= 512:
            return json_error('That recovery code is invalid or was replaced.', 400, 'invalid_recovery')
        decoded = None
        for signer in (recovery_signer, legacy_recovery_signer):
            try:
                decoded = signer.loads(code)
                break
            except BadSignature:
                continue
        original = (decoded.get('player') or decoded.get('guest')) if isinstance(decoded, dict) else None
        if not isinstance(original, str) or not re.fullmatch(r'[a-f0-9]{32}', original):
            return json_error('That recovery code is invalid or was replaced.', 400, 'invalid_recovery')
        try:
            wallet = gaming.recover(original, hashlib.sha256(code.encode()).hexdigest(), client_ip=g.client_ip)
            g.guest = g.new_guest = original
            return jsonify(ok=True, wallet=wallet, player_csrf=player_csrf(), release=RELEASE)
        except ValueError as exc:
            return json_error(str(exc), getattr(exc, 'status', 400), getattr(exc, 'code', 'invalid_recovery'))

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
        # Local Gaming statistics only; this endpoint never contacts providers.
        response = jsonify(ok=True, **gaming.leaders(), public_activity=gaming.public_leaderboard(),
                           release=RELEASE, visitor_ip_configured=not config.production or config.proxy)
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
            return checkpoint_status(runtime.store.checkpoint(), runtime.admin, runtime.shuffle["rows"], gaming.recovery())

    def render_admin(tab=None, draft=None, errors=None, confirm_race=False, restore=None, status=200,
                     change_review=None, review_token=None, recovery_review=None, section_focus=None):
        if status >= 400 and wants_json():
            return json_error(' '.join((errors or {}).values()) or 'This change could not be saved.', status)
        tab = tab or request.args.get("tab", "overview")
        if tab not in TABS:
            tab = "overview"
        values = runtime.status()
        values['gaming'] = gaming.leaders()
        values['gaming']['public_activity'] = gaming.public_leaderboard()
        values['health'] = health_view(runtime, measurements, values)
        values["checkpoint"] = recovery_status() if g.superadmin else None
        empire_status = runtime.empiredrop.private_status(g.admin["site_settings"])
        values["providers"] = summarize_providers(values, empire_status)
        values["durability"] = dict(mode='Spaces mirror' if runtime.store.mirror else 'Local JSON',
                                    remote=bool(runtime.store.mirror),
                                    revision=g.revision,
                                    last_mirrored=(runtime.store.mirror.last_verified if runtime.store.mirror else 0))
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
                               change_review=change_review, review_token=review_token,
                               recovery_review=recovery_review, admin_receipt=receipt,
                               gaming_grant_id=secrets.token_hex(16),
                               empire_admin=empire_status, section_focus=section_focus), status

    def admin_saved(message, tab, target):
        """A receipt is created only after the state commit succeeds.

        JSON writes redirect once to the native page; invalid writes stay in the
        original form so the browser can retain drafts and selected upload files.
        Never save passwords or form bodies in a receipt or log.
        """
        session['admin_receipt'] = dict(message=message, user=g.user, tab=tab,
                                        target=target, at=int(time.time()))
        destination = admin_link(tab) + '#feedback-' + target
        if wants_json():
            return jsonify(ok=True, message=message, redirect=destination, release=RELEASE)
        return redirect(destination, 303)

    @app.route("/admin", methods=["GET", "POST"], endpoint="admin_main")
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
        return redirect(admin_link("overview"), 303)

    # Stable V13 workspace routes. Each visible navigation target resolves
    # directly to an authenticated page instead of depending on query parsing.
    def workspace(tab, focus=None):
        return render_admin(tab, section_focus=focus)

    @app.get('/admin/leaderboards/shuffle')
    @protected
    def admin_shuffle_page():
        return workspace('shuffle')

    @app.get('/admin/leaderboards/shuffle/schedule')
    @protected
    def admin_shuffle_schedule_page():
        return workspace('race', 'schedule')

    @app.get('/admin/leaderboards/shuffle/players')
    @protected
    def admin_shuffle_players_page():
        return workspace('players')

    @app.get('/admin/leaderboards/shuffle/prizes')
    @protected
    def admin_shuffle_prizes_page():
        return workspace('race', 'prizes')

    @app.get('/admin/leaderboards/shuffle/source')
    @protected
    def admin_shuffle_source_page():
        return workspace('shuffle', 'shuffleSource')

    @app.get('/admin/leaderboards/empiredrop')
    @protected
    def admin_empiredrop_page():
        return workspace('empiredrop')

    @app.get('/admin/leaderboards/empiredrop/schedule')
    @protected
    def admin_empiredrop_schedule_page():
        return workspace('empiredrop', 'empireDatesTitle')

    @app.get('/admin/leaderboards/empiredrop/payouts')
    @protected
    def admin_empiredrop_payouts_page():
        return workspace('empiredrop', 'empireRewards')

    @app.get('/admin/leaderboards/empiredrop/source')
    @protected
    def admin_empiredrop_source_page():
        return workspace('empiredrop', 'empireRaceDetails')

    @app.get('/admin/settings')
    @protected
    def admin_settings_page():
        return workspace('settings')

    @app.get('/admin/recovery')
    @protected
    def admin_recovery_page():
        return workspace('settings', 'recovery')

    @app.get('/admin/activity')
    @protected
    def admin_activity_page():
        return workspace('activity')

    # Cached V9/V10/V11 links remain safe compatibility aliases.
    @app.get('/admin/section/<section>')
    @protected
    def admin_section_compat(section):
        tab = ADMIN_SECTION_ALIASES.get(section.strip().lower())
        if tab is None:
            abort(404, description="Unknown admin section. Open Control Center and try again.")
        anchor = {'recovery': 'recovery', 'accounts': 'adminAccounts',
                  'connections': 'configurationDetails'}.get(section)
        return redirect(admin_link(tab, anchor) if anchor else admin_link(tab), code=302)

    # Old bookmarked paths redirect to canonical destinations.
    legacy_destinations = {
        '/admin/overview': 'overview', '/admin/leaderboards': 'shuffle',
        '/admin/shuffle': 'shuffle', '/admin/race': 'race',
        '/admin/schedule': 'race', '/admin/players': 'players',
        '/admin/empiredrop': 'empiredrop', '/admin/community': 'gaming',
        '/admin/logs': 'activity',
    }
    for legacy_path, legacy_tab in legacy_destinations.items():
        def legacy_admin_destination(_tab=legacy_tab):
            return redirect(admin_link(_tab), code=302)
        endpoint = 'admin_compat_' + legacy_path.strip('/').replace('/', '_')
        app.add_url_rule(legacy_path, endpoint=endpoint, view_func=protected(legacy_admin_destination), methods=['GET'])

    required_actions = {
        '/admin', '/admin/section/<section>', '/admin/action', '/admin/logout',
        '/admin/leaderboards/shuffle', '/admin/leaderboards/shuffle/schedule',
        '/admin/leaderboards/shuffle/players', '/admin/leaderboards/shuffle/prizes',
        '/admin/leaderboards/shuffle/source', '/admin/leaderboards/empiredrop',
        '/admin/leaderboards/empiredrop/schedule', '/admin/leaderboards/empiredrop/payouts',
        '/admin/leaderboards/empiredrop/source', '/admin/gaming', '/admin/settings',
        '/admin/recovery', '/admin/activity',
        '/admin/empiredrop/refresh', '/admin/empiredrop/schedule',
        '/admin/empiredrop/rewards', '/admin/empiredrop/races/config',
        '/admin/empiredrop/keys'
    }

    @app.get('/admin/navigation-status')
    @protected
    def admin_navigation_status():
        """Safe diagnostic: destinations and methods only, no credentials."""
        return jsonify(ok=True, release=RELEASE, sections={
            name: admin_link(tab) for name, tab in ADMIN_SECTION_ALIASES.items()
        }, registered=[{'path': rule.rule, 'methods': sorted(rule.methods - {'HEAD','OPTIONS'})}
                      for rule in app.url_map.iter_rules()
                      if rule.rule.startswith('/admin') and not '<' in rule.rule])

    @app.post("/admin/logout")
    def logout():
        require_csrf()
        session.clear()
        return redirect(url_for("login"), 303)

    @app.get("/admin/status")
    @protected
    def status():
        value = runtime.status()
        # The dedicated gaming feed owns fast rankings. Older clients still
        # receive them unless they explicitly opt out of this duplicate body.
        if request.args.get('gaming') != '0':
            value['gaming'] = gaming.leaders()
        value['health'] = health_view(runtime, measurements, value)
        value["checkpoint"] = recovery_status() if g.superadmin else None
        value["providers"] = summarize_providers(value, runtime.empiredrop.private_status(g.admin["site_settings"]))
        rows, edits = value.pop("rows"), value.pop("edits")
        # Other tabs have no participant table; keep their minute responses small.
        if request.args.get("tab", "players") == "players":
            value["participants"] = filtered(rows, edits, request.args)
        if request.args.get("code_red") != "1":
            value.pop("red", None)
        return jsonify(value)

    @app.get('/admin/empiredrop/status')
    @protected
    def empire_admin_status():
        """Protected provider diagnostics; a public request can never read names."""
        return jsonify(runtime.empiredrop.private_status(g.admin['site_settings']))

    @app.post('/admin/empiredrop/refresh')
    @protected
    def empire_admin_refresh():
        """Queue an independent worker check; do not claim success when queued."""
        require_csrf()
        if runtime.started:
            queued = runtime.empiredrop.request_refresh()
            if queued: safe_activity('empiredrop','info','refresh_queued')
            message = ('EmpireDrop refresh requested; check status for the confirmed result.' if queued
                       else 'A refresh was requested recently; the 15-second limit is still active.')
        else:
            message = 'The EmpireDrop worker is not running. Launch python wager_backend.py.'
        return admin_saved(message, 'empiredrop', 'empireRefresh')

    @app.post('/admin/empiredrop/test')
    @protected
    def empire_admin_test():
        """Test authenticated access WITHOUT publishing or changing any standings.

        This is a real network test only when the Superadmin has confirmed the
        official provider contract; otherwise it fails safely with an explanation.
        """
        require_csrf()
        if not g.superadmin:
            abort(403)
        try:
            source_mode = runtime.empiredrop._race_settings()['source_mode']
            if source_mode == 'races':
                rows, _ = runtime.empiredrop._fetch_races(empire_schedule(g.admin))
            elif source_mode == 'legacy_window':
                rows, _ = runtime.empiredrop._fetch_window(empire_schedule(g.admin))
            else:
                rows = runtime.empiredrop.fetch(empire_schedule(g.admin))
        except ProviderError as exc:
            # Only our own short safe exception text is exposed; no response body or keys.
            result = {'ok': False, 'kind': exc.kind, 'message': str(exc)[:220]}
            status = 422
        else:
            result = {'ok': True, 'kind': 'verified', 'message': 'Authenticated result validated. No standings were changed.',
                      'qualified_players': len(rows)}
            status = 200
        safe_activity('empiredrop','success' if status==200 else 'warning','connection_test',count=len(rows) if status==200 else None,
                        code=exc.kind if status!=200 and isinstance(exc,ProviderError) else None)
        return jsonify(result), status

    @app.post('/admin/empiredrop/discover')
    @protected
    def empire_admin_discover():
        """Read public-key race catalog; never return credentials or player PII."""
        require_csrf()
        if not g.superadmin: abort(403)
        try:
            return jsonify({'ok':True, **runtime.empiredrop.discover_races()})
        except ProviderError as exc:
            return jsonify({'ok':False, 'kind':exc.kind, 'message':str(exc)[:220]}), 422

    @app.post('/admin/empiredrop/probe')
    @protected
    def empire_admin_probe():
        """Return only JSON field names/types to aid correct field mapping."""
        require_csrf()
        if not g.superadmin: abort(403)
        try:
            # The slug can be left empty to use the uniquely active provider race.
            slug = str((request.get_json(silent=True) or {}).get('slug', '')).strip()
            if len(slug) > 100: raise ValueError('Invalid slug length.')
            return jsonify({'ok':True, **runtime.empiredrop.probe_race(slug)})
        except (ProviderError, ValueError) as exc:
            return jsonify({'ok':False, 'kind':getattr(exc,'kind','input'), 'message':str(exc)[:220]}), 422

    @app.post('/admin/empiredrop/races/config')
    @protected
    def empire_admin_race_config():
        """Persist race API settings independently of Shuffle and legacy mode."""
        require_csrf()
        if not g.superadmin: abort(403)
        try:
            expected = int(request.form.get('revision', '-1'))
            if expected != g.revision: raise Conflict('Settings changed. Reload and try again.')
            # Authentication, endpoint, units and JSON paths are FIXED by the
            # official OpenAPI 2.0.1. Admins only choose which race to display.
            values = {
                'source_mode': request.form.get('source_mode', 'races').strip(),
                'race_slug': request.form.get('race_slug', '').strip(),
                'auto_select': request.form.get('auto_select') == 'yes',
                'race_window_policy': request.form.get('race_window_policy', 'provider').strip(),
            }
            candidate = copy.deepcopy(g.admin)
            candidate['empiredrop_races'] = validate_race_settings(values)
            runtime.commit(candidate, expected)
            runtime.empiredrop.request_refresh()
            safe_activity('admin','info','settings_saved',code='empire_settings')
            return admin_saved('EmpireDrop race API settings saved; a refresh was queued. Verify results before publishing.',
                               'empiredrop', 'empireRaces')
        except (ValueError, Conflict) as exc:
            return render_admin('empiredrop', errors={'empiredrop':str(exc)},
                                status=409 if isinstance(exc, Conflict) else 422)

    @app.post('/admin/empiredrop/schedule')
    @protected
    def empire_admin_schedule():
        """EmpireDrop calendar is never copied from or written into Shuffle."""
        require_csrf()
        if not g.superadmin:
            abort(403)
        try:
            expected = int(request.form.get('revision', '-1'))
            if expected != g.revision:
                raise Conflict('Another administrator saved settings. Reload before editing.')
            mode = request.form.get('mode')
            if mode == 'weekly':
                value = {'mode':'weekly'}
            elif mode == 'custom':
                start = eastern_epoch(request.form.get('start_et'))
                end = eastern_epoch(request.form.get('end_et'))
                if not 0 < start < end <= 4102444799 or end-start > 90*86400:
                    raise ValueError('EmpireDrop custom race must be between 1 minute and 90 days.')
                value = {'mode':'custom', 'start_time':start, 'end_time':end}
            else:
                raise ValueError('Choose a valid EmpireDrop schedule mode.')
            candidate = copy.deepcopy(g.admin)
            candidate['empiredrop_race'] = value
            # Local dates are retained for administration and backup, but the
            # public standings remain on EmpireDrop's documented slug endpoint.
            # Earlier releases silently switched this form to the deprecated
            # timestamp endpoint, which could leave the public board empty.
            race_options = validate_race_settings(candidate.get('empiredrop_races', {}))
            race_options['source_mode'] = 'races'
            race_options['race_window_policy'] = 'provider'
            candidate['empiredrop_races'] = validate_race_settings(race_options)
            runtime.commit(candidate, expected)
            runtime.empiredrop.request_refresh()
            safe_activity('admin','info','settings_saved',code='empire_schedule')
            return admin_saved(
                'EmpireDrop local schedule saved. Official provider standings and dates remain authoritative.',
                'empiredrop', 'empireSchedule')
        except (ValueError, Conflict) as exc:
            return render_admin('empiredrop', errors={'empiredrop':str(exc)},
                                status=409 if isinstance(exc, Conflict) else 422)

    @app.post('/admin/empiredrop/rewards')
    @protected
    def empire_admin_rewards():
        """Atomically save a draft or publish ten independent rank prizes.

        This form has its own revision counter. Unrelated Shuffle, account or
        integration changes no longer invalidate an open payout editor.
        """
        require_csrf()
        if not g.superadmin:
            abort(403)
        try:
            expected = int(request.form.get('reward_revision', '0'))
            mode = request.form.get('save_mode', 'draft')
            if mode not in {'draft', 'publish'}:
                raise ValueError('Choose Save draft or Save and publish.')
            with runtime.store.connection(transaction=True) as conn:
                published = validate_rewards(conn['admin'].get('empiredrop_rewards', {}))
                current = validate_rewards(conn['admin'].get('empiredrop_rewards_draft',
                                                             conn['admin'].get('empiredrop_rewards', {})))
                if expected != current['revision']:
                    raise Conflict('EmpireDrop prizes changed in another tab. Reload and review the saved values.')
                payload = dict(
                    currency=request.form.get('currency', 'EUR'),
                    enabled=mode == 'publish',
                    prizes={str(n): request.form.get('prize_' + str(n), '') for n in range(1, 11)},
                    revision=current['revision'] + 1,
                    updated_at=int(time.time()),
                    updated_by=g.user,
                )
                value = validate_rewards(payload)
                runtime.store.backup_in(conn, 'before-empiredrop-payout-change',
                                        {'empiredrop_rewards': published,
                                         'empiredrop_rewards_draft': current})
                conn['admin']['empiredrop_rewards_draft'] = copy.deepcopy(value)
                if mode == 'publish':
                    conn['admin']['empiredrop_rewards'] = copy.deepcopy(value)
                conn['admin']['settings_revision'] = int(conn['admin'].get('settings_revision', 1)) + 1
                conn['admin']['updated_at'] = int(time.time())
                conn['revision'] += 1
            runtime.sync()
            _, persisted_admin = runtime.store.admin()
            persisted = validate_rewards(persisted_admin.get('empiredrop_rewards_draft',
                                                                persisted_admin.get('empiredrop_rewards', {})))
            if persisted != value:
                raise StoreError('The payout write could not be verified. Existing public prizes were not changed.')
            public_prizes = runtime.empiredrop.public().get('prizes', {})
            expected_public = rewards_public(value)
            if mode == 'publish' and public_prizes != expected_public:
                raise StoreError('The payout was saved but the public projection did not refresh. Reload before retrying.')
            safe_activity('admin', 'success', 'empire_rewards_published' if mode == 'publish' else 'empire_rewards_draft',
                            code='empire_rewards', count=10)
            message = (
                'EmpireDrop prizes saved and published on the public Top 10.'
                if mode == 'publish' else
                'EmpireDrop prize draft saved. The public leaderboard still shows the previously published state.'
            )
            return admin_saved(message, 'empiredrop', 'empireRewards')
        except (ValueError, Conflict, StoreError) as exc:
            safe_activity('admin', 'warning', 'empire_rewards_save_failed',
                            code='conflict' if isinstance(exc, Conflict) else 'validation')
            return render_admin('empiredrop', errors={'empiredrop': str(exc)},
                                status=409 if isinstance(exc, Conflict) else 422)

    @app.get('/admin/empiredrop/settings-backup')
    @protected
    def empire_settings_backup():
        """Export ONLY EmpireDrop admin choices. No live keys or player IDs."""
        if not g.superadmin: abort(403)
        _, current = runtime.store.admin()
        document = {
            'format': 'redhunllef-empiredrop-settings-2',
            'empiredrop_races': validate_race_settings(current.get('empiredrop_races', {})),
            'empiredrop_race': copy.deepcopy(current.get('empiredrop_race', {'mode':'weekly'})),
            'empiredrop_rewards': validate_rewards(current.get('empiredrop_rewards', {})),
            'empiredrop_rewards_draft': validate_rewards(current.get('empiredrop_rewards_draft', current.get('empiredrop_rewards', {}))),
        }
        safe_activity('admin','info','backup_export')
        return Response(json.dumps(document,indent=2),mimetype='application/json',
                        headers={'Content-Disposition':'attachment; filename=empiredrop-settings-backup.json'})

    @app.post('/admin/empiredrop/settings-restore')
    @protected
    def empire_settings_restore():
        """Opt-in import of settings ONLY; never replace accounts, games, or keys.

        A successful commit performs the store's ordinary revision-checked save.
        The separate provider worker then refreshes when its cache permits.
        """
        require_csrf()
        if not g.superadmin: abort(403)
        try:
            if request.form.get('confirm') != 'yes':
                raise ValueError('Check the confirmation before importing settings.')
            expected = int(request.form.get('revision','-1'))
            if expected != g.revision:
                raise Conflict('Settings changed. Reload and recheck the import.')
            upload = request.files.get('settings_file')
            if upload is None:
                raise ValueError('Select an EmpireDrop settings JSON file.')
            try:
                incoming = json.load(upload)
            except (ValueError,UnicodeDecodeError):
                raise ValueError('The selected file is not valid JSON.') from None
            if not isinstance(incoming, dict) or incoming.get('format') not in {
                    'redhunllef-empiredrop-settings-1', 'redhunllef-empiredrop-settings-2'}:
                raise ValueError('This is not a supported EmpireDrop settings backup.')
            required = {'format','empiredrop_races','empiredrop_race','empiredrop_rewards'}
            allowed = required | {'empiredrop_rewards_draft'}
            if not required.issubset(incoming) or set(incoming) - allowed:
                raise ValueError('This EmpireDrop settings backup has unexpected fields.')
            race = incoming['empiredrop_race']
            if not isinstance(race,dict) or race.get('mode') not in {'weekly','custom'}:
                raise ValueError('Invalid EmpireDrop race schedule in backup.')
            if race['mode']=='custom':
                start,end = race.get('start_time'),race.get('end_time')
                if type(start) is not int or type(end) is not int or                    not 0 < start < end <= 4102444799 or end-start>90*86400:
                    raise ValueError('Invalid custom race dates in backup.')
                race={'mode':'custom','start_time':start,'end_time':end}
            else:
                race={'mode':'weekly'}
            reward = validate_rewards(incoming['empiredrop_rewards'])
            reward_draft = validate_rewards(incoming.get('empiredrop_rewards_draft', reward))
            opts = validate_race_settings(incoming['empiredrop_races'])
            candidate = copy.deepcopy(g.admin)
            candidate.update(empiredrop_races=opts, empiredrop_race=race,
                             empiredrop_rewards=reward, empiredrop_rewards_draft=reward_draft)
            runtime.commit(candidate,expected,reason='before-empiredrop-settings-restore')
            runtime.empiredrop.request_refresh()
            safe_activity('admin','info','settings_saved')
            return admin_saved('EmpireDrop settings restored. Accounts, games, Shuffle and API keys were not changed.',
                               'empiredrop','empireBackup')
        except (ValueError,Conflict) as exc:
            return render_admin('empiredrop',errors={'empiredrop':str(exc)},
                                status=409 if isinstance(exc,Conflict) else 422)

    @app.post('/admin/empiredrop/keys')
    @protected
    def empire_admin_keys():
        """Update the server-side private file, never store credentials in admin JSON."""
        require_csrf()
        if not g.superadmin:
            abort(403)
        try:
            changed = config.replace_empiredrop_keys(request.form.get('empiredrop_public_key',''),
                                                     request.form.get('empiredrop_private_key',''))
            return admin_saved('EmpireDrop credentials updated in private/settings.json.' if changed
                               else 'No new credential was entered; existing keys remain unchanged.',
                               'empiredrop', 'empireKeys')
        except (ValueError, OSError) as exc:
            return render_admin('empiredrop', errors={'empiredrop':'Credential update failed: ' +
                                ('Check that private settings are writable.' if isinstance(exc,OSError) else str(exc))}, status=422)

    @app.post('/admin/empiredrop/config')
    @protected
    def empire_admin_config():
        require_csrf()
        if not g.superadmin:
            abort(403, description='Only the Superadmin can configure EmpireDrop.')
        try:
            expected = int(request.form.get('revision', '-1'))
            if expected != g.revision:
                raise Conflict('Another administrator changed settings. Reload and try again.')
            fields = {name: request.form.get(name, '').strip() for name in sorted(EDITABLE - {'code_scoped','verified_contract'})}
            fields['code_scoped'] = request.form.get('code_scoped') == 'yes'
            fields['verified_contract'] = request.form.get('verified_contract') == 'yes'
            candidate = copy.deepcopy(g.admin)
            candidate['empiredrop_api'] = validate_settings(fields)
            runtime.commit(candidate, expected)
            # Preserve the last verified result on configuration saves. It is
            # marked stale until a successful provider response replaces it.
            with runtime.empiredrop.lock:
                prior = dict(runtime.empiredrop.saved)
                if prior.get('updated_at'):
                    prior.update(error='API configuration changed; last verified results retained until rechecked.',
                                 error_kind='configuration')
                    runtime.store.publish('empiredrop', prior)
                    runtime.empiredrop.saved = prior
            runtime.empiredrop.request_refresh()
            return admin_saved('EmpireDrop API configuration saved. Last verified results preserved; refresh requested.',
                               'empiredrop', 'empireConfig')
        except (ValueError, Conflict) as exc:
            return render_admin('empiredrop', errors={'empiredrop':str(exc)},
                                status=409 if isinstance(exc, Conflict) else 422)

    @app.get('/admin/operations/events')
    @protected
    def operations_events():
        """Admin-only structured events. No usernames, addresses, keys, or bodies."""
        try:
            result = activity.list(request.args.get('service','all'),
                                   request.args.get('level','all'),request.args.get('limit','100'))
        except ValueError:
            return json_error('Choose valid event filters.',422)
        return jsonify(events=result, summary=activity.summary(request.args.get('service','all'),request.args.get('level','all')),
                       retention='Last 300 events; reset on server restart')

    @app.get('/admin/operations/export')
    @protected
    def operations_export():
        """Download a minimal, safe operational report, never runtime snapshots."""
        try:
            report = activity.export(request.args.get('service','all'),
                                     request.args.get('level','all'))
        except ValueError:
            return json_error('Choose valid event filters.',422)
        # TXT is convenient when sharing a quick diagnostic excerpt. Both
        # formats are built exclusively from the allowlisted event schema.
        if request.args.get('format') == 'txt':
            lines = ['RedHunllef operational activity (sanitized)',
                     'Generated: '+report['generated_at'], report['retention'], '']
            for event in report['events']:
                lines.append('%s | %-10s | %-7s | %-18s | class=%s | HTTP %s | %s ms | %s entries | %sx' % (
                    datetime.fromtimestamp(event['at'], timezone.utc).isoformat(),event['service'],event['level'],event['event'],
                    event.get('code') or '-',
                    event['http_status'] if event['http_status'] is not None else '-',
                    event['duration_ms'] if event['duration_ms'] is not None else '-',
                    event['count'] if event['count'] is not None else '-',
                    event.get('occurrences', 1)))
            return Response('\n'.join(lines)+'\n',mimetype='text/plain',
                            headers={'Content-Disposition':'attachment; filename=redhunllef-operations.txt'})
        return Response(json.dumps(report,indent=2),mimetype='application/json',
                        headers={'Content-Disposition':'attachment; filename=redhunllef-operations.json'})

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
        safe_activity('admin','info','backup_export')
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
            value['weekly_history'] = copy.deepcopy(conn['live'].get('weekly_history'))
            value['redpoints'] = copy.deepcopy(conn.get('gaming'))
            marker = export_marker(conn['admin'], value["leaderboard_snapshots"], int(time.time()), value["redpoints"])
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
            # Older recovery files may include retired profile fields; they are
            # ignored rather than restored into the current application.
            redpoints = validate_gaming(value.get('redpoints'))
            review = dict(accounts=len(value["users"]), overrides=len(value["overrides"]),
                          history=len(value["race_history"]), rows=len(value["leaderboard_snapshots"]["last_top15"]),
                          start=fmt_et(value["site_settings"]["start_time"]), end=fmt_et(value["site_settings"]["end_time"]),
                          redpoints=len(redpoints['players']) if redpoints else 0)
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
            return redirect(admin_link(tab if tab in TABS else "overview"), 303)
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
            # One sanitized operational event for the control panel. The detailed
            # account/adjustment audit remains in the protected persistent audit.
            if action_name in {'save_race', 'override', 'restore'}:
                safe_activity('admin', 'info', 'settings_saved', code='shuffle_settings')
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

    missing_admin_actions = required_actions - {rule.rule for rule in app.url_map.iter_rules()}
    if missing_admin_actions:
        raise RuntimeError("Missing admin routes: " + ", ".join(sorted(missing_admin_actions)))
    return app


def main():
    boot_started = time.perf_counter()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        from release_check import check_release
        checked = check_release(strict='--check' in sys.argv)
        preflight_seconds = time.perf_counter() - boot_started
        if not checked['ok']:
            raise RuntimeError('Release check failed: '+'; '.join(checked['problems']))
        for warning in checked['warnings']:
            LOG.warning('RELEASE %s', warning)
        if '--check' in sys.argv:
            LOG.info('RELEASE Checked %s Python modules and %s templates. No accounts or game state changed.', checked['python_modules'], checked['templates'])
            return 0
        app = create_app()
        application_seconds = time.perf_counter() - boot_started - preflight_seconds
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
        listener_seconds = time.perf_counter() - boot_started - preflight_seconds - application_seconds
        LOG.info("BOOT stages: preflight=%.3fs application=%.3fs listener=%.3fs",
                 preflight_seconds, application_seconds, listener_seconds)
        LOG.info("START RedHunllef %s listening on 0.0.0.0:%s; storage=%s.", RELEASE, config.port,
                 'JSON + Spaces mirror' if runtime.store.mirror else 'local JSON')
        LOG.info('HEALTH /healthz checks the process; /readyz checks local reads and writes. Provider delays appear separately in Admin Overview.')
        LOG.info("GAMING RedPoints identities, wallets and recovery are handled independently at /gaming.")
        if not runtime.store.pg:
            LOG.info("STORAGE Local file ready; no external database is required.")
            if config.production and not runtime.store.mirror:
                LOG.warning("STORAGE On App Platform, local changes are lost on redeploy/container replacement. Download the private recovery file from Settings after important changes.")
        for key, details in config.diagnostics().items():
            LOG.info("CONFIG %s: %s (%s).", key, "configured" if details["configured"] else "missing", details["source"])
        LOG.info("RACE Saved window: %s → %s. State=%s.", fmt_et(runtime.admin["site_settings"]["start_time"]),
                 fmt_et(runtime.admin["site_settings"]["end_time"]), phase(runtime.admin["site_settings"]))
        def shutdown(*_):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM, shutdown)
        runtime.start()
        LOG.info("BOOT ready for HTTP after %.3fs; /healthz is process health, /readyz is storage readiness",
                 time.perf_counter() - boot_started)
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
