# Contributing

Small, focused pull requests are welcome. Explain the user problem, behavior change and checks run. Use Python 3.12+ and the pinned requirements, run the offline unit tests and composite check, then inspect the studio in a browser.

Do not make real paid calls in automated tests. Mock provider requests. Test approval invalidation, duplicate-submission guards and recovery whenever those paths change. Never submit keys, signed URLs, model responses, user media or run folders in bug reports or commits.

Include a sanitized error and reproduction steps when reporting a bug. New provider adapters should preserve original audio, persist task IDs before collection, avoid automatic billed retries and clearly describe pricing uncertainty. Contributions are under this project's MIT license.
