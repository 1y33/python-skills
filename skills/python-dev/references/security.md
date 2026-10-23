# Trust boundaries

Read when changing untrusted input, authorization, secrets, or network exposure. Identify attacker-controlled values, protected resources, and privilege boundaries before choosing validation. Fail closed when required protection is absent.

## Identity and secrets

Load credentials through explicit configuration or a secret manager. Redacting types reduce accidental display but do not prevent deliberate serialization or traceback leakage. Exclude secrets and sensitive payloads from logs, errors, snapshots, and metric labels. Retain TLS verification.

Generate security tokens with secrets; compare authentication secrets/signatures with hmac.compare_digest. Use established password hashing and token-verification libraries; verify algorithm, issuer, audience, expiry, and key policy rather than merely decoding claims. Support rotation and least-privilege credentials.

List who can reach each listener: local users, browser pages, the network. Localhost is not a browser trust boundary because DNS rebinding bypasses CORS: validate the Host header against an allowlist. Cache keys for per-user data include user, tenant, and permissions. Centralize authentication policy, list public exceptions explicitly, and authorize the actual resource, operation, and tenant. Check authorization within the mutation boundary when races could invalidate it. Browser cookie authentication needs CSRF protection; CORS is not authentication. Rate-limit inbound expensive and authentication operations.

## Files and archives

Resolve user-controlled paths and verify containment against a trusted root. Define symlink policy; resolve-and-check is insufficient if an attacker can mutate the tree before open. Use descriptor-relative/no-follow operations or isolation when race resistance is required and supported.

Check every archive member and link target, cap entry count and expanded bytes, and prevent traversal and decompression bombs. Uploaded filenames are metadata, not trusted storage paths. Verify allowed content and size; generated names do not replace authorization. Protect temporary files and permissions.

## Network and serialization

Prevent SSRF through scheme/host/port policy and restrictions on private, loopback, and link-local destinations. Account for DNS rebinding, redirects, and the actual connected address; use egress controls where application checks cannot enforce the boundary.

Never execute or deserialize untrusted code with eval, exec, pickle, marshal, or unsafe loaders. Restricted model-loading modes reduce risk but are not a hostile-code sandbox. Use safe format parsers with nesting, size, and resource limits. Parameterize SQL; never concatenate untrusted shell commands. Escape output for its destination context.

Dynamic imports, plugins, annotation evaluation, and dependency installation execute code. Treat extensions as trusted or isolate them with real process/OS controls; an ABC or Python subinterpreter is not a security boundary.

## Checklist

- [ ] Who can reach each listener is stated; Host allowlist and admin-route auth match that answer.
- [ ] Identity, resource authorization, secret redaction, and unsafe-startup refusal are tested.
- [ ] Paths, archives, uploads, URLs, and parsers resist relevant traversal, races, and exhaustion.
- [ ] Injection and code-execution boundaries are explicit; dependencies are audited.
- [ ] Failure tests include denied access and cross-tenant attempts, not only valid input.
