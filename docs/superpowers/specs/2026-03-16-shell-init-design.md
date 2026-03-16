# Shell Init Integration — Design Spec

> IpMan - Intelligence Package Manager
> Date: 2026-03-16
> Status: Approved
> Sprint: 7 (Phase 4 — User Experience Improvement)

## 1. Background & Motivation

Currently, `ipman env activate` creates the symlink and prints a shell script, but users must manually `eval "$(ipman env activate myenv)"` to update their prompt. On Windows, `eval` doesn't exist in PowerShell, making the feature effectively broken.

This spec introduces `ipman init`, modeled after `conda init`, which injects a shell function wrapper into the user's shell config file. After running `ipman init` once, `ipman env activate/deactivate` works directly without `eval`.

## 2. `ipman init` Command

```bash
ipman init [SHELL...]           # Inject into specified shell(s)
ipman init                      # Auto-detect current shell
ipman init --reverse [SHELL...] # Remove injection
ipman init --dry-run             # Print what would be injected, don't write
```

### 2.1 Shell Config File Mapping

| Shell | Config File | Detection |
|-------|-----------|-----------|
| bash | `~/.bashrc` | `$SHELL` contains `bash` |
| zsh | `~/.zshrc` | `$SHELL` contains `zsh` |
| fish | `~/.config/fish/config.fish` | `$SHELL` contains `fish` |
| powershell | `$PROFILE` (typically `~/Documents/PowerShell/Microsoft.PowerShell_profile.ps1`) | `$PSModulePath` exists |

### 2.2 Auto-Detection Logic

1. Check `$SHELL` env var (Unix)
2. Check `$PSModulePath` (Windows PowerShell)
3. Fallback: bash

## 3. Injection Content

All injections are wrapped with marker comments for precise `--reverse` removal.

### 3.1 bash/zsh

```bash
# >>> ipman init >>>
# !! Contents within this block are managed by 'ipman init' !!
ipman() {
    if [ "$1" = "env" ] && [ "$2" = "activate" ]; then
        shift 2
        eval "$(command ipman env activate "$@")"
    elif [ "$1" = "env" ] && [ "$2" = "deactivate" ]; then
        shift 2
        eval "$(command ipman env deactivate "$@")"
    else
        command ipman "$@"
    fi
}
# <<< ipman init <<<
```

### 3.2 fish

```fish
# >>> ipman init >>>
# !! Contents within this block are managed by 'ipman init' !!
function ipman
    if test "$argv[1]" = "env"; and test "$argv[2]" = "activate"
        eval (command ipman env activate $argv[3..])
    else if test "$argv[1]" = "env"; and test "$argv[2]" = "deactivate"
        eval (command ipman env deactivate $argv[3..])
    else
        command ipman $argv
    end
end
# <<< ipman init <<<
```

### 3.3 powershell

```powershell
# >>> ipman init >>>
# !! Contents within this block are managed by 'ipman init' !!
function ipman {
    $ipmanExe = (Get-Command ipman -CommandType Application).Source
    if ($args[0] -eq 'env' -and $args[1] -eq 'activate') {
        $remaining = @($args | Select-Object -Skip 2)
        $script = (& $ipmanExe env activate @remaining) -join "`n"
        Invoke-Expression $script
    } elseif ($args[0] -eq 'env' -and $args[1] -eq 'deactivate') {
        $remaining = @($args | Select-Object -Skip 2)
        $script = (& $ipmanExe env deactivate @remaining) -join "`n"
        Invoke-Expression $script
    } else {
        & $ipmanExe @args
    }
}
# <<< ipman init <<<
```

### 3.4 Key Design Decisions

- `command ipman` (bash/zsh/fish) and `Get-Command ipman -CommandType Application` (powershell) call the real binary, avoiding recursive function calls.
- Only `env activate` and `env deactivate` are intercepted; all other subcommands pass through to the binary unchanged.
- The shell function signature matches the real CLI exactly — users don't need to change any commands.

## 4. `--reverse` Logic

1. Read the shell config file
2. Find the block between `# >>> ipman init >>>` and `# <<< ipman init <<<`
3. Remove the entire block (including marker lines)
4. Write back the file
5. If markers not found, print: "ipman init has not been run for {shell}"

Idempotent: running `--reverse` when already removed is a no-op with a message.

## 5. Shell Detection

`ipman init` needs its own shell detection logic, separate from the existing `_detect_shell()` in `cli/env.py` which returns "bash" for both bash and zsh. The new detection must distinguish them because the **config file paths differ** (`~/.bashrc` vs `~/.zshrc`):

```python
def detect_shell() -> str:
    shell_path = os.environ.get("SHELL", "")
    if "zsh" in shell_path:
        return "zsh"
    if "bash" in shell_path:
        return "bash"
    if "fish" in shell_path:
        return "fish"
    if os.environ.get("PSModulePath"):
        return "powershell"
    return "bash"  # fallback
```

## 6. File Handling Safety

### 6.1 Backup before modification

Before writing to any config file, create a backup: `~/.bashrc` → `~/.bashrc.ipman-backup`. If a backup already exists, overwrite it (latest backup only).

### 6.2 Create file if not exists

If the target config file does not exist (common for `~/.zshrc` on fresh installs, PowerShell `$PROFILE`, and `config.fish`), create the file and any necessary parent directories before injecting.

### 6.3 File encoding

All config files read/written as UTF-8.

## 7. Idempotency

Running `ipman init` multiple times does NOT duplicate the injection:
1. Check if markers already exist in the config file
2. If yes, remove old block first, then inject new one (supports upgrades)
3. If no, append the block

## 8. User Experience Flow

### First-time user (no `ipman init`):
```
$ ipman env activate myenv
Activated 'myenv'.
  Prompt tag: [ip:myenv]

Tip: Run 'ipman init' to enable automatic shell integration.
     After that, 'ipman env activate' will update your prompt directly.
```

### After `ipman init`:
```
$ ipman init
Detected shell: bash
Modified: /home/user/.bashrc
Shell integration installed. Restart your shell or run:
  source ~/.bashrc

$ source ~/.bashrc
$ ipman env activate myenv
(prompt changes to: [ip:myenv] $)

$ ipman env deactivate
(prompt restored)
```

### Reverse:
```
$ ipman init --reverse
Detected shell: bash
Removed ipman shell integration from /home/user/.bashrc
Restart your shell or run:
  source ~/.bashrc
```

## 9. Backward Compatibility

- Users who never run `ipman init` continue to see the `eval` hint — no behavior change.
- The `eval "$(ipman env activate ...)"` pattern still works even after `ipman init` (the shell function calls it internally).
- No changes to the activate/deactivate core logic — only the CLI output messaging changes.

## 10. Tip Messaging in activate/deactivate

The existing `cli/env.py` activate command shows an `eval` hint when stdout is a TTY. After this change:

- **If `ipman init` has NOT been run** (detected by checking if markers exist in the shell config): show the new tip: `"Tip: Run 'ipman init' to enable automatic shell integration."`
- **If `ipman init` HAS been run**: show nothing extra — the shell function handles everything.
- The old `eval` hint is removed from the TTY output.

Detection: `shell_init.is_initialized(shell)` checks if the markers exist in the config file.

## 11. Production Code Changes

| File | Action | Description |
|------|--------|-------------|
| `src/ipman/core/shell_init.py` | Create | Shell config injection/removal logic |
| `src/ipman/cli/init.py` | Create | `ipman init` CLI command |
| `src/ipman/cli/main.py` | Modify | Register `init` command |
| `src/ipman/cli/env.py` | Modify | Add "Run ipman init" tip to activate/deactivate output |
| `tests/test_core/test_shell_init.py` | Create | Injection, removal, idempotency, dry-run tests |
| `tests/test_cli/test_init.py` | Create | CLI command tests |

## 12. Test Scenarios

### test_shell_init.py (core logic)

| Test | Description |
|------|-------------|
| `test_generate_bash_injection` | Correct bash function content with markers |
| `test_generate_zsh_injection` | Same structure as bash |
| `test_generate_fish_injection` | Fish function syntax |
| `test_generate_powershell_injection` | PowerShell function syntax |
| `test_inject_into_file` | Appends block to config file |
| `test_inject_idempotent` | Running twice does not duplicate |
| `test_inject_upgrade` | Running with new content replaces old block |
| `test_remove_injection` | `--reverse` removes block cleanly |
| `test_remove_not_present` | `--reverse` when not injected is no-op |
| `test_dry_run` | Returns content without writing file |
| `test_detect_shell` | Auto-detects bash/zsh/fish/powershell |
| `test_detect_shell_zsh_not_bash` | zsh detected as zsh, not bash |
| `test_config_file_path` | Correct path for each shell |
| `test_backup_created` | Config file backup created before modification |
| `test_config_file_created_if_missing` | Config file + parent dirs created if not exist |
| `test_is_initialized` | Detects whether markers are present in config |

### test_init.py (CLI)

| Test | Description |
|------|-------------|
| `test_init_default` | Auto-detect shell and inject |
| `test_init_specific_shell` | `ipman init bash` |
| `test_init_multiple_shells` | `ipman init bash zsh` |
| `test_init_reverse` | `ipman init --reverse` |
| `test_init_dry_run` | `ipman init --dry-run` |
