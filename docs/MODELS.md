# Model integrations

Oxen is the default generation backend. It uses Seedance 2.5 reference-to-video, 480p draft quality, output audio disabled, Edit routing for image identity and automatic duration. Private input links are verified before submission. HD completion uses a saved draft task ID and must occur before provider expiry.

Replicate generation supports the included Seedance adapter and Wan 2.2 Animate Replace. Wan accepts one photo and original video; it does not consume depth guidance or a text prompt. Replicate 720p regeneration is a new prediction rather than same-draft completion.

Lec is an optional 720p adapter without draft completion. Provider schema, access, pricing and moderation can change. Check your provider console before paying. No adapter guarantees unrestricted content or exact identity.

Preparation uses hosted Demucs, Depth Anything Video and SAM masks via Replicate. Face mesh is an optional local MediaPipe worker. No hosted model weights are included in this package.
