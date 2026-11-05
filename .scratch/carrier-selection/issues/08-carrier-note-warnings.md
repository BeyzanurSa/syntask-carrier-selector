# 08: Carrier note warnings

**What to build:** For every selection, the Carrier notes of Eligible carriers are checked against the Order with one Jev Noul question each ("does this note state a restriction or risk relevant to this Order?"). Notes at or above the warning threshold (default 0.7) produce a Note warning shown next to the Carrier with the note text. Warnings never change the selection. If the check cannot run, the response says the notes were not checked.

**Blocked by:** 04, 07

**Status:** ready-for-agent

- [ ] A note judged relevant produces a warning with the Carrier name, note text and probability, and the selected Carrier is the same as without the note (tested with a fake interpreter)
- [ ] Carriers without notes are not sent to Jev
- [ ] When the check fails, the selection still completes and `notes_checked` is false
- [ ] The result screen shows warnings with a clear icon and the note text
- [ ] Demo path works: edit a Carrier note on the Taşıyıcılar page, re-run an Order, and the warning appears
