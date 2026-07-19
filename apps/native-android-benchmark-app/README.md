# Native Android Benchmark App

This project contains the native Android implementation of the benchmark
scenarios used in the comparative study of:

- React Native Legacy Architecture
- React Native New Architecture
- native Android

The app focuses on benchmark implementation only. Research data, analysis
scripts, figures, and paper sources should live outside this application
repository in the final research artifact.

## Scenarios

The app currently contains four benchmark scenarios:

1. real-time UI updates
2. large-list auto-scroll
3. UI animations
4. JS-native style communication reference implemented fully on Android

Each scenario is implemented as a separate activity under
`app/src/main/java/com/example/nativebenchmarkapp/`.

## Project Structure

```text
app/src/main/java/   Android activities and benchmark logic
app/src/main/res/    layouts, drawables, and other resources
gradle/              Gradle wrapper and version catalog
```

## Requirements

- Android Studio
- Android SDK 24+
- JDK 11

## Running The App

Build and install the debug variant:

```sh
.\gradlew.bat installDebug
```

## Notes For Public Release

- Local IDE files and machine-specific settings are intentionally ignored.
- No release keystore is included in the public-ready project state.
- Benchmark output files should be reviewed later and moved into the final
  research-artifact structure if they are intended to be published as raw data.
