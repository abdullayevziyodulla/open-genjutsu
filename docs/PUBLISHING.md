# Publish your independent project

Use the source ZIP produced by `scripts/package_release.py`, not this live installation. Extract it into a new folder. The ZIP includes LICENSE, NOTICE, documentation, tests and GitHub Actions, with no Git history, keys, private media or jobs.

1. Create an empty repository in **your own** GitHub account. Choose a name, for example `open-genjutsu`.
2. In the extracted `Open-Genjutsu` folder, initialize a fresh repository:

```bash
git init -b main
git add .
git commit -m "Initial Open Genjutsu release"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Replace both placeholders with your actual destination. Do not push to the upstream creator's repository. Retain LICENSE and NOTICE in every release.

3. Wait for the included offline checks to pass in GitHub Actions. They perform no paid inference.
4. Add repository topics such as `video-editing`, `character-replacement`, `seedance`, `python`, `fastapi` and `open-source`. The description can be: "Local, open-source video character replacement with motion guidance and original-audio restoration. Bring your own API keys."
5. Create a tagged release and attach the source ZIP and its SHA256 file. Include supported providers, setup steps and current limitations. Publish demonstration media only when you have rights to the footage, sound and likenesses.

The README already includes a clean studio screenshot and contribution instructions. Gather feedback through issues; request sanitized errors and reproduction steps rather than private clips or credentials. Multi-user public hosting is a separate engineering project, not a deployment switch.
