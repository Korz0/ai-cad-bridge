# Preparing a GitHub release

This deliverable is a repository-ready source package. Creating a GitHub repository, choosing its owner and publishing a release are separate online actions. No remote URL or publisher identity is fabricated in the package.

1. Review the included MIT license and use your intended GitHub account/organization. Rename the repository if desired without changing the plugin's internal name casually.
2. Run unit/protocol tests and the available licensed Inventor live suites. Update `docs/TEST_REPORT.md` with evidence, not inferred success. Keep untested versions labeled as candidates.
3. Run `python scripts/package_release.py --output <outside-directory>`. It uses an explicit source allowlist, excludes CAD models, caches and test artifacts, and produces a repository ZIP, standalone plugin ZIP and SHA256SUMS.
4. Inspect the ZIP contents. Run the installer from an extracted repository ZIP in a path containing spaces. Test MCP startup and a harmless schema request. For a full clean-machine claim, repeat on a separate Windows machine; isolated local testing is not that claim.
5. Upload the repository to your selected GitHub account. Enable Issues, review the Actions results, then tag `v0.2.0` and create a beta release with the repository ZIP and checksums. The standalone plugin ZIP is for plugin import/manual tooling; the repository ZIP includes the installer and is the recommended download.

If using GitHub CLI after creating the intended empty remote, standard `git init`, `git add`, `git commit`, `git remote add origin <your-actual-url>` and `git push` can publish it. Replace the URL with the actual chosen repository; no example account is a real publishing destination.

## Release policy

Update the version in the root portable manifest, compatibility manifest, Python project, tests and changelog together. Rerun install to synchronize runtime/plugin versions. Pin reviewed dependency versions in `requirements-lock.txt`; test all declared Python versions before expanding support claims. The current lock is a tested constraints file, not a hash-locked offline wheelhouse.

Do not ship proprietary CAD models, user photos, saved credentials, `.venv`, pywin32 generated caches or Autodesk DLLs. The source intentionally contains no mini-PC photographs or branded reference model.

## Official plugin directory

GitHub distribution is separate from OpenAI directory submission. Local MCP submissions currently require an eligible/allowlisted organization and review. Do not call this package directory-approved or submission-ready. That route additionally needs verified publisher details, listing URLs/policies, review material and applicable attestations. [Official guidance](https://developers.openai.com/plugins/deploy/desktop-only).
