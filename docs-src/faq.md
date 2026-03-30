# FAQ

## Installation

### Q: `pip install ipman-cli` fails with "no matching distribution found"

Two common causes:

**Cause 1 (most common): Python version below 3.10**

IpMan requires Python >= 3.10. When your Python version doesn't meet the requirement, PyPI finds no compatible distribution.

**Cause 2: VPN / proxy causing SSL connection failure**

Under VPN or corporate networks, pip may fail to connect to PyPI due to SSL certificate verification failure. The error can sometimes appear as "no matching distribution" (accompanied by SSL warnings). See [SSL errors](#q-pip-install-fails-with-ssl-certificate_verify_failed) below.

**Troubleshooting steps**:

```bash
# 1. Check Python version (must be >= 3.10)
python3 --version

# 2. If version is sufficient, test PyPI connectivity
pip index versions ipman-cli
```

**Solutions**:
- Version issue: upgrade Python to 3.10+
- Network issue: see [SSL errors](#q-pip-install-fails-with-ssl-certificate_verify_failed) below

macOS users can install via Homebrew:

```bash
brew install python@3.12
```

Then set it as default — see [Installation Guide](getting-started/installation.md#2-set-python-312-as-default).

---

### Q: How to set Homebrew Python 3.12 as default on macOS?

Add PATH configuration to `~/.zshrc`:

```bash
echo 'export PATH="$(brew --prefix python@3.12)/libexec/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Verify:

```bash
python3 --version   # Should show 3.12.x
which python3       # Should point to Homebrew path
```

> **Note**: Do not delete or overwrite `/usr/bin/python3` — macOS system tools depend on it. This method safely shadows the system version via PATH priority.

---

### Q: `pip install` fails with "externally-managed-environment" on Python 3.12

**Cause**: Python 3.12 enforces [PEP 668](https://peps.python.org/pep-0668/), preventing pip from installing packages into Homebrew-managed Python environments.

**Recommended**: Use pipx for CLI tools:

```bash
brew install pipx
pipx ensurepath
pipx install ipman-cli
```

pipx automatically creates an isolated virtual environment for ipman-cli.

> **VPN users**: If pipx also fails with SSL errors, add trusted hosts:
> ```bash
> pipx install ipman-cli --pip-args="--trusted-host pypi.org --trusted-host files.pythonhosted.org"
> ```
> See [SSL errors](#q-pip-install-fails-with-ssl-certificate_verify_failed) below.

**Alternative**: Create a virtual environment manually:

```bash
python3 -m venv ~/.ipman-venv
source ~/.ipman-venv/bin/activate
pip install ipman-cli
```

> **Not recommended**: `pip install --break-system-packages ipman-cli` bypasses the restriction but may corrupt Homebrew's Python packages.

---

### Q: `pip install` fails with "SSL: CERTIFICATE_VERIFY_FAILED"

**Typical error**:

```
WARNING: Retrying ... after connection broken by 'SSLError(SSLCertVerificationError(1,
'[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate'))'
```

**Cause**: Usually VPN, corporate proxy, or missing CA root certificates preventing pip from verifying PyPI's SSL certificate.

**Solution 1: VPN / corporate proxy (most common)**

Temporarily skip SSL verification:

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ipman-cli
```

For pipx users:

```bash
pipx install ipman-cli --pip-args="--trusted-host pypi.org --trusted-host files.pythonhosted.org"
```

> **Tip**: To make this permanent, add to `~/.pip/pip.conf`:
> ```ini
> [global]
> trusted-host =
>     pypi.org
>     files.pythonhosted.org
> ```

**Solution 2: Missing CA certificates on macOS**

```bash
brew install ca-certificates
```

**Solution 3: Add corporate root certificate to trust chain**

If your company network uses an SSL MITM proxy, import the corporate root certificate:

```bash
# Get the root certificate from your IT department, then:
# macOS: double-click the .crt file to import into Keychain, set to "Always Trust"
# Or: specify via environment variable
export SSL_CERT_FILE=/path/to/company-root-ca.crt
```

---

### Q: Which Python versions are supported?

IpMan requires **Python >= 3.10**. Python 3.12 or later is recommended.

Python 3.9 and below are not supported because the project uses 3.10+ language features (e.g. `match/case` pattern matching, `X | Y` type union syntax).

---

### Q: Which operating systems are supported?

IpMan supports **Linux**, **macOS**, and **Windows**.

---

## Usage

### Q: Which AI agent tools does IpMan support?

Currently supported:

- **Claude Code**
- **OpenClaw**

IpMan does not modify agent internals — it interacts through standard CLI commands.

### Q: How to check the installed version?

```bash
ipman --version
```
