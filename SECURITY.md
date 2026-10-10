# Security and privacy

## Protect local settings

`settings.json` may contain private page URLs or request headers and is excluded by `.gitignore`. Do not upload it. Keep access codes, cookies, passwords, and API keys off GitHub, issue reports, screenshots, and commit messages.

If a credential is exposed, revoke or rotate it with the service that issued it. Deleting a file in a later commit does not remove the secret from Git history.

## Respect access rules

Monitor only pages you own or are authorized to access. This program makes ordinary HTTP requests; it does not bypass logins, challenges, rate limits, or access controls. Respect the website's terms and choose an appropriate polling interval.

## Report a security concern

Do not post credentials or private page content in a public issue. Contact the repository owner privately if you believe you found a vulnerability. This project does not currently promise a response time or private advisory process.