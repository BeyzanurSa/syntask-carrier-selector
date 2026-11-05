# 09: Polish, security review and delivery

**What to build:** The application is ready to hand in and to present live. The UI gets a design pass (consistent spacing, typography, readable tables, responsive layout, no unnecessary animation), the codebase is reviewed for architecture issues and leaked secrets, the README explains the system end to end, and the live demo runs reliably without depending on the public distance servers.

**Blocked by:** 01, 02, 03, 04, 05, 06, 07, 08

**Status:** done

- [x] UI pass done on all five pages; layout works on narrow screens
- [x] Full test suite passes; a code review finds no open correctness issues
- [x] Security check: no key in code, logs, README, git or frontend; `.env` ignored; `.env.example` placeholder only
- [x] README covers purpose, architecture diagram, technology choices, folder structure, setup, environment variables, running, endpoints, Jev's role, deterministic parts, confidence behavior, running tests, example requests and responses
- [x] A documented step warms the distance cache for the demo Orders
- [x] The seven-step live demo (add Carrier, edit note, new Order, show selection, show reason, change ranking, re-run and compare) is rehearsed end to end
