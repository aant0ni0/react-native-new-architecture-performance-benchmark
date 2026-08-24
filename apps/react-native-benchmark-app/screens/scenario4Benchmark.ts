export interface BenchmarkResult {
  durationMs: number;
  completedOps: number;
}

export interface TimedOperationsResult {
  benchmark: BenchmarkResult;
  lastValue: number | null;
  stoppedEarly: boolean;
}

interface TimedOperationsOptions {
  operationCount: number;
  operation: (index: number) => Promise<number>;
  shouldStop: () => boolean;
  now?: () => number;
}

interface DiagnosticOptions {
  operationCount: number;
  operation: (index: number) => Promise<number>;
  validateResult: (index: number, value: number) => void;
}

export class BenchmarkValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'BenchmarkValidationError';
  }
}

export function monotonicNow(): number {
  const runtime = globalThis as typeof globalThis & {
    performance?: {now?: () => number};
  };
  const timer = runtime.performance?.now;
  return typeof timer === 'function' ? timer.call(runtime.performance) : Date.now();
}

export function calculateOpsPerSecond(
  result: BenchmarkResult | null,
): number | null {
  if (result === null || result.durationMs <= 0) {
    return null;
  }

  return Math.round(result.completedOps / (result.durationMs / 1000));
}

export async function runTimedOperations({
  operationCount,
  operation,
  shouldStop,
  now = monotonicNow,
}: TimedOperationsOptions): Promise<TimedOperationsResult> {
  const startMs = now();
  let completedOps = 0;
  let lastValue: number | null = null;
  let endMs: number | null = null;

  for (let index = 0; index < operationCount; index++) {
    if (shouldStop()) {
      break;
    }

    lastValue = await operation(index);
    if (shouldStop() || index + 1 === operationCount) {
      endMs = now();
    }
    completedOps += 1;

    if (endMs !== null) {
      break;
    }
  }

  const durationMs = Math.round((endMs ?? now()) - startMs);
  return {
    benchmark: {durationMs, completedOps},
    lastValue,
    stoppedEarly: completedOps < operationCount,
  };
}

export async function runUntimedDiagnostic({
  operationCount,
  operation,
  validateResult,
}: DiagnosticOptions): Promise<void> {
  for (let index = 0; index < operationCount; index++) {
    const value = await operation(index);
    validateResult(index, value);
  }
}

export function expectedScalarResult(input: number): number {
  return input + 1;
}

export function expectedArraySum(values: ReadonlyArray<number>): number {
  return values.reduce((sum, value) => sum + value, 0);
}

export function verifyScalarResult(input: number, actual: number): void {
  const expected = expectedScalarResult(input);
  if (actual !== expected) {
    throw new BenchmarkValidationError(
      `Scenario 4 scalar validation failed: expected ${expected}, received ${actual}.`,
    );
  }
}

export function verifyArrayResult(
  expectedSum: number,
  payloadSize: number,
  actual: number,
): void {
  if (actual !== expectedSum) {
    throw new BenchmarkValidationError(
      `Scenario 4 array validation failed for payload ${payloadSize}: expected ${expectedSum}, received ${actual}.`,
    );
  }
}
