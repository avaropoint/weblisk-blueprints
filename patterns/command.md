<!-- blueprint
type: pattern
name: command
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent, patterns/logging, patterns/secrets]
platform: any
tier: free
-->

# Command Pattern

Secure execution of commands and scripts on local or remote systems.
Defines the sandboxed execution model, permission controls, output
capture, timeout enforcement, and audit trail for agents that need to
invoke system commands, CLI tools, or scripts as part of their
processing.

## Overview

Some agents need to execute system commands — running CLI tools,
invoking scripts, calling external binaries, or executing shell
commands on remote systems. This pattern defines a standard, secure
interface for command execution that provides:

- Sandboxed execution with explicit permission grants
- Output capture (stdout, stderr, exit code)
- Timeout enforcement with kill semantics
- Environment variable injection (including secrets)
- Audit trail for every command executed
- Remote execution over SSH with credential management

Agents extend this pattern when they need to invoke external commands.
The framework provides the execution runtime; the agent declares what
commands it's allowed to run.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [error, code, category, retryable]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: FieldType
          fields_used: [string, int, boolean, timestamp]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, type, capabilities]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/logging
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: LogEntry
          fields_used: [log_type, level, component, details]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/secrets
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: SecretRef
          fields_used: [key, env_var]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Allowlist-only** — Agents can only execute commands they've
   declared in their blueprint. Arbitrary command execution is
   forbidden.
2. **Sandboxed** — Commands run in a restricted environment with
   controlled working directory, environment variables, and resource
   limits.
3. **Audited** — Every command execution is logged with the full
   command, arguments, exit code, duration, and truncated output.
4. **Timeout-enforced** — Every command has a maximum execution time.
   The framework kills commands that exceed their timeout.
5. **No shell injection** — Commands are executed as argument arrays,
   never as shell-interpreted strings.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: command-execution
      description: Sandboxed execution of declared commands with output capture
      parameters:
        - name: key
          type: string
          required: true
          description: Command key from agent declaration
        - name: args
          type: "[]string"
          required: true
          description: Argument values validated against allowed pattern
        - name: timeout
          type: int
          required: false
          description: Override timeout (cannot exceed max_timeout)
      inherits: Argument validation, sandbox setup, timeout enforcement, audit logging
      overridable: true
      override_constraints: Must preserve allowlist-only enforcement and shell injection prevention

    - name: remote-execution
      description: Command execution on remote systems via SSH
      parameters:
        - name: target
          type: string
          required: true
          description: Named remote host from configuration
        - name: key
          type: string
          required: true
          description: Command key from declaration
      inherits: SSH connection, argument validation, output capture
      overridable: true
      override_constraints: Must use SSH key authentication only, password auth forbidden

  types:
    - name: CommandDeclaration
      description: Allowed command definition with binary, args pattern, and timeout
      inherited_by: Types section
    - name: CommandResult
      description: Execution result with exit code, output, duration, and timeout status
      inherited_by: Types section

  endpoints:
    - path: cmd.execute(key, args, options)
      description: Execute a declared command in sandbox
      inherited_by: Command Execution API section
```

---

## Command Declaration

Agents declare their allowed commands in the blueprint:

```markdown
## Configuration

### Commands
| Command Key | Binary | Allowed Args | Max Timeout | Description |
|------------|--------|-------------|-------------|-------------|
| lighthouse | lighthouse | [--output=json, --chrome-flags=*] | 120s | Run Lighthouse audit |
| curl_check | curl | [-s, -o, /dev/null, -w, *, --max-time, *] | 30s | HTTP health check |
| git_pull | git | [pull, --ff-only] | 60s | Pull latest code |
```

### Declaration Fields

| Field | Required | Description |
|-------|----------|-------------|
| Command Key | yes | Unique identifier for this command within the agent |
| Binary | yes | Executable name or absolute path |
| Allowed Args | yes | Argument patterns. `*` = any value for that position. Fixed strings must match exactly. |
| Max Timeout | yes | Maximum execution time before kill |
| Description | yes | Purpose of this command |

---

## Command Execution API

Agents execute commands through the framework's command client:

```
cmd.execute(key, args, options) → CommandResult
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| key | string | yes | Command key from declaration |
| args | string[] | yes | Argument values (validated against allowed pattern) |
| options.timeout | int | no | Override timeout (cannot exceed max_timeout) |
| options.cwd | string | no | Working directory (must be within allowed paths) |
| options.env | object | no | Additional environment variables |
| options.stdin | string | no | Data to send to stdin |
| options.capture_output | bool | no | Whether to capture stdout/stderr (default: true) |

### CommandResult

```json
{
  "command_key": "lighthouse",
  "binary": "lighthouse",
  "args": ["https://example.com", "--output=json"],
  "exit_code": 0,
  "stdout": "{ ... lighthouse report ... }",
  "stderr": "",
  "duration_ms": 45000,
  "timed_out": false,
  "started_at": "2026-04-25T10:30:00Z",
  "completed_at": "2026-04-25T10:30:45Z"
}
```

---

## Argument Validation

Before executing any command, the framework validates arguments
against the declared allowed pattern:

### Validation Rules

```
1. Count args matches allowed pattern length (unless pattern uses
   variadic *)
2. For each arg position:
   a. If pattern = fixed string → arg MUST match exactly
   b. If pattern = * → any value accepted
   c. If pattern = prefix* → arg MUST start with prefix
3. No argument may contain shell metacharacters: ; | & $ ` \ ( ) { }
   unless explicitly allowed
4. No argument may be an absolute path outside allowed directories
```

### Shell Injection Prevention

Commands are NEVER executed through a shell interpreter. The binary
is invoked directly with the argument array:

```
# CORRECT: Direct execution (no shell interpretation)
exec("lighthouse", ["https://example.com", "--output=json"])

# FORBIDDEN: Shell execution (vulnerable to injection)
exec("sh", ["-c", "lighthouse https://example.com --output=json"])
```

If an agent needs shell features (pipes, redirects), it MUST use
separate commands and connect them programmatically.

---

## Execution Sandbox

### Environment

Commands run in a controlled environment:

```yaml
sandbox:
  working_directory: /tmp/weblisk-cmd/{agent_name}/{execution_id}
  allowed_paths:
    - /tmp/weblisk-cmd/
    - {workspace_root}
  env_inherit: false            # Do NOT inherit host environment
  env_base:                     # Minimal base environment
    PATH: /usr/local/bin:/usr/bin:/bin
    HOME: /tmp/weblisk-cmd/{agent_name}
    LANG: en_US.UTF-8
  env_secrets: true             # Inject declared secrets as env vars
```

### Resource Limits

| Resource | Default Limit | Configurable |
|----------|--------------|-------------|
| CPU time | 120 seconds | Per-command max_timeout |
| Memory | 512 MB | `WL_CMD_MAX_MEMORY` |
| Disk write | 100 MB | `WL_CMD_MAX_DISK` |
| Open files | 256 | `WL_CMD_MAX_FILES` |
| Child processes | 10 | `WL_CMD_MAX_PROCS` |

### Timeout Enforcement

```
1. Start command with configured timeout
2. If command completes before timeout → return result
3. If timeout reached:
   a. Send SIGTERM to process
   b. Wait 5 seconds for graceful exit
   c. If still running: send SIGKILL
   d. Return result with timed_out: true
   e. Log: command.timeout with {key, timeout, duration_ms}
```

---

## Remote Execution

Agents MAY execute commands on remote systems via SSH:

### Remote Command Declaration

```markdown
### Commands
| Command Key | Binary | Target | Auth | Max Timeout | Description |
|------------|--------|--------|------|-------------|-------------|
| remote_deploy | deploy.sh | remote | ssh_key | 300s | Deploy to production |
```

### Remote Execution Flow

```
1. Resolve target host from configuration
2. Load SSH credentials from secrets store (patterns/secrets)
3. Establish SSH connection with timeout (10s default)
4. Execute command on remote host with argument validation
5. Capture stdout, stderr, exit code
6. Close connection
7. Return CommandResult with remote: true
```

### Remote Configuration

```yaml
remote:
  hosts:
    production:
      host: prod.example.com
      port: 22
      user: deploy
      secret_key: SSH_DEPLOY_KEY    # References patterns/secrets
    staging:
      host: staging.example.com
      port: 22
      user: deploy
      secret_key: SSH_STAGING_KEY
  connection_timeout: 10            # seconds
  keepalive_interval: 30            # seconds
```

### Remote Security Rules

| Rule | Enforcement |
|------|------------|
| Only declared remote hosts are accessible | Framework rejects unknown hosts |
| SSH key authentication only | Password auth is forbidden |
| Commands are validated before transmission | Same arg validation as local |
| Remote output is size-limited | Max 1 MB stdout, 256 KB stderr |
| Remote commands use the same timeout enforcement | SIGTERM → SIGKILL over SSH |

---

## Output Handling

### Capture

By default, stdout and stderr are captured:

| Stream | Max Size | On Overflow |
|--------|---------|-------------|
| stdout | 1 MB | Truncated, `stdout_truncated: true` |
| stderr | 256 KB | Truncated, `stderr_truncated: true` |

### Streaming

For long-running commands, output can be streamed line-by-line:

```
cmd.execute(key, args, {
  on_stdout: (line) => { /* process line */ },
  on_stderr: (line) => { /* process line */ }
})
```

Streaming and capture are mutually exclusive. Streaming does not
store the full output in the result.

### Sensitive Output

Commands that produce sensitive output (e.g., credential generation)
MUST be marked:

```markdown
| Command Key | ... | Sensitive Output |
|------------|-----|-----------------|
| gen_key | ... | yes |
```

Sensitive output is NOT logged in the audit trail. Only exit code
and duration are recorded.

---

## Audit Trail

Every command execution is logged:

```json
{
  "log_type": "command.executed",
  "level": "info",
  "component": "perf-auditor",
  "details": {
    "command_key": "lighthouse",
    "binary": "lighthouse",
    "args": ["https://example.com", "--output=json"],
    "exit_code": 0,
    "duration_ms": 45000,
    "timed_out": false,
    "remote": false,
    "stdout_size_bytes": 15234,
    "stderr_size_bytes": 0,
    "sensitive": false
  }
}
```

| Event | Log Type | Level |
|-------|----------|-------|
| Command started | `command.started` | info |
| Command completed | `command.executed` | info |
| Command failed | `command.failed` | error |
| Command timed out | `command.timeout` | warn |
| Argument validation failed | `command.rejected` | warn |
| Remote connection failed | `command.remote_error` | error |

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WL_CMD_ENABLED` | `true` | Enable/disable command execution globally |
| `WL_CMD_SANDBOX` | `true` | Enable sandbox restrictions |
| `WL_CMD_MAX_MEMORY` | `512` | Max memory per command (MB) |
| `WL_CMD_MAX_DISK` | `100` | Max disk write per command (MB) |
| `WL_CMD_MAX_FILES` | `256` | Max open files per command |
| `WL_CMD_MAX_PROCS` | `10` | Max child processes per command |
| `WL_CMD_WORK_DIR` | `/tmp/weblisk-cmd` | Base working directory |

### Disabling Command Execution

Setting `WL_CMD_ENABLED=false` disables all command execution. Agents
that extend this pattern will receive `COMMAND_DISABLED` errors for
all `cmd.execute()` calls. This is useful for environments where
external command execution is not permitted (e.g., Cloudflare Workers).

---

## Types

### CommandDeclaration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| key | string | yes | Unique command identifier within agent |
| binary | string | yes | Executable name or path |
| allowed_args | string[] | yes | Argument patterns |
| max_timeout | int | yes | Maximum seconds |
| description | string | yes | Purpose |
| sensitive_output | bool | no | Whether output contains secrets |
| remote | bool | no | Whether command executes remotely |

### CommandResult

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| command_key | string | yes | Command identifier |
| binary | string | yes | Executed binary |
| args | string[] | yes | Actual arguments |
| exit_code | int | yes | Process exit code |
| stdout | string | no | Captured stdout (absent if streaming or sensitive) |
| stderr | string | no | Captured stderr |
| duration_ms | int | yes | Execution duration |
| timed_out | bool | yes | Whether command was killed by timeout |
| started_at | string | yes | ISO 8601 start timestamp |
| completed_at | string | yes | ISO 8601 completion timestamp |
| remote | bool | yes | Whether executed remotely |
| stdout_truncated | bool | no | Whether stdout was truncated |
| stderr_truncated | bool | no | Whether stderr was truncated |

---

## Implementation Notes

- On platforms that don't support process execution (Cloudflare
  Workers, browser environments), this pattern is unavailable.
  Agents SHOULD check `WL_CMD_ENABLED` at startup and disable
  command-dependent features gracefully.
- Working directories are created per-execution and cleaned up after
  the command completes. Persistent working directories require
  explicit configuration.
- On Linux, the sandbox MAY use `unshare` or container namespaces
  for stronger isolation. On macOS, sandbox profiles can restrict
  file access. The baseline sandbox (PATH restriction, working
  directory isolation) works on all UNIX platforms.
- Windows support: argument validation and output capture work
  identically. Process killing uses `taskkill`. Resource limits
  use Job Objects.
- For long-running commands (builds, deployments), consider setting
  generous timeouts and using streaming output to provide progress
  feedback.
- Remote execution over SSH requires the `ssh` binary on the host
  system. The framework does not embed an SSH client library.

## Verification Checklist

- [ ] Only declared commands can be executed
- [ ] Undeclared command keys are rejected
- [ ] Argument validation enforces allowed patterns
- [ ] Shell metacharacters in arguments are rejected
- [ ] Commands are executed directly, never through shell interpreter
- [ ] Working directory is isolated per-execution
- [ ] Environment variables are controlled (no host inheritance)
- [ ] Secrets are injected as environment variables when configured
- [ ] Timeout is enforced with SIGTERM → SIGKILL escalation
- [ ] stdout and stderr are captured with size limits
- [ ] Truncation is indicated in the result
- [ ] Sensitive output is not logged
- [ ] Every execution is audit-logged
- [ ] Resource limits (memory, disk, processes) are enforced
- [ ] Remote execution validates host against declared hosts
- [ ] Remote execution uses SSH key authentication only
- [ ] WL_CMD_ENABLED=false disables all command execution
- [ ] Failed argument validation is logged as command.rejected
