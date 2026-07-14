# SPS-004 — Security

**Status:** Approved  
**Version:** 1.0

## Objectives

- Protect creator credentials.
- Minimize impact of compromised components.
- Make secure behavior default.
- Support local-first operation.

## Credential Management

Credentials must use centralized secret management.

Preferred storage:

- macOS Keychain
- Windows Credential Manager
- Linux Secret Service

## Logging

Never log passwords, API keys, OAuth tokens, webhook URLs, cookies, auth headers, or secrets.

## AI Providers

AI is optional. Only required information should be transmitted.

## Guiding Principle

Security should quietly protect creators without making StreamPilot difficult to use.
