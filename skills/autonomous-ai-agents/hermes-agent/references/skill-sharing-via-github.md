# Sharing Skills Between Multiple Hermes Instances via GitHub

## Problem

You run Hermes on two machines (e.g. a Mac Mini and a Linux desktop),
and skills created by the agent only live in `~/.hermes/skills/` on the
local machine. There is no built-in skillsync feature.

## Solution: GitHub Private Repo

Use a git repository as the shared storage for skill files, synced via
`git push` and `git pull` on each machine.

### Setup on Machine A (where skills are created)

```bash
# 1. Authenticate GitHub CLI (one-time)
gh auth login
# Follow device code flow: https://github.com/login/device

# 2. Create private repo and push existing skills
cd ~/.hermes/skills
git init
git add -A
git commit -m "Initial skill import"
gh repo create hermes-skills --private --push --source=. --remote=origin

# Or push to an already-existing repo:
git remote add origin https://github.com/YOUR_USER/hermes-skills.git
git push -u origin main
```

### Setup on Machine B (where skills are consumed)

```bash
# 1. Authenticate first
gh auth login

# 2. Clone into ~/.hermes/skills
cd ~/.hermes
mv skills skills.bak  # backup existing local skills if any
git clone https://github.com/YOUR_USER/hermes-skills.git skills

# 3. Tell Hermes to reload (or restart session)
# In CLI: /reload-skills
```

### Syncing Updates

When a skill is updated on Machine A:

```bash
cd ~/.hermes/skills
git add -A
git commit -m "Update skill X: added Y"
git push
```

Then on Machine B:

```bash
cd ~/.hermes/skills
git pull
hermes skills list  # verify
```

Or set up a cron job to auto-pull:

```bash
# Pull every 30 minutes
cd ~/.hermes/skills && git pull -q
# (Can be a cronjob no_agent script)
```

## Caveats

- **⚠️ Hermes Agent cannot write to git-controlled skills.** When the
  agent uses `skill_manage` tool to create/update a skill, it writes
  files through Hermes's own file tools (not through shell git commands).
  If `~/.hermes/skills/` is a git repo, new/modified files will show as
  untracked changes in git status. The agent must be instructed to
  commit and push after skill changes.

- **⚠️ Concurrent edits across machines.** Git merge conflicts can
  occur if both machines modify the same SKILL.md around the same time.
  The agent can handle merge conflicts via terminal tool if needed.

- **⚠️ Pricer cookies / environment-specific files.** Do NOT commit
  cookie files, `.env` exports, or machine-specific paths. Add a
  `.gitignore`:

```
# ~/.hermes/skills/.gitignore
pricer_cookies/
.env
*.json
```

- **⚠️ `skill_manage(action='create')` writes to `~/.hermes/skills/` directly,
  not through the git repo.** So after creating a skill, run:
  ```bash
  cd ~/.hermes/skills && git add -A && git commit -m "Add new skill" && git push
  ```

- **⚠️ The agent's `skill_manage` tool does NOT know the parent directory
  is a git repo.** It writes files normally. The git workflow (add/commit/push)
  must be done explicitly via terminal tool or explained to the user.

## Method 2: Symlink (Simpler Alternative)

If both machines share a network filesystem (e.g. Synology NAS, Samba, iCloud Drive):

```bash
# On both machines
mv ~/.hermes/skills ~/.hermes/skills_local_backup
ln -s /path/to/shared/folder/hermes-skills ~/.hermes/skills
/usr/libexec/PlistBuddy -c "Add :EnvironmentVariables:HERMES_HOME string /path/to/shared/folder" ~/Library/LaunchAgents/com.user.hermes.plist 2>/dev/null
```

Caveat: file-locking issues if both agents modify the same skill simultaneously.
