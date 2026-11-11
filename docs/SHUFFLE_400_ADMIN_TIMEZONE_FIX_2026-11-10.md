# RedHunllef: Shuffle 400 and Admin timezone hotfix — 2026-11-10

## Root causes supported by evidence

The provided operations JSON contains five Shuffle HTTP 400 rejections, all
classified as `window` by older code. That classification was misleading: the
old client assigned `window` to *every* HTTP 400 without inspecting the error.
It also contains an EmpireDrop HTTP 200 with 10 ranked entries. EmpireDrop's
successful source retrieval does not independently prove the public board rendered.

`static/admin-providers.js` and `static/admin-empiredrop.js` used the invalid
`Intl.DateTimeFormat` combination `dateStyle` + `timeStyle` + `timeZoneName`.
A browser RangeError interrupted refresh status rendering.

The bundled `data/state.json` has a Shuffle window from August 4–11, 2026,
which is expired relative to November 2026. It could explain rejection of a
historical request, but the operational log does not prove that was the specific
Shuffle provider validation reason. **This update does not overwrite that race.**

## Changes

- Both admin date formatters now use explicit fields with the Eastern timezone
  abbreviation, avoiding the RangeError.
- Shuffle HTTP 400 errors are only called `window` when the bounded response
  mentions known date keys; otherwise they're `bad_request`. Untrusted response
  text is never written to logs or shown to administrators.
- Source cards show a practical warning for stale race periods and clarify what
  HTTP 400 does and does not establish.
- Repeated warnings of the same service/event/code/status are grouped for up to
  five minutes, with an occurrence counter in the activity viewer.
- No API URLs, keys, username data, game data, or prize calculations were changed.
- Private settings, administrator seed and data/state.json are preserved intact.

## Actions in DigitalOcean after deployment

1. Open **Admin → Shuffle**, confirm the last HTTP status and last verified update.
2. Open **Schedule & prizes**. Review the saved dates; if the August 2026 race
   is no longer the intended event, use **Use current week** (for the current competition) or **Prepare next race** (for the next competition) and review the
   changes before publishing. This will intentionally create a new race window.
3. Verify the **Shuffle API key** is present in *the running DigitalOcean app*.
   The original ZIP has a key, but `.gitignore` can exclude private/settings.json
   from the Git deployment. Configure SHUFFLE_API_KEY as an encrypted secret
   if deploying through Git.
4. Request a refresh and check **Activity & logs**. HTTP 400 may still happen
   if the provider rejects the dates or request parameters. No live provider
   call has been performed by the test suite.
5. Open **Admin → EmpireDrop**; the submitted operations report already
   confirmed a response of HTTP 200 / 10 rows. Review the public board and
   your race slug before changing any EmpireDrop settings.

**Storage warning:** DigitalOcean App Platform local JSON state may be lost on
redeploy. Export a fresh private recovery copy before uploading the ZIP. The
bundled data files represent an earlier snapshot, not your latest live state.
