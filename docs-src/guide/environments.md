# Virtual Environments

IpMan isolates skills into virtual environments, similar to Python's virtualenv/conda.

## Scopes

| Scope | Flag | Location | Use case |
|-------|------|----------|----------|
| Project | `--project` (default) | `.ipman/envs/` in project dir | Per-project isolation |
| User | `--user` | `~/.ipman/envs/` | Shared across user projects |
| Machine | `--machine` | System-wide | Global tools |

## Commands

```bash
# Create
ipman env create myenv
ipman env create shared-env --user
ipman env create global-tools --machine

# Activate / Deactivate
ipman env activate myenv
ipman env deactivate

# List and inspect
ipman env list
ipman env status

# Delete
ipman env delete myenv
```

## Prompt Tag

When an environment is active, your shell prompt shows:

```
[ip:myenv] $
```

See the [tech spec](https://github.com/twisker/ipman) for the full prompt tag format across scope layers.
