# Security policy

## Reporting a vulnerability

Do not publish exploit details, credentials, reset links, personal information or production database records in a public issue or pull request.

Use GitHub's **Security → Advisories → Report a vulnerability** for a private report when that option is enabled. If it is unavailable, open a minimal issue asking the repository owner for a private reporting channel, without disclosing the vulnerability. The repository owner is [@gbharath8182](https://github.com/gbharath8182). Do not assume unsolicited direct messages or an address found elsewhere are trusted reporting channels.

Include the affected commit, affected route/component, prerequisites, impact and the smallest non-destructive reproduction using synthetic data. Maintainers will coordinate remediation and disclosure; no response-time or bounty commitment is implied.

## Testing authorization

Public source code is not permission to probe the live deployment, access another account, exfiltrate data, send unsolicited email, exhaust paid AI quotas or disrupt infrastructure. Obtain explicit written authorization defining scope before testing hosted services. Use an isolated local environment and disposable data for normal contribution work. Stop if testing exposes real user data; report privately without retaining unnecessary copies.

## Supported code and deployment boundaries

Security fixes target the maintained application on `main`; historical scripts under `scripts/legacy/` are not supported operational tools. Do not execute them against production. Deploy the latest reviewed release, keep credentials in the hosting environment, and rotate exposed keys rather than merely removing them from a commit.

The app uses authenticated, user-scoped APIs, secure production refresh cookies, bounded inputs and origin/rate-limit controls. These are defense layers, not a security certification. Current limitations include per-process rate limiting, browser-accessible bearer tokens, non-durable background email delivery and no rotating refresh-token replay store. Use a trusted remote sandbox for code execution; never execute candidate code in the web-service process.

## Camera, audio and interview data

The spoken practice mode displays camera video locally and does not upload or save video. Audio is recorded only after the user starts recording, limited to three minutes/8 MB per answer, sent to Groq for transcription, and not persisted by this application. Provider processing and retention are subject to Groq's policy. Confirmed transcripts and generated feedback are stored in user-scoped MongoDB sessions and can be deleted through the session controls. A 24-hour answer window is not automatic data deletion. Operator backups have their own retention policy.

Treat transcripts as personal data: do not log request bodies, include them in fixtures, or expose them through public analytics. Practice feedback must not claim to infer emotion, personality, accent quality, truthfulness or eye contact from video or transcripts.

## Repository access is separate from licensing

Public visibility does not grant write/admin access or permission to delete this repository. Repository deletion requires owner/admin authority. `LICENSE.md`, contributor policies and `CODEOWNERS` do not technically prevent pushes, force-pushes or deletion. Enforce access and branch protection in GitHub settings; see [repository protection](docs/repository-protection.md). Protect the owner's GitHub account with two-factor authentication and review collaborators, deploy keys and installed apps regularly.
