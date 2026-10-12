# Open Genjutsu workflow instructions

Read README.md and docs/SETUP-AGENT.md for installation. Preserve the current provider choice, credentials, source files and saved jobs. Do not run paid inference, uploads or top-ups during setup or development.

For generation, preserve the complete original video/audio. Isolate vocals, pitch +3 semitones with timing preserved, and embed them in the motion-guidance video. Preserve colored depth output; use raw SAM masks and repair missing subject areas or background spill via original-RGB segmentation when needed.

Review the entire clip before EVERY generation: hands, hair, clothing, cuts, holes, background spill, alignment and flicker. Mesh modes additionally require full facial-tracking review. Sampled contact sheets do not establish full review. Approval is hash-bound to the current artifacts; never approve a known defect or falsely claim full visual review. A user may review and approve the complete input themselves.

Show the exact creative prompt and cost estimate before paid submission. Existing explicit authorization for that exact attempt is sufficient. Never automatically resubmit uncertain or failed paid calls; inspect saved IDs and provider status first. Resume collection rather than requeue. HD requires separate explicit authorization. Match references to the actual subjects; the optional second reference currently represents another person, not another view of the same person.

Use the chosen provider adapter. Oxen uses private repository uploads and verified expiring signed links, with generated audio disabled. Restore the complete untouched original soundtrack after generation. Preserve request IDs, audit files, draft IDs and expiry. Do not promise cheapest pricing, unrestricted support or guaranteed identity/motion quality.

The release contains source only: exclude .env, runtime state, environments, runs, logs, model weights, personal media and Git history. Retain LICENSE and NOTICE. Keep the app on localhost; do not publish an unauthenticated server.
