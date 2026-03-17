# IpHub IP Format Enhancement — Implementation Plan (Sub-1)

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend IP format with tags/summary/links/changelog, add tag-based search, and build auto-generated landing page infrastructure with i18n.

**Architecture:** Two-repo changes — ipman CLI (Python: data model + publisher + search) and iphub registry (GitHub Actions + Jinja2 templates + Python scripts for page generation). CLI changes are backward-compatible; all new fields optional.

**Tech Stack:** Python 3.12, Click, PyYAML, Jinja2, GitHub Actions, GitHub Pages

**Spec:** `docs/superpowers/specs/2026-03-16-iphub-ip-format-enhancement-design.md`

---

## File Map

### Repo 1: twisker/ipman (CLI)

| File | Action | Responsibility |
|------|--------|---------------|
| `src/ipman/core/package.py` | Modify | IPPackage add 6 new fields; parse_ip_file() + dump_ip_file() adapt |
| `src/ipman/hub/publisher.py` | Modify | generate_*_registry() output new fields; version data includes changelog |
| `src/ipman/hub/client.py` | Modify | search() supports tag filtering |
| `src/ipman/cli/hub.py` | Modify | `hub search --tag`, `hub info` shows new fields, `hub top --tag` |
| `tests/test_core/test_package.py` | Modify | Tests for new fields in parse/dump |
| `tests/test_hub/test_publisher.py` | Modify | Tests for new fields in registry generation |
| `tests/test_hub/test_client.py` | Modify | Tests for tag-based search |
| `tests/test_cli/test_hub.py` | Modify | Tests for --tag CLI option |

### Repo 2: twisker/iphub (Registry)

| File | Action | Responsibility |
|------|--------|---------------|
| `templates/ip-readme.md.j2` | Create | README.md generation template with onboarding |
| `templates/ip-landing.html.j2` | Create | HTML Landing Page template |
| `templates/i18n/en.yaml` | Create | English UI translations |
| `templates/i18n/zh-cn.yaml` | Create | Chinese UI translations |
| `scripts/generate_pages.py` | Create | Read registry → render templates → output pages/ |
| `scripts/generate_trending.py` | Create | Read stats/snapshots → compute trending → update index |
| `.github/workflows/rebuild-index.yml` | Modify | Add tag aggregation, trending computation, Labels sync |
| `.github/workflows/rebuild-pages.yml` | Create | Trigger page generation after registry changes |
| `.github/workflows/validate-pr.yml` | Modify | Add tag validation rules |

---

## Chunk 1: ipman CLI — Data Model Extension

### Task 1: Extend IPPackage dataclass with new fields

**Files:**
- Modify: `src/ipman/core/package.py`
- Modify: `tests/test_core/test_package.py`

- [ ] **Step 1: Write failing test for new fields in parse_ip_file()**

Append to `tests/test_core/test_package.py`:

```python
def test_parse_ip_file_with_new_fields(tmp_path):
    """New optional fields (tags, summary, etc.) are parsed correctly."""
    content = textwrap.dedent("""\
        name: extended-kit
        version: "1.0.0"
        description: "Test kit"
        skills:
          - name: skill-a
        tags: [frontend, react]
        summary: "A test summary"
        homepage: "https://example.com"
        repository: "https://github.com/test/repo"
        icon: "https://example.com/icon.png"
        links:
          - title: "Guide"
            url: "https://example.com/guide"
    """)
    f = tmp_path / "extended.ip.yaml"
    f.write_text(content)
    pkg = parse_ip_file(f)
    assert pkg.tags == ["frontend", "react"]
    assert pkg.summary == "A test summary"
    assert pkg.homepage == "https://example.com"
    assert pkg.repository == "https://github.com/test/repo"
    assert pkg.icon == "https://example.com/icon.png"
    assert pkg.links == [{"title": "Guide", "url": "https://example.com/guide"}]


def test_parse_ip_file_without_new_fields(tmp_path):
    """Old files without new fields still parse (backward compat)."""
    content = textwrap.dedent("""\
        name: old-kit
        version: "1.0.0"
        description: "Old format"
        skills:
          - name: skill-a
    """)
    f = tmp_path / "old.ip.yaml"
    f.write_text(content)
    pkg = parse_ip_file(f)
    assert pkg.tags == []
    assert pkg.summary is None
    assert pkg.homepage is None
    assert pkg.links == []


def test_dump_ip_file_with_new_fields(tmp_path):
    """New fields are written to .ip.yaml."""
    pkg = IPPackage(
        name="dump-test", version="1.0.0", description="Test",
        skills=[SkillRef(name="s1")],
        tags=["ai", "coding"],
        summary="A summary",
        homepage="https://example.com",
    )
    out = tmp_path / "dump.ip.yaml"
    dump_ip_file(pkg, out)
    data = yaml.safe_load(out.read_text())
    assert data["tags"] == ["ai", "coding"]
    assert data["summary"] == "A summary"
    assert data["homepage"] == "https://example.com"
```

Add `import textwrap` if not already present.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_core/test_package.py::test_parse_ip_file_with_new_fields -v`
Expected: FAIL — `IPPackage` has no `tags` attribute.

- [ ] **Step 3: Extend IPPackage dataclass**

In `src/ipman/core/package.py`, add to `IPPackage` dataclass after `license`:

```python
    tags: list[str] = field(default_factory=list)
    summary: str | None = None
    homepage: str | None = None
    repository: str | None = None
    icon: str | None = None
    links: list[dict[str, str]] = field(default_factory=list)
```

- [ ] **Step 4: Update parse_ip_file()**

In `parse_ip_file()`, after existing field extraction, add:

```python
    tags=data.get("tags", []),
    summary=data.get("summary"),
    homepage=data.get("homepage"),
    repository=data.get("repository"),
    icon=data.get("icon"),
    links=data.get("links", []),
```

- [ ] **Step 5: Update dump_ip_file()**

In `dump_ip_file()`, after existing fields, add (only if non-empty/non-None):

```python
    if pkg.tags:
        d["tags"] = pkg.tags
    if pkg.summary:
        d["summary"] = pkg.summary
    if pkg.homepage:
        d["homepage"] = pkg.homepage
    if pkg.repository:
        d["repository"] = pkg.repository
    if pkg.icon:
        d["icon"] = pkg.icon
    if pkg.links:
        d["links"] = pkg.links
```

- [ ] **Step 6: Run all package tests**

Run: `uv run pytest tests/test_core/test_package.py -v`
Expected: All pass including 3 new tests.

- [ ] **Step 7: Run full test suite**

Run: `uv run pytest tests/ --ignore=tests/e2e -v`
Expected: All pass.

- [ ] **Step 8: Commit**

```bash
git add src/ipman/core/package.py tests/test_core/test_package.py
git commit -m "feat: extend IPPackage with tags/summary/links/icon fields"
```

### Task 2: Update publisher to output new fields + changelog

**Files:**
- Modify: `src/ipman/hub/publisher.py`
- Modify: `tests/test_hub/test_publisher.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_hub/test_publisher.py`:

```python
def test_generate_package_registry_with_new_fields():
    """New fields (tags, summary, etc.) appear in registry output."""
    result = generate_package_registry(
        name="test-pkg", description="Test", author="@tester",
        tags=["ai", "coding"], summary="A summary",
        repository="https://github.com/test/repo",
        icon="https://example.com/icon.png",
        links=[{"title": "Guide", "url": "https://example.com"}],
    )
    assert result["tags"] == ["ai", "coding"]
    assert result["summary"] == "A summary"
    assert result["repository"] == "https://github.com/test/repo"
    assert result["icon"] == "https://example.com/icon.png"
    assert result["links"] == [{"title": "Guide", "url": "https://example.com"}]


def test_generate_skill_registry_with_tags():
    """Skill registry outputs tags and summary."""
    result = generate_skill_registry(
        name="test-skill", description="Test", author="@tester",
        tags=["css", "layout"], summary="A CSS helper",
    )
    assert result["tags"] == ["css", "layout"]
    assert result["summary"] == "A CSS helper"


def test_generate_version_data_with_changelog():
    """Version data includes structured changelog."""
    from ipman.core.package import IPPackage, SkillRef
    pkg = IPPackage(
        name="test", version="2.0.0", description="Test",
        skills=[SkillRef(name="s1")],
    )
    changelog = {
        "summary": "Added new skill",
        "added": ["s1"],
        "removed": [],
        "changed": [],
    }
    result = generate_version_data(pkg, changelog=changelog)
    assert result["changelog"]["summary"] == "Added new skill"
    assert result["changelog"]["added"] == ["s1"]
```

- [ ] **Step 2: Run to verify failures**

Run: `uv run pytest tests/test_hub/test_publisher.py::test_generate_package_registry_with_new_fields -v`

- [ ] **Step 3: Update generate_package_registry()**

Add new parameters: `tags`, `summary`, `repository`, `icon`, `links` (all optional, default None). Include in output dict when non-None.

- [ ] **Step 4: Update generate_skill_registry()**

Add `tags` and `summary` parameters. Include in output when non-None. Deprecation note: still accept `keywords` param but map it to `tags` internally.

- [ ] **Step 5: Update generate_version_data()**

Add `changelog` parameter (dict or None). Include in output when provided.

- [ ] **Step 6: Update IpHubPublisher.publish_package() and publish_skill()**

Pass new fields from IPPackage/CLI args through to the generate_*() functions.

- [ ] **Step 7: Run all publisher tests**

Run: `uv run pytest tests/test_hub/test_publisher.py -v`

- [ ] **Step 8: Commit**

```bash
git add src/ipman/hub/publisher.py tests/test_hub/test_publisher.py
git commit -m "feat: publisher outputs tags/summary/changelog in registry files"
```

### Task 3: Add tag-based search to client

**Files:**
- Modify: `src/ipman/hub/client.py`
- Modify: `tests/test_hub/test_client.py`

- [ ] **Step 1: Write failing test**

```python
def test_search_by_tag(mock_index):
    """Search filters by tag when provided."""
    # mock_index should have skills/packages with tags field
    client = IpHubClient(cache_dir=tmp_path)
    # ... setup mock index with tags ...
    results = client.search("", tag="frontend")
    assert all("frontend" in r.get("tags", []) for r in results)
```

- [ ] **Step 2: Implement tag filtering in search()**

Add `tag: str | None = None` parameter to `search()`. When provided, filter results where `tag in entry.get("tags", [])`.

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_hub/test_client.py -v`

- [ ] **Step 4: Commit**

```bash
git add src/ipman/hub/client.py tests/test_hub/test_client.py
git commit -m "feat: hub client supports tag-based search filtering"
```

### Task 4: Add --tag option to CLI hub commands

**Files:**
- Modify: `src/ipman/cli/hub.py`
- Modify: `tests/test_cli/test_hub.py`

- [ ] **Step 1: Write failing test**

```python
def test_hub_search_with_tag(runner, mock_client):
    """hub search --tag filters results."""
    result = runner.invoke(cli, ["hub", "search", "--tag", "frontend"])
    assert result.exit_code == 0
```

- [ ] **Step 2: Add --tag option to hub search command**

```python
@hub.command()
@click.argument("query", default="")
@click.option("--tag", default=None, help="Filter by tag")
@click.option("--agent", default=None)
def search(query, tag, agent):
    ...
    results = client.search(query, agent=agent, tag=tag)
```

- [ ] **Step 3: Add --tag to hub top command**

Similar pattern.

- [ ] **Step 4: Update hub info to display new fields**

Show tags, summary, links, changelog when available.

- [ ] **Step 5: Run CLI tests**

Run: `uv run pytest tests/test_cli/test_hub.py -v`

- [ ] **Step 6: Run full test suite**

Run: `uv run pytest tests/ --ignore=tests/e2e -v`

- [ ] **Step 7: Commit**

```bash
git add src/ipman/cli/hub.py tests/test_cli/test_hub.py
git commit -m "feat: hub search/top support --tag option, info shows new fields"
```

---

## Chunk 2: iphub Repository — Templates + Scripts + Workflows

> **Note:** This chunk operates on the `twisker/iphub` repository, not the ipman CLI repo. The implementer must clone iphub separately or work in a different directory.

### Task 5: Create i18n translation files

**Files:**
- Create: `templates/i18n/en.yaml`
- Create: `templates/i18n/zh-cn.yaml`

- [ ] **Step 1: Create English translations**

```yaml
# templates/i18n/en.yaml
quick_start: "Quick Start"
first_time: "First time? 3 steps to go"
install_agent: "Install Agent"
install_agent_pick: "pick one"
install_ipman: "Install IpMan"
install_this: "Install this skill kit"
or_one_line: "Or one-line install"
what_is_ipman: "What is IpMan? Agent skill virtual environment manager, like conda."
what_is_ipman_detail: "One-click install, switch, and share AI Agent skill sets."
learn_more: "Learn more"
skills_included: "Skills Included"
skill: "Skill"
description: "Description"
installs: "Installs"
tags: "Tags"
version_history: "Version History"
links: "Links"
author: "Author"
auto_generated: "Auto-generated by IpHub"
added: "Added"
removed: "Removed"
changed: "Changed"
trending_coming_soon: "Trending data coming soon — check back in a few days!"
```

- [ ] **Step 2: Create Chinese translations**

```yaml
# templates/i18n/zh-cn.yaml
quick_start: "快速开始"
first_time: "第一次使用？3 步搞定"
install_agent: "安装 Agent"
install_agent_pick: "选一个"
install_ipman: "安装 IpMan"
install_this: "一键安装本技能包"
or_one_line: "或一键安装"
what_is_ipman: "什么是 IpMan？Agent 技能虚拟环境管理器，类比 conda。"
what_is_ipman_detail: "一键安装、切换、分享 AI Agent 的技能组合。"
learn_more: "了解更多"
skills_included: "包含技能"
skill: "技能"
description: "描述"
installs: "安装量"
tags: "标签"
version_history: "版本历史"
links: "相关链接"
author: "作者"
auto_generated: "由 IpHub 自动生成"
added: "新增"
removed: "移除"
changed: "变更"
trending_coming_soon: "趋势数据正在收集中，请几天后再来查看！"
```

- [ ] **Step 3: Commit**

```bash
git add templates/i18n/
git commit -m "feat: add i18n translation files (en + zh-cn)"
```

### Task 6: Create README.md generation template

**Files:**
- Create: `templates/ip-readme.md.j2`

- [ ] **Step 1: Write the Jinja2 template**

The template renders a complete README.md from registry data + index data + i18n strings. Include:
- IP name and description
- Onboarding guide (agent install → ipman install → install this IP)
- Skills table with descriptions and install counts
- Tags as badges
- Version history with structured changelog
- Links section
- Author section
- IpMan promotion footer

The "Install Agent" section should conditionally show only agents that the IP supports.

See spec Section 7.2 for the exact content structure.

- [ ] **Step 2: Commit**

```bash
git add templates/ip-readme.md.j2
git commit -m "feat: add README.md Jinja2 template with onboarding guide"
```

### Task 7: Create HTML Landing Page template

**Files:**
- Create: `templates/ip-landing.html.j2`

- [ ] **Step 1: Write the HTML template**

A self-contained HTML page with:
- Embedded CSS (no external dependencies for GitHub Pages reliability)
- Language switcher banner
- Same content structure as README template but with richer styling
- Responsive design (mobile-friendly)
- Copy-to-clipboard for install commands
- i18n: all UI text from translation vars

- [ ] **Step 2: Commit**

```bash
git add templates/ip-landing.html.j2
git commit -m "feat: add HTML landing page template with i18n"
```

### Task 8: Create page generation script

**Files:**
- Create: `scripts/generate_pages.py`

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Generate README.md + HTML landing pages from registry data.

Usage: python scripts/generate_pages.py [--changed-only]

Reads: registry/, index.yaml, templates/
Writes: pages/
"""
```

Core logic:
1. Load index.yaml for skill descriptions and install counts
2. For each IP package in registry/:
   a. Load meta.yaml + all version files
   b. Check for custom.md (user override)
   c. If no custom.md, auto-generate markdown from template
   d. Render README.md → `pages/@owner/<name>/README.md`
   e. For each language (en, zh-cn):
      - Load i18n strings
      - Render HTML → `pages/@owner/<name>/<lang>/index.html`
   f. Render root index.html (English default + language switcher)
3. For each skill in registry/ (simpler page, no version history)

The `--changed-only` flag limits processing to registry entries modified in the latest commit (for CI efficiency).

- [ ] **Step 2: Add unit tests**

Create `scripts/test_generate_pages.py` with tests for:
- Template rendering with full data
- Template rendering with missing optional fields (graceful degradation)
- custom.md override takes priority
- i18n strings substituted correctly

- [ ] **Step 3: Commit**

```bash
git add scripts/generate_pages.py scripts/test_generate_pages.py
git commit -m "feat: add page generation script with i18n and custom.md support"
```

### Task 9: Create trending calculation script

**Files:**
- Create: `scripts/generate_trending.py`

- [ ] **Step 1: Write the script**

```python
#!/usr/bin/env python3
"""Calculate trending data from install count snapshots.

Usage: python scripts/generate_trending.py

Reads: stats/snapshots/, index.yaml
Writes: trending section appended to index.yaml
Also: creates today's snapshot, cleans up snapshots older than 30 days.
"""
```

Core logic:
1. Create today's snapshot from current index.yaml install counts
2. Load snapshot from 7 days ago (if exists)
3. Calculate weekly growth per skill/IP
4. Aggregate by tag → hot_tags (weighted by growth)
5. Find rising entries (new + fast-growing)
6. Find new_releases (released in last 7 days)
7. If < 7 days of snapshots, set `bootstrap: true`
8. Write trending section to index.yaml
9. Delete snapshots older than 30 days

- [ ] **Step 2: Commit**

```bash
git add scripts/generate_trending.py
git commit -m "feat: add trending calculation script with bootstrap handling"
```

### Task 10: Update rebuild-index.yml for tags + trending + Labels

**Files:**
- Modify: `.github/workflows/rebuild-index.yml`

- [ ] **Step 1: Add tag aggregation step**

After existing index rebuild, add:
- Scan all registry files for `tags` field (and `keywords` fallback)
- Build `tags:` section in index.yaml with counts and top entries per tag

- [ ] **Step 2: Add trending calculation step**

```yaml
- name: Calculate trending
  run: python scripts/generate_trending.py
```

- [ ] **Step 3: Add GitHub Labels sync step**

```yaml
- name: Sync tag labels to counter issues
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: python scripts/sync_tag_labels.py
```

Create `scripts/sync_tag_labels.py` — reads registry tags, compares with issue labels, adds/removes `tag:*` labels.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/rebuild-index.yml scripts/sync_tag_labels.py
git commit -m "ci: rebuild-index adds tag aggregation, trending, and label sync"
```

### Task 11: Create rebuild-pages.yml workflow

**Files:**
- Create: `.github/workflows/rebuild-pages.yml`

- [ ] **Step 1: Write the workflow**

```yaml
name: Rebuild Pages

on:
  push:
    branches: [main]
    paths: ["registry/**"]
  workflow_dispatch:

jobs:
  generate-pages:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install jinja2 pyyaml markdown

      - name: Generate pages
        run: python scripts/generate_pages.py

      - name: Commit and push pages
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add pages/
          git diff --staged --quiet || git commit -m "Auto-generate pages [skip ci]"
          git push
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/rebuild-pages.yml
git commit -m "ci: add rebuild-pages workflow for auto-generated landing pages"
```

### Task 12: Update validate-pr.yml with tag validation

**Files:**
- Modify: `.github/workflows/validate-pr.yml`

- [ ] **Step 1: Add tag validation rules**

In the YAML validation step, add checks:
- Tags match pattern `^[a-z0-9][a-z0-9\-]{0,28}[a-z0-9]$`
- Max 10 tags per entry
- Min 2, max 30 chars per tag

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/validate-pr.yml
git commit -m "ci: validate-pr enforces tag format and count limits"
```

### Task 13: Enable GitHub Pages on iphub repo

This is a **manual step** — the implementer must:
1. Go to `twisker/iphub` → Settings → Pages
2. Set source to "Deploy from a branch"
3. Set branch to `main`, folder to `/pages`
4. Save

- [ ] **Step 1: Document this in the repo README**

Add a note about GitHub Pages configuration.

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add GitHub Pages setup instructions"
```

---

## Chunk 3: Integration Verification

### Task 14: End-to-end verification on ipman CLI

- [ ] **Step 1: Run full ipman test suite**

Run: `uv run pytest tests/ --ignore=tests/e2e -v`
Expected: All pass.

- [ ] **Step 2: Run lint + type check**

Run: `uv run ruff check src/ tests/ && uv run mypy src/`
Expected: Clean.

- [ ] **Step 3: Manual test — publish with new fields**

```bash
# Create a test IP with new fields
cat > /tmp/test.ip.yaml << 'EOF'
name: test-enhanced
version: "1.0.0"
description: "Test IP with enhanced format"
skills:
  - name: test-skill
tags: [test, e2e]
summary: "Testing enhanced IP format"
links:
  - title: "Test"
    url: "https://example.com"
EOF

ipman hub info test-enhanced  # Should show tags, summary, links
```

- [ ] **Step 4: Commit any fixes**

### Task 15: End-to-end verification on iphub repo

- [ ] **Step 1: Test page generation locally**

```bash
cd /path/to/iphub
python scripts/generate_pages.py
# Verify pages/ directory has expected structure
ls pages/
```

- [ ] **Step 2: Test trending calculation**

```bash
python scripts/generate_trending.py
# Verify index.yaml has trending section with bootstrap: true
grep "bootstrap:" index.yaml
```

- [ ] **Step 3: Open generated HTML in browser**

Verify landing page renders correctly with i18n and onboarding guide.

- [ ] **Step 4: Push and verify GitHub Pages**

After push, check `https://twisker.github.io/iphub/` loads correctly.
