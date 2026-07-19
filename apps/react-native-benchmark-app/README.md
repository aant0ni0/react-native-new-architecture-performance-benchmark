# React Native Benchmark App

This project contains the React Native implementation of the benchmark scenarios
used in the comparative study of:

- React Native Legacy Architecture
- React Native New Architecture
- native Android

The app focuses on benchmark implementation only. Research data, analysis
scripts, figures, and paper sources should live outside this application
repository in the final research artifact.

## Scenarios

The app currently contains four interactive benchmark scenarios:

1. real-time UI updates
2. large-list auto-scroll
3. UI animations
4. JS-native communication

Each scenario is implemented as a separate screen under `screens/`.

## Project Structure

```text
android/     Android host app and native benchmark modules
ios/         iOS host app
modules/     JS wrappers around native communication modules
screens/     Benchmark scenario screens
specs/       TurboModule specs used by React Native codegen
```

## Requirements

- Node.js 20 or newer
- npm
- Android SDK and Android Studio for Android builds
- Xcode and CocoaPods for iOS builds

## Running The App

Start Metro:

```sh
npm start
```

Run on Android:

```sh
npm run android
```

Run on iOS:

```sh
bundle install
bundle exec pod install
npm run ios
```

## Architecture Switching

Scenario 4 can be exercised against both React Native communication paths:

- Legacy Native Module
- TurboModule / New Architecture

To switch between them, update both:

- `android/gradle.properties`
- `modules/CommunicationModule.ts`

These two values must stay in sync:

- `newArchEnabled=false` with `IS_LEGACY = true`
- `newArchEnabled=true` with `IS_LEGACY = false`

## Notes For Public Release

- Local IDE files, Metro cache, and Codex helper files are intentionally ignored.
- Paper sources, generated figures, and ad hoc research notes are not part of
  the application itself and should be moved into a separate research-artifact
  structure before publication.
- Raw benchmark outputs should be stored in a separate data or artifact
  repository rather than alongside the application source code.
