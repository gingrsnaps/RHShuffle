# Community boss reference

Run `python wager_backend.py`; the game is served at `/play`. No separate process,
SQL server or external account is required. State uses `data/state.json`.

The shared boss defaults to 2,400,000 HP. Registered players attack every 30 seconds,
without daily or weekly quotas. A random shared weakness lasts ten minutes;
consecutive identical draws are valid. Defaults are 100 normal damage, 150 weakness
damage, and a 100 bonus every tenth hit. Admins can change those whole-number values.

Health never regenerates automatically. Only an explicit admin health edit or a new
raid can increase it. The percentage measures defeated HP from 0% through 100%.
Requests never supply trusted damage. Repeated request receipts return the original
hit without dealing damage twice. A lost response can therefore be retried safely.

Names are self-reported. Public leaderboards show aliases; the owner and signed-in
admins can see submitted names. The admin Top 5 contains full names. A Shuffle
spelling match does not verify an account or connection. The game does not claim
access to a Shuffle IP mapping.

Each player is identified by a persistent signed browser cookie. Shared IPv4,
IPv6, VPN, carrier and proxy addresses do not restrict how many players can join.
The same cookie keeps its saved username and cooldown when IPs change. Tabs sharing
a cookie are the same player; separate browser identities get independent cooldowns.
Game writes still require a valid cookie and CSRF token. Missing IP headers do not
block registration, recovery or attacks. No household approval or raid reset is
needed. Old network records are retained for compatibility, not used for admission.

A browser identity is not proof of a unique human; cookie deletion can create a
new player. Existing names cannot be claimed just by typing them. Use the original
browser or a valid recovery code to restore an existing profile.

A private recovery code restores the original identity after cookie loss. The
server stores a digest; the code is shown once when created. A replacement revokes
the old code. Codes need the saved secret and profile data and cannot recover a
lost server disk by themselves. They remain valid across new raids.

The eight existing badges, progress labels and week-long prerequisites are unchanged.
Badges do not cap hits. The added Red rally is a separate cosmetic community goal:
15 distinct raiders hit within a rolling ten-minute window to light the arena for
the rest of the raid. It does not change health or damage.

Admin controls require current authenticated sessions and CSRF tokens. Avatar
uploads accept validated PNG/JPG/JPEG/WebP and reject malformed/animated/oversized
images. Health and damage previews show expected effects; revision checks prevent
stale admin edits. The last 100 host actions retain actor/time/before/after details.
All private fields are excluded from public projections.

Recent activity estimates use up to sixty minute buckets. After five minutes and
ten hits with damage, admin shows approximate damage/hour and remaining duration.
Presets fill the next raid's HP input only. They do not guarantee a duration or
change the current boss automatically. Before sufficient data exists, the preset
health amounts are only starting suggestions.

Rejected requests are counted in bounded, in-memory windows. Bursts are briefly
throttled per signed browser and visible as private diagnostic flags, without automatic bans or shared-IP lockouts. Valid
eligible attacks bypass that guard and keep their regular 30-second cadence.

Screens poll every five seconds. Hidden browser tabs resume on visibility. The
server's Shuffle/Kick minute workers run independently of game polling. The only
launch script remains `wager_backend.py`.

App Platform replaces local files on redeploy/container replacement. Use the
existing manual private recovery export before a planned redeployment; progress
after the latest export can still be lost. No external backup service was added.
