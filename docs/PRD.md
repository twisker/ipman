# IpMan Software Requirements Document

## 1. Introduction

### 1.1 Background
With the increasing popularity of Agent tools such as OpenClaw and Claude Code, writing skills for them has become a trend. However, due to the existence of many skills with the same name, users face chaos when searching for, installing, and managing different versions of skills—similar to the early challenges of Python environment management. To address this issue, a virtual environment management tool specifically for skills is needed to achieve isolation, dependency management, and distribution of skill environments.

### 1.2 Goals
Develop a command-line tool named **IpMan (intelligence package manager)** to achieve the following core objectives:
- Provide virtual environment management for skills (analogous to Python's virtualenv/conda/uv).
- Support mainstream Agent tools (at least OpenClaw and Claude Code).
- Cross-platform support (Linux, macOS, Windows).
- Allow packaging a set of skills into a text-file-based **Intelligence Package (IP)** for easy installation and distribution.
- Provide an IpHub (analogous to PyPI).
- Maintain decoupling from Agent tools' internal structures by managing skills through standard commands rather than hacking into tool-specific directories.

## 2. Overall Description

### 2.1 Product Scope
IpMan is a pure command-line tool focused on managing Agent skill environments. It allows users to create, switch, delete virtual environments; install, uninstall, publish skills and IP packages; and interact with the IpHub. IpMan does not modify the internal implementation of Agent tools; instead, it achieves isolation by calling the Agent's standard skill management interfaces or manipulating skill storage directories (via symbolic links, etc.).

### 2.2 User Characteristics
- **Skill Developers**: Need to isolate skill environments for different projects to avoid version conflicts; want to publish their skills or IP packages to IpHub.
- **Skill Users**: Want to quickly install and try different skills, switch environments between projects; need clear details about skills (function, author, version, etc.) to avoid confusion.
- **Project Maintainers**: Need to define a fixed set of skill dependencies for a project to facilitate team collaboration and deployment.

### 2.3 Assumptions and Dependencies
- Users have installed one or more supported Agent tools (OpenClaw, Claude Code, etc.).
- The IpHub leverages free GitHub infrastructure (e.g., GitHub Issues, GitHub Pages, or GitHub Actions) for simple data storage and counting; if not feasible, low-cost OSS solutions are used.
- User systems have a Python runtime environment (IpMan itself is written in Python).
- Internet connectivity is available for accessing the IpHub.

## 3. Functional Requirements

### 3.1 Virtual Environment Management
| ID   | Description | Source |
|------|-------------|--------|
| FR1  | Provide capabilities to create, activate, deactivate, delete, and list virtual environments. | Main Goal 1 |
| FR2  | Virtual environments should be implemented using symbolic links to separate actual skill storage from project environments (similar to nvm's handling of npm), facilitating switching and isolation. | Detail 1 |
| FR3  | Support creating virtual environments for different scopes:<br>- `--project`: create environment in the current project directory (default).<br>- `--user`: create environment for the current user.<br>- `--machine`: create environment for the entire machine. | Detail 28 |
| FR4  | After environment activation, the system command prompt should change noticeably to remind the user they are in an IpMan-managed virtual environment. The prompt format must be clearly distinguishable from Python virtual environments (e.g., virtualenv). | Detail 31 |

### 3.2 Skill Management
| ID   | Description | Source |
|------|-------------|--------|
| FR5  | Support installing, uninstalling, upgrading, and listing skills within a virtual environment. Skill management should draw inspiration from `uv` (e.g., fast dependency resolution, lock files). | Main Goal 2, Detail 2 |
| FR6  | When installing a skill, detailed metadata must be recorded: brief description, detailed description, source URL, version, author, dependencies, etc., to resolve confusion caused by skills with the same name. | Detail 5, 17 |
| FR7  | Support installing individually published skills (i.e., not packaged as an IP) within a virtual environment, and such skills must include metadata (brief description, short name, version, dependencies, etc.) upon publication. | Detail 17 |
| FR8  | Support offline installation of skills or IP packages from a local IP file. | Detail 7 |
| FR9  | Support online installation of skills or IP packages by simple name from IpHub (similar to pip's `install <package>`). | Detail 8 |
| FR10 | Support automatic resolution and installation of skill dependencies (including recursive dependencies of IP packages). | Detail 21 |

### 3.3 IP Package Management
| ID   | Description | Source |
|------|-------------|--------|
| FR11 | Support packaging a set of skills into an IP package, defined by a text file (format to be determined: JSON/YAML/TXT, to be considered). | Main Goal 4, Detail 3 |
| FR12 | The IP text file must include:<br>- Package basic information: name, version, brief description, detailed description, author info.<br>- List of referenced skills: each skill must include function description, source URL, version, author, etc.<br>- Dependencies on other IP packages (support recursive references).<br>- Support for comments. | Detail 4, 5, 20, 24 |
| FR13 | IP files automatically generated by IpMan should include a header comment with a reference to the IpMan project repository and brief installation instructions, so anyone who obtains the IP file knows how to install it. | Detail 25 |
| FR14 | Support exporting the skills in the current virtual environment to an IP file. | Implicit |
| FR15 | Support installing all skills from an IP file into the current virtual environment, automatically handling dependencies. | Detail 7, 21 |

### 3.4 Marketplace Interaction
| ID   | Description | Source |
|------|-------------|--------|
| FR16 | Provide an IpHub that allows users to search, browse, and download skills and IP packages. | Main Goal 5 |
| FR17 | IpHub should record installation/download counts for each skill and IP package, and support rankings (Top 10/20/50). | Detail 6, 20 |
| FR18 | Support publishing local skills or IP packages to IpHub (user authentication required; method TBD). | Detail 8 |
| FR19 | Persistent data for IpHub should prioritize free GitHub resources (e.g., Issues, Pages, Actions); if not feasible, use public free infrastructure; finally consider low-cost OSS. | Detail 9 |
| FR20 | The project homepage (README) should dynamically display the Top 10 skills and Top 10 IP packages rankings. | Detail 22 |
| FR21 | The project homepage should also display a trend chart of the project's GitHub stars. | Detail 23 |

### 3.5 Project Integration and Tool Detection
| ID   | Description | Source |
|------|-------------|--------|
| FR22 | IpMan should detect supported Agent tools (e.g., OpenClaw, Claude Code) installed on the local machine and their versions. | Detail 29 |
| FR23 | When run in a project directory, IpMan should automatically guess the Agent tool used by the project based on project files and directory structure, and create a skill environment for that tool. | Detail 26 |
| FR24 | Allow users to explicitly specify the target Agent tool via an argument (`--agent`), overriding automatic detection. | Detail 26 |
| FR25 | When creating a virtual environment, if the current project already has some skills installed (e.g., in a global scope), provide an argument (`--inherit`) to let users choose whether to inherit those installed skills into the new environment. | Detail 27 |

### 3.6 Command Line Interface
| ID   | Description | Source |
|------|-------------|--------|
| FR26 | All commands, parameters, and help text should default to English. If the system environment supports Chinese (e.g., `LANG` environment variable contains `zh`), explanatory and prompt text should automatically switch to Chinese. | Detail 10 |
| FR27 | Provide comprehensive help documentation and tutorials, including both English and Chinese versions. | Detail 11 |
| FR28 | The documentation must include the schema (format specification) of the IP text file format. | Detail 30 |

## 4. Non-Functional Requirements

### 4.1 Platform Compatibility
| ID   | Description | Source |
|------|-------------|--------|
| NFR1 | The tool must support Linux, macOS, and Windows operating systems. | Main Goal 3 |
| NFR2 | On Windows, provide pre-compiled executables and installers, and support automated CI/CD packaging. | Detail 14, 19 |

### 4.2 Usability
| ID   | Description | Source |
|------|-------------|--------|
| NFR3 | The tool should remain decoupled from Agent internal structures. All skill installation/uninstallation operations should be performed by calling the Agent's standard interfaces or via symbolic links, avoiding direct intrusion into Agent-specific directory structures. | Main Goal 6 |
| NFR4 | Environment switching should be fast and reliable, without interfering with other projects or Agents on the same machine. | Implicit |

### 4.3 Documentation and Internationalization
| ID   | Description | Source |
|------|-------------|--------|
| NFR5 | Provide complete help documentation and tutorials in both English and Chinese, and generate them automatically via CI/CD (e.g., building from Markdown sources to HTML/PDF). | Detail 11, 15 |
| NFR6 | The documentation must include a detailed schema description of the IP file format. | Detail 30 |

### 4.4 Release and Installation
| ID   | Description | Source |
|------|-------------|--------|
| NFR7 | IpMan itself should support multiple installation methods:<br>- Via PyPI (`pip install ipman`).<br>- Via curl+shell script (for Unix-like systems).<br>- Windows installers (e.g., .exe or .msi). | Detail 13 |
| NFR8 | Each version release should provide source tarballs as well as Windows pre-compiled versions and installers. | Detail 14 |
| NFR9 | All release artifacts should be generated and published via an automated CI/CD process. | Detail 14 |
| NFR10 | Upon version release, the CI/CD process should automatically publish the IpMan package to PyPI. | New |

### 4.5 Development and Testing
| ID   | Description | Source |
|------|-------------|--------|
| NFR11 | The development process should follow TDD (Test-Driven Development). Before each version release, all test cases must pass on all three target platforms (Linux, macOS, Windows). | Detail 18 |
| NFR12 | An automated testing framework must be set up to run test cases on all three platforms. | Detail 18 |
| NFR13 | The project must be hosted on GitHub and utilize GitHub Actions (or similar) for CI/CD. | Detail 16 |
| NFR14 | The project codebase must follow Git Flow branching rules, and the release process should be triggered when a release branch is merged into the main branch. | New |

### 4.6 Data Storage and Statistics
| ID   | Description | Source |
|------|-------------|--------|
| NFR15 | Installation/download statistics for the IpHub should be accurately recorded and used for ranking displays. | Detail 6, 20 |
| NFR16 | Data storage should prioritize free GitHub resources (e.g., counting via GitHub Issues, static data via GitHub Pages) with consideration for data persistence. | Detail 9 |

## 5. External Interface Requirements

### 5.1 User Interface
- **Command Line Interface**: All functionality is exposed via command-line commands, following common CLI conventions (e.g., `ipman create`, `ipman activate`, `ipman install`). Support `--help` for assistance.

### 5.2 Interface with Agent Tools
- **Skill Installation/Uninstallation**: IpMan must call the standard skill management commands provided by the Agent tool, or manipulate skill storage directories via symbolic links. Implementation must adapt to different Agents while keeping internal logic decoupled.

### 5.3 Interface with Online Marketplace
- **HTTP/HTTPS Communication**: Used to download skill metadata and package content, upload packages, retrieve statistics, etc. IpHub may provide a RESTful API.

## 6. Constraints

- **Development Language**: IpMan must be implemented in Python.
- **Open Source Hosting**: The project must be hosted on GitHub with an appropriate open-source license (e.g., MIT, Apache 2.0).
- **Version Management**: Follow Semantic Versioning (SemVer).
- **Branching Model**: The project codebase must follow Git Flow branching rules, with release processes triggered when a release branch is merged into main. (Already covered in NFR14)
- **Dependency Management**: Minimize external dependencies or ensure cross-platform compatibility.

---

## Appendix A: Draft IP Text File Format (TBD)
- Possible formats: JSON, YAML, or custom TXT. Must support comments.
- Example structure (YAML):
  ```yaml
  # IpMan package file - see https://github.com/twisker/ipman for installation
  name: my-skillset
  version: 1.0.0
  description: A collection of useful skills for web research
  author:
    name: John Doe
    email: john@example.com
  skills:
    - name: web-scraper
      version: 2.1.0
      source: https://github.com/agent-skills/web-scraper
      description: Extracts data from websites
      author: Agent Skills Team
    - name: summarizer
      version: 1.3.2
      source: https://github.com/other/summarizer
      description: Summarizes text using NLP
  dependencies:
    - base-utils@^1.0.0
  ```
- The exact schema will be defined in subsequent documentation.

---

## 7. Security Requirements (v2.0)

> Added 2026-03-14. Addresses the growing threat of malicious AI agent skills.
> References: [Skill Vetter](https://clawhub.ai/spclaudehome/skill-vetter), [Snyk ToxicSkills](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/)

### 7.1 Threat Context

The AI agent skill ecosystem faces severe security threats:
- 36% of ClawHub skills contain prompt injection (Snyk ToxicSkills, Feb 2026)
- 13.4% have critical security issues; 824+ confirmed malicious skills
- Attack techniques: credential theft, data exfiltration, obfuscated code, prompt injection
- Skills run with full agent permissions — no sandbox by default

### 7.2 Skill Risk Assessment Engine

| ID | Description |
|----|-------------|
| FR-S1 | IpMan shall include a built-in risk assessment engine that analyzes skills and IP packages for security risks. The engine shall be inspired by [Skill Vetter](https://clawhub.ai/spclaudehome/skill-vetter) or directly invoke it where applicable. |
| FR-S1.1 | Risk classification: 🟢 LOW (no issues), 🟡 MEDIUM (some concerns), 🔴 HIGH (red flags), ⛔ EXTREME (likely malicious). |
| FR-S1.2 | Red flag detection: curl/wget to unknown URLs, credential harvesting (API keys, tokens, ~/.ssh, ~/.aws), obfuscated code (base64, minified, eval/exec), sudo/root requests, network calls to raw IPs, access to agent memory files. |
| FR-S1.3 | Permission scope analysis: file read/write scope, network call targets, command execution, scope minimality check (Principle of Least Privilege). |
| FR-S1.4 | Source reputation check: author history, download count, repo age/stars, community reviews. |
| FR-S1.5 | Output: structured risk report with risk level, detected flags, permission summary, and verdict (SAFE TO INSTALL / INSTALL WITH CAUTION / DO NOT INSTALL). |

### 7.3 IpHub Report & Flag System

| ID | Description |
|----|-------------|
| FR-S2 | IpHub shall support a community-driven reporting mechanism for flagging suspicious skills/packages. |
| FR-S2.1 | Report submission via `ipman hub report <name> --reason <description>`. |
| FR-S2.2 | Report count tracked as metadata in IpHub registry, visible in `ipman hub info` output with prominent display. |
| FR-S2.3 | Upon receiving a report, the system re-runs risk assessment on the reported item and updates the risk label. |
| FR-S2.4 | High report counts contribute to elevated risk classification as an input signal. |

### 7.4 Publish-Time Risk Assessment

| ID | Description |
|----|-------------|
| FR-S3 | When publishing via `ipman hub publish`, the risk assessment engine is automatically invoked before creating the PR. |
| FR-S3.1 | Risk level is included in the registry file metadata. |
| FR-S3.2 | If risk level is HIGH or EXTREME, the publish is blocked with an explanation. |
| FR-S3.3 | Risk assessment results are included in the PR body for reviewer reference. |

### 7.5 Install-Time Security Enforcement

| ID | Description |
|----|-------------|
| FR-S4 | IpMan shall enforce security policies during installation based on the active security mode. |
| FR-S4.1 | **IpHub source (default trust):** Trust existing risk label from IpHub; skip local assessment unless in STRICT mode or `--vet` flag is specified. |
| FR-S4.2 | **Local file / URL / custom hub source:** Always run local risk assessment before installation unless `--no-vet` flag is specified. |
| FR-S4.3 | Install-time action matrix: |

| Risk Level | PERMISSIVE | DEFAULT | CAUTIOUS | STRICT |
|-----------|------------|---------|----------|--------|
| 🟢 LOW | Install | Install | Install | Install |
| 🟡 MEDIUM | Install | Install | Warn+Install | Warn+Confirm |
| 🔴 HIGH | Install | Warn+Install | Block | Block |
| ⛔ EXTREME | Warn+Install | Block | Block | Block |

| ID | Description |
|----|-------------|
| FR-S4.4 | **Block:** Refuse installation, display risk report, log to security log file. |
| FR-S4.5 | **Warn+Confirm:** Display warning, require explicit user confirmation (bypass with `--yes`). |

### 7.6 Security Mode Levels

| ID | Description |
|----|-------------|
| FR-S5 | IpMan shall support four security mode levels: PERMISSIVE, DEFAULT, CAUTIOUS, STRICT. |
| FR-S5.1 | Security mode priority: CLI flag `--security <mode>` > config file `security.mode` > built-in default (DEFAULT). |
| FR-S5.2 | In STRICT mode, all install sources trigger local risk assessment, regardless of existing IpHub labels. |

### 7.7 Security Logging

| ID | Description |
|----|-------------|
| FR-S6 | When a skill/IP is blocked or warned, a log entry is written to the security log file. |
| FR-S6.1 | Log entry includes: timestamp, skill name, source, risk level, risk details, action taken (blocked/warned/installed). |
| FR-S6.2 | Log path configurable via config file; default: `~/.ipman/security.log`. |
| FR-S6.3 | Logging can be disabled via config: `security.log_enabled: false`. |

### 7.8 Configuration File

| ID | Description |
|----|-------------|
| FR-S7 | IpMan shall support a YAML configuration file at `~/.ipman/config.yaml` for default parameter values. |
| FR-S7.1 | Supported fields: `security.mode`, `security.log_enabled`, `security.log_path`, `hub.url`, `agent.default`. |
| FR-S7.2 | Priority order: CLI flags > environment variables > config file > built-in defaults. |

Example:
```yaml
# ~/.ipman/config.yaml
security:
  mode: default          # permissive | default | cautious | strict
  log_enabled: true
  log_path: ~/.ipman/security.log

hub:
  url: https://raw.githubusercontent.com/twisker/iphub/main

agent:
  default: auto          # auto | claude-code | openclaw
```

### 7.9 IpHub Mirror Support

| ID | Description |
|----|-------------|
| FR-S8 | IpMan shall support alternative IpHub registry URLs for regional access or network restrictions. |
| FR-S8.1 | Mirror URL configurable via: config file `hub.url`, CLI flag `--hub-url <url>`, or environment variable `IPMAN_HUB_URL`. |
| FR-S8.2 | Mirror URLs point to alternative hosting of the same index.yaml and registry file structure. |

### 7.10 CNB (cnb.cool) Mirror

| ID | Description |
|----|-------------|
| FR-S9 | An official IpHub mirror shall be maintained on CNB (cnb.cool) (Yunxiao) as a public repository. |
| FR-S9.1 | A GitHub Actions workflow on the main iphub repo shall auto-sync to CNB on every merge to main. |
| FR-S9.2 | Users in regions with GitHub access limitations can configure `hub.url` to point to the CNB mirror URL. |

---

**Document Version**: 2.0
**Last Updated**: 2026-03-14