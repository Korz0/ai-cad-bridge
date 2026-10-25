# Contributing

Start with an issue describing the workflow or reproducible bug. Include the plugin version, Inventor display/major version, Windows and Python versions, and a minimal non-confidential command. Use the compatibility issue template when contributing a new release's live-test evidence.

Keep COM access on its owning STA thread and release it in `finally`. Do not share COM proxies across requests. Preserve the workspace boundary, no-overwrite behavior and rollback semantics. Use documented Autodesk APIs; cite introduction versions for new members. Never label a release tested solely from mocks or version checks.

Run the automated tests; use a new workspace for opt-in live suites. New behavior needs a meaningful test, especially unit conversion, persistent references, file safety and copy modification. Do not commit test models, logs containing private paths, Autodesk DLLs or user photographs. Contributions are provided under the project's MIT license.
