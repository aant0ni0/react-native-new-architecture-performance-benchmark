# React Native New Architecture Performance Benchmark

This repository accompanies the paper **"React Native New Architecture Performance: An Empirical Comparison with Legacy Architecture and Native Android"**.

It contains:

- a React Native benchmark application covering the Legacy Architecture and the New Architecture,
- a native Android benchmark application used as the baseline implementation,
- curated CSV result tables for the benchmark scenarios reported in the study.

The repository is intentionally focused on the benchmark artifact itself. Manuscript sources, intermediate spreadsheets, and exploratory analysis material are maintained separately.

## Repository Structure

```text
react-native-new-architecture-performance-benchmark/
  apps/
    react-native-benchmark-app/
    native-android-benchmark-app/
  data/
    README.md
    results/
      s1_latency_results.csv
      s2_scroll_results.csv
      s3_js_driver_results.csv
      s3_native_driver_results.csv
      s4_scalar_call_results.csv
      s4_array_call_results.csv
      s5_startup_results.csv
  LICENSE
  README.md
```

## Benchmark Scope

The benchmark suite covers five scenarios:

1. real-time UI updates,
2. large-list auto-scroll,
3. UI animations,
4. JavaScript-native communication,
5. application startup time.

Scenario 3 is provided in two result variants:

- JS-driven animations,
- native-driver animations.

Scenario 4 is provided in two result variants:

- scalar/simple calls,
- array/complex calls.

## Applications

### React Native Benchmark App

Location: `apps/react-native-benchmark-app/`

This application contains the React Native implementations used for the Legacy Architecture and New Architecture measurements. It also includes the native Android modules used by the React Native benchmark scenarios.

The local application README contains implementation-specific details and run instructions.

### Native Android Benchmark App

Location: `apps/native-android-benchmark-app/`

This application contains the native Android baseline implementation used in the comparative study.

The local application README contains implementation-specific details and run instructions.

## Results Data

Location: `data/results/`

The CSV files contain curated scenario result tables prepared for repository publication.

Important formatting note:

- files use the semicolon (`;`) as the column delimiter,
- decimal values follow the spreadsheet locale and may use a comma as the decimal separator.

A short description of every CSV file is provided in `data/README.md`.

## Reproducing the Applications

The benchmark applications can be explored independently from their subdirectories.

### React Native app

```sh
cd apps/react-native-benchmark-app
npm install
npm start
npm run android
```

### Native Android app

```sh
cd apps/native-android-benchmark-app
.\gradlew.bat installDebug
```

## License

This repository is distributed under the MIT License. See `LICENSE` for details.
