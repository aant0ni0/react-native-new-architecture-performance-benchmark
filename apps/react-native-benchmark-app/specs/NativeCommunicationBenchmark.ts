/**
 * TurboModule spec for Scenario 4: JS-Native Communication Benchmark.
 *
 * Codegen generates NativeCommunicationBenchmarkSpec.kt from this file.
 * The same JS API works in both architecture modes:
 *   newArchEnabled=true  → JSI direct call (TurboModule)
 *   newArchEnabled=false → bridge async queue (Legacy interop)
 *
 * increment() is intentionally trivial (value + 1) so that measured time
 * reflects communication overhead, not computation.
 */
import type {TurboModule} from 'react-native';
import {TurboModuleRegistry} from 'react-native';

export interface Spec extends TurboModule {
  increment(value: number): Promise<number>;
  sumArray(values: ReadonlyArray<number>): Promise<number>;
}

export default TurboModuleRegistry.getEnforcing<Spec>('CommunicationBenchmark');
