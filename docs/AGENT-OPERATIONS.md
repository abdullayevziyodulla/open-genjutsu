# Workflow operations

Follow AGENTS.md. Use workflow.py prepare VIDEO, optionally --mode face_mesh or depth_mesh. Use workflow.py status JOB_ID to inspect review and generation state. A job ID is the local 32-character identifier, not the provider task ID.

Inspect the entire prepared input. Use workflow.py repair-rgb JOB_ID to repair depth masks with original RGB segmentation, then review again. Review approval requires the current fingerprint: workflow.py review JOB_ID --approve --fingerprint HASH --note "Full clip reviewed". Do not approve from sampled checks alone.

Submit only with authorization for the exact prompt and cost: workflow.py submit JOB_ID --prompt-file PROMPT_FILE --reference PHOTO. The optional --second-reference maps another subject. Collect a saved task with workflow.py resume JOB_ID. HD is a separate approved action: workflow.py hd JOB_ID. Use resume --hd for collection, not another HD submission.

When errors occur, inspect persisted intent, response and provider status. Do not remove intent markers to force a new paid attempt. Keep the original soundtrack and review-bound files intact.
