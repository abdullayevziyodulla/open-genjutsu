# Input storage

Oxen uploads reviewed inputs to a configured private repository and creates expiring signed download links. The uploader verifies that downloaded bytes match local SHA256 before generation. Create your own private namespace/repository and configure it in API settings.

Replicate uses its file API; Lec uses its temporary-media API. Provider storage, retention and upload billing apply. Local run folders contain private media and signed URLs; never include them in releases. There is no public hosting fallback in the default Oxen path.
