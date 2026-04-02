name: GitHub Push Workflow with PAT
description: Store and use GitHub credentials via git credential helper for secure authentication
type: reference
---

**Workflow**: When pushing to GitHub, store the PAT in `~/.git-credentials` rather than embedding it in remote URLs. This keeps sensitive data out of `.git/config`.

**Steps:**
1. Create remote URL without token: `git remote set-url origin https://github.com/username/repo.git`
2. Store credentials: `echo "https://GITHUB_PAT@github.com" >> ~/.git-credentials`
3. Configure credential helper: `git config --global credential.helper store`

**Why:** Keeps PATs out of git configuration files and allows easy revocation without touching repo URLs.

**How to apply**: For any new project needing GitHub pushes, use this credential storage pattern rather than embedding tokens in remote URLs.
