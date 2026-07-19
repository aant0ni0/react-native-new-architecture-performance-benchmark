import {NativeModules} from 'react-native';

/**
 * Architecture wrapper for Scenario 4.
 *
 * Keep these values aligned before running benchmarks:
 *
 * - IS_LEGACY = true  with `android/gradle.properties`: `newArchEnabled=false`
 * - IS_LEGACY = false with `android/gradle.properties`: `newArchEnabled=true`
 *
 * The benchmark screen imports only these wrapper functions and does not need
 * to know whether the calls go through the legacy bridge or TurboModules.
 */
export const IS_LEGACY = false;

type LegacyModule = {
  increment(v: number): Promise<number>;
  sumArray(values: number[]): Promise<number>;
};

type TurboModule = {
  increment(v: number): Promise<number>;
  sumArray(values: ReadonlyArray<number>): Promise<number>;
};

function legacyModule(): LegacyModule {
  return NativeModules.CommunicationBenchmarkLegacy as LegacyModule;
}

// Use require() so the TurboModule lookup is performed lazily only when the
// New Architecture path is selected.
function turboModule(): TurboModule {
  return require('../specs/NativeCommunicationBenchmark').default;
}

export function increment(value: number): Promise<number> {
  return IS_LEGACY
    ? legacyModule().increment(value)
    : turboModule().increment(value);
}

export function sumArray(values: number[]): Promise<number> {
  return IS_LEGACY
    ? legacyModule().sumArray(values)
    : turboModule().sumArray(values);
}
