# Security

Run Open Genjutsu on localhost for a single user. Credential forms store keys in the ignored project-local .env. The server rejects unrelated browser origins for mutation requests and validates Host headers; these controls do not replace authentication for public hosting.

Do not publish keys, provider responses, signed media URLs or private clips in issues. For a suspected secret leak, rotate the affected key at its provider and remove the exposed material. Before adding remote hosting, implement authentication, authorization, per-user storage, request limits and a durable worker queue.
