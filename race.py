"""Pure race calculations: exact decimal rankings and one public projection."""
from decimal import Decimal, localcontext
import hashlib
import json
import time

from race_support import decimal_amount, money, race_key

NAMES = ("username", "displayName", "userName", "player", "name")
WEIGHTED = ("weightedWagerAmount", "weightedWager", "weightedAmount", "wagerWeighted")
RAW = ("wagerAmount", "totalWagered", "wageredAmount", "rawWagerAmount")
CAMPAIGN = ("campaignCode", "campaign", "code", "referralCode", "affiliateCode")


def first(row, keys):
    return next((row[k] for k in keys if row.get(k) is not None), None)


def phase(site, now=None):
    now = time.time() if now is None else now
    start, end = site["start_time"], site["end_time"]
    return "unconfigured" if not start or end <= start else "upcoming" if now < start else "ended" if now >= end else "active"


def token(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:20]


def normalize(rows, site, raw_fallback=False):
    accepted, red, rejected, missing_campaign = [], [], {}, 0
    for row in rows:
        reason = None
        if not isinstance(row, dict):
            reason = "invalid record"
        else:
            name, weighted, raw, campaign = first(row, NAMES), first(row, WEIGHTED), first(row, RAW), first(row, CAMPAIGN)
            campaign = None if campaign is None else str(campaign).strip().casefold()
            if not isinstance(name, str) or not name.strip() or len(name) > 64:
                reason = "missing or invalid username"
            elif weighted is None and not raw_fallback:
                reason = "missing weighted amount"
            else:
                try:
                    amount = decimal_amount(raw if weighted is None else weighted)
                except ValueError:
                    reason = "invalid weighted amount"
                if reason is None:
                    raw_invalid = False
                    try:
                        raw_amount = None if raw is None else str(decimal_amount(raw))
                    except ValueError:
                        raw_amount, raw_invalid = None, True
                    item = dict(username=name.strip(), weighted=str(amount), raw=raw_amount, raw_invalid=raw_invalid, row_count=1)
                    if campaign == "red":
                        red.append(item)
                    if campaign is None:
                        missing_campaign += 1
                    expected = site.get("campaign_code_filter", "").strip().casefold()
                    if not expected or campaign is None or campaign == expected:
                        accepted.append(item)
                    else:
                        reason = "other campaign"
        if reason:
            rejected[reason] = rejected.get(reason, 0) + 1
    invalid = sum(v for k, v in rejected.items() if k != "other campaign")
    if invalid and not accepted:
        raise ValueError("Shuffle returned no usable race records. Previous results are retained.")
    warning = f"{invalid} incomplete source record(s) skipped; rankings may be incomplete." if invalid else ""
    if any(row["raw_invalid"] for row in accepted):
        warning += " Some raw totals are unavailable; valid weighted totals still update."
    return dict(source=accepted, red_source=red, rejected=rejected, missing_campaign=missing_campaign,
                received=len(rows), accepted=len(accepted), warning=warning.strip())


def aggregate(rows, mode="sum"):
    result = {}
    for row in rows:
        name = row["username"]
        if name not in result:
            result[name] = dict(row)
            continue
        old = result[name]
        old["row_count"] += row.get("row_count", 1)
        old["raw_invalid"] = old.get("raw_invalid", False) or row.get("raw_invalid", False)
        for key in ("weighted", "raw"):
            if row.get(key) is not None:
                with localcontext() as ctx:
                    ctx.prec = 60
                    a, b = decimal_amount(old.get(key) or 0), decimal_amount(row[key])
                    old[key] = str(max(a, b) if mode == "max" else a + b)
    for row in result.values():
        if row.get("raw_invalid"):
            row["raw"] = None
    return result


def rank(source, overrides, mode="sum", limit=300):
    values = aggregate(source, mode)
    for name in overrides:
        values.setdefault(name, dict(username=name, weighted=None, raw=None, row_count=1))
    ordered = sorted(values.values(), key=lambda r: (-decimal_amount(overrides.get(r["username"], r["weighted"]) or 0), r["username"].casefold(), r["username"]))
    ranked, edits, count = [], [], 0
    for row in ordered:
        original = row["weighted"]
        amount = overrides.get(row["username"], original) or "0"
        qualifies = decimal_amount(amount) >= Decimal("0.01")
        count += int(qualifies)
        item = dict(rank=count if qualifies else None, username=row["username"], weighted_wager=amount,
                    wager=money(amount), original_weighted_wager=original, original_weighted_str=money(original),
                    raw_wager=row["raw"], raw_wager_str=money(row["raw"]), row_count=row.get("row_count", 1),
                    source="override" if row["username"] in overrides else "shuffle")
        if qualifies and len(ranked) < limit:
            ranked.append(item)
        if item["source"] == "override":
            edits.append(item)
    return ranked, edits, count


def empty(site):
    return dict(key=race_key(site), source=[], red_source=[], rows=[], edits=[], red=[], red_total=0, count=0,
                updated_at=0, attempt_at=0, ok=None, error="", warning="", received=0, accepted=0,
                rejected={}, missing_campaign=0, previous_top=[], snapshot_only=False)


def calculate(snapshot, admin, config):
    result = dict(snapshot)
    site = admin["site_settings"]
    rows, edits, count = rank(result["source"], admin["overrides"], config.aggregation, config.limit)
    # Code Red includes raw wagerers with zero weighted contribution, too.
    red = aggregate(result.get("red_source", []), config.aggregation)
    red = [r for r in red.values() if max(decimal_amount(r["weighted"]), decimal_amount(r.get("raw") or 0)) >= Decimal("0.01")]
    red.sort(key=lambda r: (-decimal_amount(r["weighted"]), r["username"].casefold(), r["username"]))
    result.update(rows=rows, edits=edits, count=count,
                  red=[dict(username=r["username"], weighted=money(r["weighted"]), raw=money(r["raw"])) for r in red[:100]], red_total=len(red))
    if phase(site) in {"upcoming", "unconfigured"}:
        result.update(rows=[], red=[], red_total=0, count=0)
        result["edits"] = [{**r, "rank": None} for r in edits]
    result["revision"] = token([race_key(site), result["rows"], result["edits"], result["red"], result.get("warning")])
    return result


def freshness(snapshot):
    stamp = snapshot.get("updated_at", 0)
    stale = bool(snapshot.get("snapshot_only") or snapshot.get("error") or (stamp and time.time() - stamp > 180))
    state = "delayed" if stale else "waiting" if not stamp else "partial" if snapshot.get("warning") else "current"
    return dict(state=state, updated_at=stamp, attempt_at=snapshot.get("attempt_at", 0),
                label={"delayed":"Updates delayed", "waiting":"Waiting for source data", "partial":"Updated with incomplete data", "current":"Up to date"}[state],
                warning=snapshot.get("warning", ""), error=snapshot.get("error", ""))
