"""Canonical admin navigation contract.

Every visible destination has one stable URL. Legacy query-string and section
links redirect to these paths, so cached older pages cannot create 404s.
"""
from urllib.parse import urlencode

ADMIN_TABS = frozenset({
    "overview", "shuffle", "race", "players", "empiredrop",
    "gaming", "activity", "settings"
})

ADMIN_PATHS = {
    "overview": "/admin",
    "shuffle": "/admin/leaderboards/shuffle",
    "race": "/admin/leaderboards/shuffle/schedule",
    "players": "/admin/leaderboards/shuffle/players",
    "empiredrop": "/admin/leaderboards/empiredrop",
    "gaming": "/admin/gaming",
    "activity": "/admin/activity",
    "settings": "/admin/settings",
}

ADMIN_ANCHORS = {
    "race": frozenset({"raceForm", "prizes", "siteConfiguration"}),
    "players": frozenset({"override"}),
    "empiredrop": frozenset({"empirePlayersHeading", "empireDatesTitle",
        "empireRewards", "empireRaceDetails", "empireBackup", "empireAdvanced"}),
    "gaming": frozenset({"gamingAdminHeading", "gamingFunding"}),
    "settings": frozenset({"accountSecurity", "adminAccounts", "backups",
        "configurationDetails", "accessControls", "recovery"}),
    "activity": frozenset({"adminOperations"}),
}

ADMIN_SECTION_ALIASES = {
    "overview": "overview", "dashboard": "overview",
    "leaderboards": "shuffle", "shuffle": "shuffle",
    "schedule": "race", "race": "race", "prizes": "race", "edit-race": "race",
    "participants": "players", "wagerers": "players", "players": "players",
    "empiredrop": "empiredrop", "empire": "empiredrop",
    "games": "gaming", "gaming": "gaming", "redpoints": "gaming",
    "settings": "settings", "recovery": "settings", "connections": "settings",
    "accounts": "settings", "activity": "activity", "logs": "activity",
}


def admin_link(tab="overview", anchor=None):
    """Return a validated canonical admin URL."""
    if tab not in ADMIN_TABS:
        raise ValueError("Unknown admin tab")
    if anchor is not None and anchor not in ADMIN_ANCHORS.get(tab, frozenset()):
        raise ValueError("Unknown admin section")
    return ADMIN_PATHS[tab] + ("#" + anchor if anchor else "")


def legacy_query(tab):
    """Document the former URL for tests and migration diagnostics."""
    if tab not in ADMIN_TABS:
        raise ValueError("Unknown admin tab")
    return "/admin?" + urlencode({"tab": tab})
