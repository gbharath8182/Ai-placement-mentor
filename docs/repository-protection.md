# Repository protection

## What public visibility permits

A public repository can be viewed and forked. It does not give visitors permission to push to `main`, merge pull requests, change access or delete the original repository. Repository deletion is an owner/admin operation. Keep administrator access limited to trusted maintainers; normal contributors should use forks and pull requests.

Usage rights are a separate matter: this project's [source-available notice](../LICENSE.md) requires prior permission for uses beyond applicable law, existing grants and GitHub's platform rights. It is not an open-source license. Neither that notice nor a security policy can prevent someone from copying files technically. Consult qualified counsel if enforceability or commercial licensing is material.

## Maintainer setup in GitHub

The authenticated Git identity available during the 28 October 2026 update had push access but **no admin or maintain permission**. No branch-protection or security-setting changes were attempted with that identity. The repository owner or another administrator must perform the setup below.

### Commands for an administrator

If GitHub CLI is already installed and signed into an account with administration access, run these from the repository root. Do not paste tokens into chat or commit credentials.

```powershell
gh api repos/gbharath8182/Ai-placement-mentor --jq '.permissions'
gh api repos/gbharath8182/Ai-placement-mentor/branches/main/protection
```

Confirm `admin` is true. A 404 on the second command, **after confirming repository admin access**, normally means classic branch protection is not configured; also check for existing rulesets in Settings. A 403 or inaccessible repository is not evidence of missing protection. Do not overwrite an existing policy blindly.

For an unprotected branch with no conflicting ruleset, review `.github/main-protection.example.json`, confirm the actual CI check is named `test`, then apply the example:

```powershell
gh api --method PUT repos/gbharath8182/Ai-placement-mentor/branches/main/protection --input .github/main-protection.example.json
gh api --method PUT repos/gbharath8182/Ai-placement-mentor/private-vulnerability-reporting
gh api repos/gbharath8182/Ai-placement-mentor/branches/main/protection
```

The example requires reviewed PRs and passing tests for non-admin contributors, blocks branch deletion/force-pushes, and deliberately leaves admin enforcement off so the owner can maintain the project without self-approval deadlocks. An admin bypass can also bypass protections: it is not protection against a compromised owner account. If you require protection even from admins, review that trade-off and set `enforce_admins` to true with a second trusted reviewer available. Do not run the PUT against an existing protection configuration without merging and reviewing its settings first. Existing rulesets may impose additional requirements.

### Step-by-step without GitHub CLI

These settings require authenticated repository-administration access. Documentation and committed files do not activate them.

1. Sign in as the owner or an administrator and open the repository. Click **Settings**. If Settings or the controls below are missing, ask the owner for assistance; push access alone is insufficient.
2. In **Settings → Collaborators / Manage access**, remove unnecessary write/admin grants. Do not add public contributors as administrators. Review deploy keys, GitHub Apps and token permissions. Enable two-factor authentication on the owner's account.
3. In **Settings → Rules → Rulesets**, select **New ruleset → New branch ruleset**. Name it `Protect main`, set enforcement to **Active**, and target `main` under target branches. Enable **Restrict deletions** and **Block force pushes**. Require a pull request, conversation resolution and the `test` status check from the Tests workflow. Review the actual displayed check name before selecting it.
4. Enable one required approval and code-owner review for outside contributions; `.github/CODEOWNERS` names the current repository owner. Where there is only one maintainer, mandatory independent approval can block that maintainer's own pull requests. Choose a narrowly scoped owner/admin bypass deliberately if the owner must continue direct maintenance pushes; do not grant broad bypass access to collaborators. Click **Create** or **Save changes**.
5. In **Settings → Code security / Advanced Security**, enable private vulnerability reporting, secret scanning and push protection where available for this repository and plan. Never assume these are active just because `SECURITY.md` exists.
6. In **Settings → Actions → General**, use read-only default workflow-token permissions and require approval for workflows from outside contributors. Never expose deployment secrets to untrusted pull requests or execute their code in a privileged `pull_request_target` workflow.
7. Confirm the ruleset is **Active**, target is `main`, status checks resolve correctly, and a non-bypass contributor cannot force-push or delete that branch. GitHub's protections for repository deletion are distinct from branch-deletion rules.

The current workflow requests `contents: read`; source-level checks scan tracked files for secret patterns. Those checks supplement, but do not replace, host-level access controls. No claim is made here that the above GitHub settings have been applied.

References: [GitHub repository licensing](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository), [protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets).
