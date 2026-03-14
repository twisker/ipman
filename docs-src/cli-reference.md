# CLI Reference

## Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--help` | Show help and exit |

## Environment Commands (`ipman env`)

| Command | Description |
|---------|-------------|
| `ipman env create <name>` | Create a new skill environment |
| `ipman env activate <name>` | Activate an environment |
| `ipman env deactivate` | Deactivate current environment |
| `ipman env delete <name>` | Delete an environment |
| `ipman env list` | List all environments |
| `ipman env status` | Show active environment details |

### Options for `env create`

| Option | Description |
|--------|-------------|
| `--project` | Project scope (default) |
| `--user` | User scope |
| `--machine` | Machine scope |
| `--agent <name>` | Specify agent tool |

## Install / Uninstall

| Command | Description |
|---------|-------------|
| `ipman install <source>` | Install skill or IP package |
| `ipman uninstall <name>` | Uninstall a skill |

### Options for `install`

| Option | Description |
|--------|-------------|
| `--agent <name>` | Specify agent tool |
| `--dry-run` | Preview without installing |
| `--security <mode>` | Security mode override |
| `--vet` | Force local risk assessment |
| `--no-vet` | Skip local risk assessment |
| `--yes` | Auto-confirm warnings |
| `--hub-url <url>` | Override IpHub URL |

## Skill Commands (`ipman skill`)

| Command | Description |
|---------|-------------|
| `ipman skill list` | List installed skills |

## Pack

| Command | Description |
|---------|-------------|
| `ipman pack` | Pack environment into .ip.yaml |

### Options for `pack`

| Option | Description |
|--------|-------------|
| `--name <name>` | Package name (required) |
| `--version <ver>` | Package version (default: 1.0.0) |
| `--description <desc>` | Package description |
| `--output <path>` | Output file path |
| `--agent <name>` | Specify agent tool |
| `--force` | Overwrite existing file |

## Hub Commands (`ipman hub`)

| Command | Description |
|---------|-------------|
| `ipman hub search <query>` | Search IpHub |
| `ipman hub info <name>` | Show skill/package details |
| `ipman hub top` | Show most installed items |
| `ipman hub publish <source>` | Publish to IpHub |
| `ipman hub report <name>` | Report suspicious skill |

### Options for `hub search`

| Option | Description |
|--------|-------------|
| `--agent <name>` | Filter by agent |

### Options for `hub publish`

| Option | Description |
|--------|-------------|
| `--description <desc>` | Skill description (required for skills) |
| `--license <license>` | License (e.g. MIT) |
| `--homepage <url>` | Project homepage |

### Options for `hub report`

| Option | Description |
|--------|-------------|
| `--reason <text>` | Reason for reporting (required) |

## Info

| Command | Description |
|---------|-------------|
| `ipman info` | Show IpMan installation info |
