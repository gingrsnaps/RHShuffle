# V21 race windows

This release pins the bundled deployment state to the requested Eastern windows and verifies schedule persistence after every admin save.

- Shuffle: Nov 17, 2026 6:00 PM EST → Nov 24, 2026 6:00 PM EST.
- EmpireDrop website schedule: Oct 27, 2026 6:00 PM EDT → Nov 28, 2026 6:00 PM EST.

EmpireDrop standings remain sourced from the official selected race slug; its provider-owned start/end dates are shown separately in Admin. The local EmpireDrop window controls RedHunllef countdown/presentation and is preserved independently of Shuffle.

Schedule saves are read back from the atomic JSON store before the UI reports success.
