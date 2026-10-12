# Validation and limits

Offline tests cover provider payloads, approval hash gates, private media link verification, duplicate-submission/retry controls, duration normalization and audio restoration. Run the tests on your own environment before release. No model inference is part of the release test suite.

The redesigned studio is checked in the local browser for onboarding, settings, saved input/result loading and responsive overflow. Tests do not guarantee current upstream availability, balance, moderation acceptance, output quality or performance fidelity. Optional face mesh needs its separate worker environment.

The app is single-user and local. Production multi-user hosting is outside this release.
