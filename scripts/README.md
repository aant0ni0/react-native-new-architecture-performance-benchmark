# Replication Utilities

Run these tools from the repository root.

## Configure React Native architecture

```powershell
python .\scripts\configure_rn_architecture.py legacy
python .\scripts\configure_rn_architecture.py new
python .\scripts\configure_rn_architecture.py check
```

The script updates both `newArchEnabled` and `IS_LEGACY` and refuses to report success if they are inconsistent.

## Capture environment

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\capture_environment.ps1 -OutputPath environment_snapshot.txt
```

Without a connected Android device, the script still records the host/toolchain and clearly skips device-specific ADB properties.

## Hash release APKs

The RN Legacy and New Architecture variants use the same Gradle output filename. If both variants must be retained and hashed together, copy each built APK to a labeled directory before cleaning/building the next variant, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\hash_release_apks.ps1 -ArtifactDirectory .\release-artifacts
```

This writes `APK_SHA256SUMS.txt` for every APK in the supplied directory.

If `-ArtifactDirectory` is omitted, the script hashes the release APKs currently present in the standard RN and native Gradle output directories. In that mode, only the **currently built** RN architecture is available because the next clean/build reuses the same output path.

See `ACQUISITION_GUIDE.md` for a complete prospective build-and-retention example.
