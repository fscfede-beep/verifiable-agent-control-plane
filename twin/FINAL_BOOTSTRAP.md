# Final A/B bootstrap

Use the same repository and branch for both environments.

## Environment A

```powershell
.\twin\prepare-environment.ps1 -Role primary -EnvironmentId A
```

## Environment B

```powershell
.\twin\prepare-environment.ps1 -Role twin -EnvironmentId B
```

The script:
1. Clones or fast-resets the repository to `main`.
2. Sets `TWIN_ENV_ROLE` and `TWIN_ENV_ID` only for the current process.
3. Installs the package.
4. Runs the complete test suite.
5. Runs Twin Doctor.
6. Saves the JSON attestation locally.

It does not copy credentials, cookies, browser profiles, OAuth tokens, or sessions.

After both environments are ready, compare their attestations with the repository's
A/B gate. Browser evidence can be collected independently using the isolated A/B
browser harness and read-only probe.
