# Testing and evidence

## Automated tests without Inventor

Install the package and pytest as shown in README, then run `python -m pytest -q`. Tests include real MCP stdio initialization/tool discovery, valid command validation, rejected path traversal and unsupported operations, version policy, schema validation, measurements and face-region semantics. They do not pretend mocked versions are real CAD integration tests.

GitHub Actions is configured for Windows/Python 3.11–3.14. Its workflow is included; remote CI results exist only after the repository is pushed and Actions runs. Passing local tests does not imply every matrix job has run.

## Live Inventor suite (explicit opt-in)

Open the target Inventor and leave one instance running. Use a NEW directory; existing directories are rejected. These tests create their own documents and close them; they do not delete or modify your existing files.

```powershell
python tests/live_suite.py --workspace test-results/inventor-2022-core
python tests/live_finishing.py --workspace test-results/inventor-2022-finishing
```

The core suite checks 21 cases including extrusion, revolve, holes, cuts, fillets, chamfers, patterns, mirror, workplanes, sketches/constraints, parameters, copy modification, persisted references, assembly constraints, rollback, STEP/STL export, STL millimeter scale and native reopen.

The finishing suite verifies one body/one feature, unchanged volume and envelope, face RGB after native reopen, and rollback on incorrect envelope or unmatched face region. Inspect its generated `colored_block.png` as well.

Record Inventor display version/major, Windows build, Python version and suite summaries. Reports may contain local paths or model details: sanitize them before posting. Never include commercial designs or license information.

See [TEST_REPORT.md](TEST_REPORT.md) for actual evidence from this release. Only 2022 has been executed in the available Inventor environment.
