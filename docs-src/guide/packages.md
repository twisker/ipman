# IP Packages

Intelligence Packages (`.ip.yaml`) bundle skills into distributable collections.

## Pack

```bash
ipman pack --name my-kit --version 1.0.0
ipman pack --name my-kit --version 1.0.0 --description "My toolkit" --output my-kit.ip.yaml
ipman pack --name my-kit --version 2.0.0 --force  # overwrite existing
```

## Install from IP File

```bash
ipman install my-kit.ip.yaml
ipman install my-kit.ip.yaml --dry-run
```

## File Format

See the [IP Package Spec](../ip-package-spec.md) for the full YAML schema.

```yaml
# IpMan Intelligence Package
name: my-kit
version: "1.0.0"
description: "My skill collection"
skills:
  - name: web-scraper
    version: "d5c15b861cd2"
  - name: css-helper
    version: "1.0.0"
dependencies:
  - name: base-utils
    version: ">=1.0.0"
```

The `version` field on skills is optional — it records the installed version at pack time for reproducibility. `ipman pack` captures it automatically from the agent CLI.
