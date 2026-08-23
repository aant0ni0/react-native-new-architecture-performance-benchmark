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

A connected Android device is required for device-specific ADB properties.

## Hash release APKs

After building both release variants:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\hash_release_apks.ps1
```

This writes `APK_SHA256SUMS.txt`.
