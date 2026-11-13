# Signing Useful Armory releases

Horizon's registry accepts a minisign (Ed25519) signature next to each release file. The registry
pins the project's public key, so **every future release must be signed with the same key**. The
owner makes and keeps the key. An agent must never generate, hold or commit the secret key.

## One-time setup (owner, on Windows)

1. Install minisign:
   ```powershell
   winget install --id jedisct1.minisign -e
   ```
   You can also use `scoop install minisign` or `choco install minisign`.
2. Make the key pair from the repository root:
   ```powershell
   minisign -G
   ```
   It asks for a password. The **public key** goes to `minisign.pub` in the current folder; commit
   that file. The **secret key** goes to `%USERPROFILE%\.minisign\minisign.key`. Never commit it,
   and back it up somewhere safe together with the password. If you lose it, you can't publish
   updates under the same key.
3. Make sure `.gitignore` contains `*.key` and `minisign.key`.

## Every release

```powershell
python tools/package.py
minisign -Sm dist/useful_armory-0.1.7.hmod
minisign -Sm dist/useful_armory_native-0.1.7.hnmod
```

Each command writes `<file>.minisig` next to the file. Check them before uploading:

```powershell
minisign -Vm dist/useful_armory-0.1.7.hmod -p minisign.pub
minisign -Vm dist/useful_armory_native-0.1.7.hnmod -p minisign.pub
cargo horizon-mod check dist/useful_armory-0.1.7.hmod --key <public key> --signature dist/useful_armory-0.1.7.hmod.minisig
```

`<public key>` is the second line of `minisign.pub` (it starts with `RW`).

## Publishing

1. Create a GitHub release, tagged `v0.1.7`. It must not be a draft or pre-release. Attach the
   `.hmod`, the `.hnmod` and both `.minisig` files. The release notes become the changelog.
2. First listing only: submit the repository at https://playhorizon.dev/mods/submit with the public
   key. This opens a pull request in `horizon-rust/horizon-mods` for a reviewer.
3. Later releases are picked up and checked automatically. A published file never changes. To fix
   one, publish a new version.
