# IpHub IP Format Enhancement — Design Spec (Sub-1)

> IpMan - Intelligence Package Manager
> Date: 2026-03-16
> Status: Approved
> Scope: Sub-project 1 of 5 (IpHub Awesome-List Transformation)

## 1. Background & Motivation

IpHub currently serves as a flat registry of skill/IP references. To enable "awesome-list" style curation and viral distribution, IpHub needs:

- Richer IP metadata (tags, summaries, links, icons)
- Version iteration with structured changelogs
- Auto-generated Landing Pages for each IP (rich media, newbie-friendly)
- A tag-based discovery and trending system
- i18n support for global reach

This spec (Sub-1) establishes the data model and page generation foundation that all subsequent sub-projects depend on.

## 2. Sub-Project Decomposition

```
Sub-1 (this spec): IP Format + Versioning + Tags + Page Generation
  ↓
Sub-2: Tag Search + Ranking + Trending (depends on Sub-1 tag data)
Sub-3: Author Pages + IP Landing Pages (depends on Sub-1 page infra)
  ↓
Sub-4: Social Media Trend Scraping + Auto IP Generation
  ↓
Sub-5: Automation Orchestration Layer
```

## 3. Three-Layer Architecture

```
User creates/edits       Auto-generated          Auto-generated
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   ip.yaml    │─────→│    ip.md     │─────→│   ip.html    │
│  Machine layer│  ①   │ Intermediate │  ②   │ Presentation │
│  CLI operates │      │ User may     │      │ Landing Page │
│              │      │ override     │      │ GitHub Pages │
└──────────────┘      └──────────────┘      └──────────────┘
                                            ┌──────────────┐
                                      ──②→ │  README.md   │
                                            │ GitHub native│
                                            └──────────────┘
```

**① ip.yaml → ip.md**: GitHub Actions auto-generates from ip.yaml fields + external data (skill descriptions, install counts from index.yaml). If user provides `custom.md` in the registry directory, the auto-generated version is skipped.

**② ip.md → ip.html + README.md**: GitHub Actions renders markdown to HTML via Jinja2 templates with i18n. README.md is also output for GitHub native rendering.

**Trigger**: `rebuild-pages.yml` Action runs after registry changes merge to main.

**Repository layout** (iphub repo):

```
iphub/
  registry/@owner/awesome-frontend/
    meta.yaml                        # existing
    2.0.0.yaml                       # existing
    custom.md                        # optional: user override for ip.md
  pages/@owner/awesome-frontend/
    README.md                        # auto-generated (GitHub native rendering)
    en/index.html                    # auto-generated (GitHub Pages)
    zh-cn/index.html                 # auto-generated (GitHub Pages)
    index.html                       # language redirect
  pages/@owner/
    en/index.html                    # author page
    zh-cn/index.html
  pages/
    en/index.html                    # IpHub homepage with trending
    zh-cn/index.html
    index.html                       # language redirect
  templates/
    ip-landing.html.j2               # Landing Page template
    ip-readme.md.j2                  # README.md template
    author-page.html.j2              # Placeholder (implemented in Sub-3)
    index-page.html.j2               # Placeholder (implemented in Sub-3)
    i18n/
      en.yaml                        # English UI texts
      zh-cn.yaml                     # Chinese UI texts
  scripts/
    generate_pages.py                # Page generation script
    generate_trending.py             # Trending calculation script
  stats/
    snapshots/                       # Daily install count snapshots (30-day retention)
```

## 4. ip.yaml Format Extension

All new fields are **optional**. Backward compatible — old files work unchanged.

```yaml
# === Existing fields (unchanged) ===
name: awesome-frontend
version: "2.0.0"
description: "Frontend developer one-stop skill kit"
author:
  name: "Twisker"
  github: "@twisker"
license: MIT
skills:
  - name: css-helper
  - name: react-patterns
  - name: a11y-checker
dependencies:
  - name: base-utils
    version: ">=1.0.0"

# === New fields (all optional) ===
tags: [frontend, react, css, accessibility]
summary: |
  Covers CSS layout, React patterns, and accessibility checking.
  Install in 10 minutes, start working immediately.
homepage: "https://github.com/twisker/awesome-frontend"
repository: "https://github.com/twisker/awesome-frontend"
icon: "https://raw.githubusercontent.com/.../icon.png"
links:
  - title: "Usage Tutorial"
    url: "https://blog.example.com/guide"
  - title: "Video Demo"
    url: "https://youtube.com/watch?v=xxx"
```

**IPPackage dataclass extension** (`src/ipman/core/package.py`):

```python
@dataclass
class IPPackage:
    # Existing
    name: str
    version: str
    description: str
    skills: list[SkillRef]
    dependencies: list[DependencyRef] = field(default_factory=list)
    author: dict[str, str] | None = None
    license: str | None = None
    # New
    tags: list[str] = field(default_factory=list)
    summary: str | None = None
    homepage: str | None = None
    repository: str | None = None
    icon: str | None = None
    links: list[dict[str, str]] = field(default_factory=list)
```

Parsing compatibility: `parse_ip_file()` uses `dict.get()` with defaults. Old files unaffected.

## 5. Registry Format Extensions

### 5.1 meta.yaml (IP packages)

New optional fields: `tags`, `summary`, `repository`, `icon`, `links`.

```yaml
type: ip
name: awesome-frontend
description: "Frontend developer one-stop skill kit"
author: "@twisker"
license: MIT
homepage: https://github.com/twisker/awesome-frontend
risk_level: LOW
# New
tags: [frontend, react, css, accessibility]
summary: |
  Covers CSS layout, React patterns, and accessibility checking.
  Install in 10 minutes, start working immediately.
repository: "https://github.com/twisker/awesome-frontend"
icon: "https://raw.githubusercontent.com/.../icon.png"
links:
  - title: "Usage Tutorial"
    url: "https://blog.example.com/guide"
```

### 5.2 Skill registry

New optional fields: `tags`, `summary`. The existing `keywords` field is **deprecated in favor of `tags`** — both are accepted during a transition period, with `tags` taking precedence. The `rebuild-index.yml` Action treats `keywords` as a fallback: if `tags` is absent but `keywords` is present, it copies `keywords` to `tags`. No manual migration required.

```yaml
type: skill
name: css-helper
# ... existing fields ...
# Deprecated (still accepted, tags takes precedence)
# keywords: [css, layout, frontend]
# New (replaces keywords)
tags: [css, layout, frontend]
summary: "Smart CSS layout assistant with Grid/Flexbox recommendations"
```

### 5.3 Version files — Changelog

Each version file (`registry/@owner/<name>/2.0.0.yaml`) adds structured `changelog`:

```yaml
version: "2.0.0"
released: 2026-03-16

skills:
  - name: css-helper
  - name: react-patterns
  - name: a11y-checker

dependencies:
  - name: base-utils
    version: ">=1.0.0"

# New
changelog:
  summary: "Added accessibility checking, removed outdated tools"
  added:
    - "a11y-checker skill"
  removed:
    - "css-grid-helper (deprecated)"
  changed:
    - "react-patterns upgraded to v3 compatible"
```

## 6. Tag System + Index Aggregation

### 6.1 Tag flow

```
ip.yaml (tags field)
  → publish writes to registry meta.yaml
    → rebuild-index Action aggregates to index.yaml
      → counter issue auto-syncs GitHub Labels (prefix: "tag:")
```

### 6.2 index.yaml extension

```yaml
# Existing structure — new 'tags' field per entry
skills:
  css-helper:
    owner: "@twisker"
    tags: [css, layout, frontend]          # New
    # ... other fields unchanged

packages:
  awesome-frontend:
    owner: "@twisker"
    tags: [frontend, react, css, accessibility]  # New
    # ... other fields unchanged

# New: tag aggregate index
tags:
  frontend:
    count: 42
    top:
      - awesome-frontend
      - react-patterns
      - css-helper
  react:
    count: 18
    top:
      - awesome-frontend
      - react-patterns

# New: trending data
trending:
  updated: "2026-03-16T04:00:00Z"

  hot_tags:
    - tag: frontend
      weekly_installs: 320
      growth: "+45%"
    - tag: data-science
      weekly_installs: 280
      growth: "+38%"

  rising:
    - name: awesome-frontend
      type: ip
      owner: "@twisker"
      weekly_installs: 89
    - name: a11y-checker
      type: skill
      owner: "@twisker"
      weekly_installs: 67

  new_releases:
    - name: vue-toolkit
      type: ip
      version: "1.0.0"
      released: "2026-03-15"
      owner: "@someone"
```

### 6.3 GitHub Labels sync

In `rebuild-index.yml`, for each skill/IP counter issue:
1. Read tags from registry file
2. Compare with existing issue labels
3. Add/remove labels to match (prefixed `tag:frontend`, `tag:react`)

### 6.4 CLI search enhancement

```bash
ipman hub search --tag frontend        # Filter by tag
ipman hub search react --tag frontend  # Keyword + tag
ipman hub top --tag frontend           # Tag-scoped ranking
```

### 6.5 Trending data sources

| Metric | Data Source | Calculation |
|--------|-----------|-------------|
| Weekly install growth | Counter issue comments (7-day window) | Current count - snapshot from 7 days ago |
| Hot tags | index.yaml tag aggregation | Weighted by associated skill/IP recent installs |
| New releases | Registry `released` dates | Published within last 7 days |
| Active authors | Registry commit history | Authors with publish activity in last 30 days |

Daily snapshots stored in `stats/snapshots/YYYY-MM-DD.yaml` (30-day retention). Cleanup performed by `generate_trending.py` — deletes snapshots older than 30 days on each run.

### 6.6 Trending bootstrap period

During the first 7 days (insufficient snapshot history), `generate_trending.py` outputs:

```yaml
trending:
  updated: "2026-03-16T04:00:00Z"
  bootstrap: true           # signals insufficient data
  hot_tags: []              # empty until 7 days of data
  rising: []
  new_releases:             # this works from day 1 (uses released dates)
    - name: awesome-frontend
      type: ip
      version: "1.0.0"
      released: "2026-03-16"
      owner: "@twisker"
```

The homepage template checks `trending.bootstrap` and shows a "Trending data coming soon" placeholder instead of empty sections.

### 6.7 Tag validation rules

- Lowercase alphanumeric + hyphens only: `^[a-z0-9][a-z0-9\-]{0,28}[a-z0-9]$`
- Min 2 chars, max 30 chars
- Max 10 tags per IP/skill
- Validated by `validate-pr.yaml` during publish

### 6.8 index.yaml size management

The `tags` aggregate and `trending` section add ~5-10KB to index.yaml. At scale (1000+ skills/IPs), this may grow to ~50KB. This is acceptable for the current stage — the CLI fetches index.yaml once per hour (TTL cache). If index.yaml exceeds 200KB in future, split `trending` into a separate `trending.yaml` file fetched on-demand.

## 7. ip.md Auto-Generation

### 7.1 Generation logic

```
registry change merged
  → rebuild-pages.yml Action
    → For each changed IP/skill:
      1. Check for custom.md in registry directory
      2. If exists → use user version
      3. If not → auto-generate from meta.yaml + version files + index data
      4. Output README.md (GitHub native) + HTML (Pages)
```

### 7.2 Auto-generated content structure (template)

```markdown
# {icon} {name}

> {description}

{summary}

## Quick Start

### First time? 3 steps to go

**1. Install Agent** (pick one)
\`\`\`bash
# Claude Code
npm install -g @anthropic-ai/claude-code

# OpenClaw
npm install -g openclaw
\`\`\`

**2. Install IpMan**
\`\`\`bash
pip install ipman-cli
# Or one-line install
curl -fsSL https://raw.githubusercontent.com/twisker/ipman/main/scripts/install.sh | bash
\`\`\`

**3. Install this skill kit**
\`\`\`bash
ipman install {name}
\`\`\`

> What is IpMan? Agent skill virtual environment manager, like conda.
> One-click install, switch, and share AI Agent skill sets.
> [Learn more →](https://twisker.github.io/ipman)

---

## Skills Included ({count})

| Skill | Description | Installs |
|-------|-------------|----------|
{for each skill: row with name, description from index, installs from index}

## Tags

{tag badges}

## Version History

{for each version, newest first:}
### v{version} ({released})
{changelog.summary}
- ✅ Added: {each added item}
- ❌ Removed: {each removed item}
- 🔄 Changed: {each changed item}

## Links

{for each link: markdown link}

## Author

**{author.name}** · [GitHub]({author.github})

---
*Auto-generated by IpHub · [ipman install {name}]*
```

The "Install Agent" section auto-adjusts based on which agents the IP's skills support.

### 7.3 External data enrichment

- Skill descriptions → from `index.yaml` skills section
- Skill install counts → from `index.yaml` installs field
- Changelog → from version files' `changelog` field

### 7.4 User override

Place `custom.md` in the registry directory:

```
registry/@twisker/awesome-frontend/
  meta.yaml
  2.0.0.yaml
  custom.md          ← user-provided, takes priority over auto-generation
```

### 7.5 Publish field mapping (ip.yaml → meta.yaml)

| ip.yaml field | meta.yaml field | Notes |
|---------------|----------------|-------|
| `name` | `name` | Existing |
| `description` | `description` | Existing |
| `author.github` | `author` | Existing (extracts github handle) |
| `license` | `license` | Existing |
| `homepage` | `homepage` | Existing |
| `tags` | `tags` | **New** |
| `summary` | `summary` | **New** |
| `repository` | `repository` | **New** |
| `icon` | `icon` | **New** |
| `links` | `links` | **New** |
| `version` | — | Goes to version file, not meta |
| `skills` | — | Goes to version file |
| `dependencies` | — | Goes to version file |

`generate_package_registry()` and `generate_skill_registry()` are updated to accept and output the new fields.

### 7.6 SEO and language fallback

The root `index.html` language redirect serves **English content by default** with a language switcher banner, rather than a blank JS redirect. This ensures search engine crawlers see real content:

```html
<!-- pages/@owner/awesome-frontend/index.html -->
<html lang="en">
  <!-- Full English content rendered here (same as en/index.html) -->
  <div class="lang-switcher">
    <a href="zh-cn/">中文</a> | <strong>English</strong>
  </div>
  <!-- ... page content ... -->
</html>
```

Crawlers index the English version; users with `zh-CN` locale see a banner suggesting the Chinese version.

## 8. i18n Architecture

### 8.1 Strategy: template-level i18n, data untranslated

| Content | Translated? | Reason |
|---------|-------------|--------|
| Template UI text ("Quick Start", "Skills Included", "Version History") | ✅ Yes | Fixed copy, low maintenance |
| Newbie onboarding (install steps) | ✅ Yes | Core conversion path |
| Author's description/summary | ❌ No | Author content, machine translation unreliable |
| Skill names, tags | ❌ No | Technical terms, keep as-is |
| Changelog | ❌ No | Author content |

### 8.2 Translation files

```yaml
# templates/i18n/en.yaml
quick_start: "Quick Start"
first_time: "First time? 3 steps to go"
install_agent: "Install Agent"
install_ipman: "Install IpMan"
install_this: "Install this skill kit"
what_is_ipman: "What is IpMan? Agent skill virtual environment manager, like conda."
learn_more: "Learn more"
skills_included: "Skills Included"
tags: "Tags"
version_history: "Version History"
author: "Author"
auto_generated: "Auto-generated by IpHub"
added: "Added"
removed: "Removed"
changed: "Changed"
```

```yaml
# templates/i18n/zh-cn.yaml
quick_start: "快速开始"
first_time: "第一次使用？3 步搞定"
install_agent: "安装 Agent"
install_ipman: "安装 IpMan"
install_this: "一键安装本技能包"
what_is_ipman: "什么是 IpMan？Agent 技能虚拟环境管理器，类比 conda。"
learn_more: "了解更多"
skills_included: "包含技能"
tags: "标签"
version_history: "版本历史"
author: "作者"
auto_generated: "由 IpHub 自动生成"
added: "新增"
removed: "移除"
changed: "变更"
```

### 8.3 Page output with i18n

```
pages/@owner/awesome-frontend/
  en/index.html          # English landing page
  zh-cn/index.html       # Chinese landing page
  index.html             # Language redirect (JS: navigator.language)
```

README.md is single-language only (author's original language) — GitHub native rendering does not support language switching.

## 9. Backward Compatibility

1. **All new ip.yaml fields are optional** — missing fields use defaults, no impact on existing functionality.
2. `parse_ip_file()` uses `dict.get()` — old CLI versions ignore unknown fields naturally (`yaml.safe_load` discards nothing, old code simply doesn't read new keys).
3. Landing pages degrade gracefully — missing `summary` falls back to `description`; missing `icon` shows none; missing `tags` shows empty.
4. **No data migration required** — existing registry files work as-is. Newly published entries naturally carry new fields.
5. Existing index.yaml consumers see new `tags` and `trending` keys but ignore them.

## 10. Production Code Changes

### 10.1 ipman CLI repository (`twisker/ipman`)

| File | Change |
|------|--------|
| `src/ipman/core/package.py` | `IPPackage` add tags/summary/homepage/repository/icon/links; `parse_ip_file()` and `dump_ip_file()` adapt |
| `src/ipman/hub/publisher.py` | `generate_package_registry()` and `generate_skill_registry()` output new fields; version files include changelog |
| `src/ipman/hub/client.py` | `search()` supports `--tag` filtering |
| `src/ipman/cli/hub.py` | `hub search` adds `--tag` option; `hub info` displays new fields |
| `tests/` | Corresponding unit test updates |

### 10.2 iphub repository (`twisker/iphub`)

| File | Change |
|------|--------|
| `.github/workflows/rebuild-index.yml` | Aggregate tags → index.yaml; generate trending data; sync GitHub Labels |
| `.github/workflows/rebuild-pages.yml` | **New**: generate README.md + Pages HTML from registry |
| `templates/ip-landing.html.j2` | **New**: Landing Page Jinja2 template |
| `templates/ip-readme.md.j2` | **New**: README.md generation template (with onboarding guide) |
| `templates/author-page.html.j2` | **New**: Author page template |
| `templates/index-page.html.j2` | **New**: IpHub homepage template (with trending) |
| `templates/i18n/en.yaml` | **New**: English UI translations |
| `templates/i18n/zh-cn.yaml` | **New**: Chinese UI translations |
| `scripts/generate_pages.py` | **New**: Page generation script (read registry → render templates) |
| `scripts/generate_trending.py` | **New**: Trending calculation script (read stats/snapshots → output trending) |
| `stats/snapshots/` | **New**: Daily install count snapshot directory |
| `pages/` | **New**: GitHub Pages output directory |

### 10.3 Unchanged

- Existing registry file formats (only new optional fields added)
- Existing ipman CLI command signatures (additive only)
- Existing index.yaml skills/packages structure (only adds `tags` field and `trending` section)
