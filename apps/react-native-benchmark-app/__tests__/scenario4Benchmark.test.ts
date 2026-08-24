import {
  BenchmarkValidationError,
  calculateOpsPerSecond,
  expectedArraySum,
  monotonicNow,
  runTimedOperations,
  runUntimedDiagnostic,
  verifyArrayResult,
  verifyScalarResult,
} from '../screens/scenario4Benchmark';

describe('scenario4Benchmark helpers', () => {
  test('calculates ops per second from completed operations and duration', () => {
    expect(calculateOpsPerSecond({completedOps: 10_000, durationMs: 2_000})).toBe(5000);
    expect(calculateOpsPerSecond(null)).toBeNull();
  });

  test('validates scalar results', () => {
    expect(() => verifyScalarResult(41, 42)).not.toThrow();
    expect(() => verifyScalarResult(41, 43)).toThrow(BenchmarkValidationError);
  });

  test('validates array sums', () => {
    const payload = [0, 1, 2, 3, 4];
    const expected = expectedArraySum(payload);

    expect(expected).toBe(10);
    expect(() => verifyArrayResult(expected, payload.length, 10)).not.toThrow();
    expect(() => verifyArrayResult(expected, payload.length, 9)).toThrow(
      BenchmarkValidationError,
    );
  });

  test('keeps correctness validation outside the timed operation loop', async () => {
    const now = jest.fn().mockReturnValueOnce(100).mockReturnValueOnce(175.9);
    const operation = jest.fn(async (index: number) => index + 1);

    const result = await runTimedOperations({
      operationCount: 3,
      operation,
      shouldStop: () => false,
      now,
    });

    expect(result).toEqual({
      benchmark: {durationMs: 76, completedOps: 3},
      lastValue: 3,
      stoppedEarly: false,
    });
    expect(operation).toHaveBeenCalledTimes(3);
    expect(now).toHaveBeenCalledTimes(2);
  });

  test('runs full correctness diagnostics outside the measurement path', async () => {
    const validated: number[] = [];

    await runUntimedDiagnostic({
      operationCount: 3,
      operation: async index => index + 1,
      validateResult: (index, value) => {
        verifyScalarResult(index, value);
        validated.push(value);
      },
    });

    expect(validated).toEqual([1, 2, 3]);
  });

  test('prefers a monotonic timer when performance.now is available', () => {
    const runtime = globalThis as typeof globalThis & {
      performance?: {now?: () => number};
    };
    const originalPerformance = runtime.performance;
    const mockPerformance = {now: jest.fn(() => 123.456)};

    Object.defineProperty(globalThis, 'performance', {
      configurable: true,
      value: mockPerformance,
    });

    expect(monotonicNow()).toBe(123.456);

    Object.defineProperty(globalThis, 'performance', {
      configurable: true,
      value: originalPerformance,
    });
  });
});
