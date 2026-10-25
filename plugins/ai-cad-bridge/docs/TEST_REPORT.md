# Release 0.2.0 test evidence

Date: **2026-10-25**. Environment: Windows 10 Enterprise x64 (build 19045), CPython 3.14.3 x64, pywin32 312, MCP SDK 1.30.0, Autodesk Inventor 2022 (internal major 26).

| Check | Actual result |
|---|---|
| Validation, compatibility policy, paths, estimates, finishing schema and MCP stdio protocol | 47 pytest tests passed |
| Live Inventor core suite | 21 cases passed |
| Live monolithic/appearance suite | Six checks passed: one body/feature, volume, envelope, reopened RGB, invalid-envelope rollback, unmatched-region rollback |
| Native output | 40 × 30 × 10 mm; 12,000 mm³; one solid, one feature, zero sketches |
| Appearance persistence | Reopened top-Z face RGB 20/95/190; base RGB 30/32/35 |
| Generated preview | Visually inspected; selected face blue, other visible faces dark |
| Portable plugin and MCP manifests | Validated against Agent Plugins 1.0 official JSON schemas |
| Codex CLI marketplace and installation | Registered, installed and listed enabled in an isolated Codex configuration |
| Installed plugin's actual PowerShell launcher and fresh runtime | Real MCP client discovered four tools, read schema/status, validated and created the monolithic colored block successfully |
| PowerShell installer | Executed under Windows PowerShell 5.1 from an extracted ZIP path containing spaces, into a fresh isolated runtime; dependency install and imports passed |

The runtime-only installer route and Codex registration were tested separately to keep the user's normal Codex configuration unchanged. This is an isolated installation on the same computer, **not** a second clean Windows machine.

The initial PowerShell test exposed argument quoting incompatible with PowerShell 5.1; the installer was corrected and rerun successfully. An initial assertion expected the asset's internal name to equal its requested label; Inventor generates that internal name. Verification now checks the display label and actual reopened RGB values. Neither issue remains in the delivered source.

The CLI's optional COM auto-start encountered local error 0x800700c1. Manually launching the installed Inventor worked and all subsequent CAD tests passed. The recommended workflow opens Inventor manually; the package does not rewrite its COM registration.

**Not executed:** Inventor 2017–2021 or 2023–2027; Python 3.11–3.13 runtime matrix; GitHub-hosted Actions; full Codex desktop conversation after reload; installation on another machine. Those tests remain explicitly unverified. The included Windows CI matrix and live suites enable maintainers/users to add evidence.

No CAD files, user photographs or machine-specific raw logs are included in the release archives. All test models were written under development/test folders outside the distributable source.
