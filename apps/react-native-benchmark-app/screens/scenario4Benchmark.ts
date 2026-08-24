export interface BenchmarkResult {
  durationMs: number;
  completedOps: number;
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
