# Skills

This repository contains local skills.

## Codex

### Install a Skill

Codex loads user-installed skills from:

```bash
${CODEX_HOME:-$HOME/.codex}/skills
```

One-line install for `prepare-rtl-for-synth`:

```bash
tmpdir="$(mktemp -d)" && git clone https://github.com/Emin017/skills.git "$tmpdir/skills" && mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills" && cp -R "$tmpdir/skills/prepare-rtl-for-synth" "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Expanded fresh-clone install:

```bash
tmpdir="$(mktemp -d)"
git clone https://github.com/Emin017/skills.git "$tmpdir/skills"
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R "$tmpdir/skills/prepare-rtl-for-synth" "${CODEX_HOME:-$HOME/.codex}/skills/"
```

To install from an existing local checkout:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R prepare-rtl-for-synth "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Then restart Codex so it can discover the new skill.

### Update an Installed Skill

Replace the installed skill directory with the latest version:

```bash
rm -rf "${CODEX_HOME:-$HOME/.codex}/skills/prepare-rtl-for-synth"
cp -R prepare-rtl-for-synth "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Restart Codex after updating.

### Verify

Check that the installed skill has a `SKILL.md` file:

```bash
ls "${CODEX_HOME:-$HOME/.codex}/skills/prepare-rtl-for-synth/SKILL.md"
```
