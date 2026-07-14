# Security Policy

Security is a core StreamPilot feature.

## Reporting a Vulnerability

Please report suspected security issues privately before public disclosure.

Do not open a public GitHub issue for vulnerabilities involving:

- API keys
- OAuth tokens
- Discord webhooks
- OBS passwords
- Credential exposure
- Plugin sandbox bypasses

## Security Principles

- Secure by Default
- Least Privilege
- Local First
- Secrets Never in Logs
- AI Optional
- No Telemetry Without Consent

## Sensitive Data

StreamPilot should never log:

- Passwords
- API keys
- OAuth tokens
- Webhook URLs
- Authentication headers
- Session cookies

## Local Credential Storage

Twitch OAuth tokens use the operating system credential manager by default. Existing
`data/twitch_tokens.json` credentials are migrated only after the OS-backed value is
written and verified. Set `STREAMPILOT_SECRET_STORE=file` only for local development;
the fallback file is written atomically with user-only permissions.
