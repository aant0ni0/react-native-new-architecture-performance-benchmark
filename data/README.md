# Data Files

This directory contains the curated CSV result tables included in the repository artifact.

## CSV Format Notes

- delimiter: semicolon (`;`)
- decimal separator: comma may be used in floating-point values
- encoding: exported from spreadsheet tooling for direct inspection and reuse

## Included Files

- `s1_latency_results.csv`  
  Final Scenario 1 result table for real-time UI updates, including latency and rendering-related metrics.

- `s2_scroll_results.csv`  
  Final Scenario 2 result table for large-list auto-scroll, including frame and resource metrics.

- `s3_js_driver_results.csv`  
  Final Scenario 3 result table for JavaScript-driven animations.

- `s3_native_driver_results.csv`  
  Final Scenario 3 result table for native-driver animations.

- `s4_scalar_call_results.csv`  
  Final Scenario 4 result table for scalar/simple JavaScript-native communication calls.

- `s4_array_call_results.csv`  
  Final Scenario 4 result table for array/complex JavaScript-native communication calls.

- `s5_startup_results.csv`  
  Final Scenario 5 result table for application startup measurements.
