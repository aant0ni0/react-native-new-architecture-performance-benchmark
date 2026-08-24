import React, {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import {
  increment as nativeIncrement,
  sumArray as nativeSumArray,
} from '../modules/CommunicationModule';
import {
  BenchmarkResult,
  calculateOpsPerSecond,
  expectedArraySum,
  runTimedOperations,
  runUntimedDiagnostic,
  verifyArrayResult,
  verifyScalarResult,
} from './scenario4Benchmark';

const SIMPLE_OP_COUNT = 100_000;
const ARRAY_OP_COUNT = 10_000;
const ARRAY_SIZES = [1, 10, 100, 1_000, 10_000] as const;
const DEFAULT_ARRAY_SIZE = 1_000;

type TestStatus =
  | 'Idle'
  | 'Running'
  | 'Validating'
  | 'Validated'
  | 'Finished'
  | 'Stopped'
  | 'Failed';

interface Props {
  onBack: () => void;
}

interface TestCardProps {
  label: string;
  description: string;
  status: TestStatus;
  result: BenchmarkResult | null;
  error: string | null;
  running: boolean;
  anyRunning: boolean;
  onStart: () => void;
  onValidate: () => void;
  onStop: () => void;
  children?: React.ReactNode;
}

function isActiveStatus(status: TestStatus): boolean {
  return status === 'Running' || status === 'Validating';
}

export default function Scenario4Screen({onBack}: Props): React.JSX.Element {
  const [status1, setStatus1] = useState<TestStatus>('Idle');
  const [result1, setResult1] = useState<BenchmarkResult | null>(null);
  const [error1, setError1] = useState<string | null>(null);
  const [status2, setStatus2] = useState<TestStatus>('Idle');
  const [result2, setResult2] = useState<BenchmarkResult | null>(null);
  const [error2, setError2] = useState<string | null>(null);
  const [arraySize, setArraySize] = useState<number>(DEFAULT_ARRAY_SIZE);

  const statusRef1 = useRef<TestStatus>('Idle');
  const statusRef2 = useRef<TestStatus>('Idle');
  const shouldStop1 = useRef(false);
  const shouldStop2 = useRef(false);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const isAnyRunning = isActiveStatus(status1) || isActiveStatus(status2);
  const sharedArray = useMemo(
    () => Array.from({length: arraySize}, (_, index) => index),
    [arraySize],
  );
  const sharedArrayExpectedSum = useMemo(
    () => expectedArraySum(sharedArray),
    [sharedArray],
  );

  const selectArraySize = useCallback((size: number) => {
    if (isActiveStatus(statusRef1.current) || isActiveStatus(statusRef2.current)) {
      return;
    }

    setArraySize(size);
    setResult2(null);
    setError2(null);
    statusRef2.current = 'Idle';
    setStatus2('Idle');
  }, []);

  const runBenchmark = useCallback(
    async (
      operationCount: number,
      shouldStopRef: React.MutableRefObject<boolean>,
      setStatus: React.Dispatch<React.SetStateAction<TestStatus>>,
      setResult: React.Dispatch<React.SetStateAction<BenchmarkResult | null>>,
      setError: React.Dispatch<React.SetStateAction<string | null>>,
      statusRef: React.MutableRefObject<TestStatus>,
      operation: (index: number) => Promise<number>,
      runPreflight: () => Promise<void>,
      validateFinalResult: (completedOps: number, lastValue: number | null) => void,
    ) => {
      shouldStopRef.current = false;
      statusRef.current = 'Running';
      setStatus('Running');
      setResult(null);
      setError(null);

      try {
        // Correctness checks run outside the timed loop so they do not alter throughput.
        await runPreflight();
        const timedResult = await runTimedOperations({
          operationCount,
          operation,
          shouldStop: () => shouldStopRef.current,
        });
        validateFinalResult(
          timedResult.benchmark.completedOps,
          timedResult.lastValue,
        );

        if (!isMounted.current) {
          return;
        }

        statusRef.current = timedResult.stoppedEarly ? 'Stopped' : 'Finished';
        setStatus(timedResult.stoppedEarly ? 'Stopped' : 'Finished');
        setResult(timedResult.benchmark);
      } catch (error) {
        if (!isMounted.current) {
          return;
        }

        statusRef.current = 'Failed';
        setStatus('Failed');
        setResult(null);
        setError(
          error instanceof Error
            ? error.message
            : 'Scenario 4 benchmark failed unexpectedly.',
        );
      }
    },
    [],
  );

  const startTest1 = useCallback(async () => {
    if (isActiveStatus(statusRef1.current) || isActiveStatus(statusRef2.current)) {
      return;
    }

    await runBenchmark(
      SIMPLE_OP_COUNT,
      shouldStop1,
      setStatus1,
      setResult1,
      setError1,
      statusRef1,
      index => nativeIncrement(index),
      async () => verifyScalarResult(0, await nativeIncrement(0)),
      (completedOps, lastValue) => {
        if (completedOps > 0 && lastValue !== null) {
          verifyScalarResult(completedOps - 1, lastValue);
        }
      },
    );
  }, [runBenchmark]);

  const stopTest1 = useCallback(() => {
    if (statusRef1.current !== 'Running') {
      return;
    }
    shouldStop1.current = true;
  }, []);

  const validateTest1 = useCallback(async () => {
    if (isAnyRunning) {
      return;
    }

    statusRef1.current = 'Validating';
    setStatus1('Validating');
    setResult1(null);
    setError1(null);

    try {
      await runUntimedDiagnostic({
        operationCount: SIMPLE_OP_COUNT,
        operation: index => nativeIncrement(index),
        validateResult: (index, nativeValue) => verifyScalarResult(index, nativeValue),
      });
      if (!isMounted.current) {
        return;
      }
      statusRef1.current = 'Validated';
      setStatus1('Validated');
    } catch (error) {
      if (!isMounted.current) {
        return;
      }
      statusRef1.current = 'Failed';
      setStatus1('Failed');
      setError1(
        error instanceof Error
          ? error.message
          : 'Scenario 4 diagnostic failed unexpectedly.',
      );
    }
  }, [isAnyRunning]);

  const startTest2 = useCallback(async () => {
    if (isActiveStatus(statusRef1.current) || isActiveStatus(statusRef2.current)) {
      return;
    }

    await runBenchmark(
      ARRAY_OP_COUNT,
      shouldStop2,
      setStatus2,
      setResult2,
      setError2,
      statusRef2,
      () => nativeSumArray(sharedArray),
      async () =>
        verifyArrayResult(
          sharedArrayExpectedSum,
          sharedArray.length,
          await nativeSumArray(sharedArray),
        ),
      (completedOps, lastValue) => {
        if (completedOps > 0 && lastValue !== null) {
          verifyArrayResult(
            sharedArrayExpectedSum,
            sharedArray.length,
            lastValue,
          );
        }
      },
    );
  }, [runBenchmark, sharedArray, sharedArrayExpectedSum]);

  const stopTest2 = useCallback(() => {
    if (statusRef2.current !== 'Running') {
      return;
    }
    shouldStop2.current = true;
  }, []);

  const validateTest2 = useCallback(async () => {
    if (isAnyRunning) {
      return;
    }

    statusRef2.current = 'Validating';
    setStatus2('Validating');
    setResult2(null);
    setError2(null);

    try {
      await runUntimedDiagnostic({
        operationCount: ARRAY_OP_COUNT,
        operation: () => nativeSumArray(sharedArray),
        validateResult: (_index, nativeValue) =>
          verifyArrayResult(
            sharedArrayExpectedSum,
            sharedArray.length,
            nativeValue,
          ),
      });
      if (!isMounted.current) {
        return;
      }
      statusRef2.current = 'Validated';
      setStatus2('Validated');
    } catch (error) {
      if (!isMounted.current) {
        return;
      }
      statusRef2.current = 'Failed';
      setStatus2('Failed');
      setError2(
        error instanceof Error
          ? error.message
          : 'Scenario 4 diagnostic failed unexpectedly.',
      );
    }
  }, [isAnyRunning, sharedArray, sharedArrayExpectedSum]);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      <Text style={styles.title}>JS-Native Communication Benchmark</Text>

      <ScrollView>
        <TestCard
          label="Test 1: Simple (number)"
          description={`${SIMPLE_OP_COUNT.toLocaleString()} round-trips, value + 1`}
          status={status1}
          result={result1}
          error={error1}
          running={status1 === 'Running'}
          anyRunning={isAnyRunning}
          onStart={startTest1}
          onValidate={validateTest1}
          onStop={stopTest1}
        />

        <TestCard
          label="Test 2: Complex (array)"
          description={`${ARRAY_OP_COUNT.toLocaleString()} round-trips, sum of ${arraySize.toLocaleString()} elements`}
          status={status2}
          result={result2}
          error={error2}
          running={status2 === 'Running'}
          anyRunning={isAnyRunning}
          onStart={startTest2}
          onValidate={validateTest2}
          onStop={stopTest2}
        >
          <PayloadSizeSelector
            sizes={ARRAY_SIZES}
            selectedSize={arraySize}
            disabled={isAnyRunning}
            onSelect={selectArraySize}
          />
        </TestCard>
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.button, styles.backButton, isAnyRunning && styles.buttonDisabled]}
          onPress={onBack}
          disabled={isAnyRunning}
          activeOpacity={0.7}>
          <Text style={styles.buttonText}>Back to Menu</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

function TestCard({
  label,
  description,
  status,
  result,
  error,
  running,
  anyRunning,
  onStart,
  onValidate,
  onStop,
  children,
}: TestCardProps): React.JSX.Element {
  const opsPerSecond = calculateOpsPerSecond(result);

  return (
    <View style={styles.card}>
      <Text style={styles.cardLabel}>{label}</Text>
      <Text style={styles.cardDescription}>{description}</Text>
      {children}

      <View style={styles.statsBlock}>
        <Text style={styles.statText}>
          Status: <Text style={styles.statValue}>{status}</Text>
        </Text>
        {result !== null && (
          <>
            <Text style={styles.statText}>
              Duration: <Text style={styles.statValue}>{result.durationMs} ms</Text>
            </Text>
            <Text style={styles.statText}>
              Completed ops: <Text style={styles.statValue}>{result.completedOps.toLocaleString()}</Text>
            </Text>
            {opsPerSecond !== null && (
              <Text style={styles.statText}>
                Ops/sec: <Text style={styles.statValue}>{opsPerSecond.toLocaleString()}</Text>
              </Text>
            )}
          </>
        )}
        {error !== null && (
          <Text style={styles.errorText}>
            Error: <Text style={styles.errorValue}>{error}</Text>
          </Text>
        )}
      </View>

      <View style={styles.buttonRow}>
        <TouchableOpacity
          style={[
            styles.button,
            styles.startButton,
            (running || anyRunning) && styles.buttonDisabled,
          ]}
          onPress={onStart}
          disabled={anyRunning}
          activeOpacity={0.7}>
          <Text style={styles.buttonText}>Start</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.button, styles.validateButton, anyRunning && styles.buttonDisabled]}
          onPress={onValidate}
          disabled={anyRunning}
          activeOpacity={0.7}>
          <Text style={styles.buttonText}>Verify all</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.button, styles.stopButton, !running && styles.buttonDisabled]}
          onPress={onStop}
          disabled={!running}
          activeOpacity={0.7}>
          <Text style={styles.buttonText}>Stop</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

function PayloadSizeSelector({
  sizes,
  selectedSize,
  disabled,
  onSelect,
}: {
  sizes: readonly number[];
  selectedSize: number;
  disabled: boolean;
  onSelect: (size: number) => void;
}): React.JSX.Element {
  return (
    <View style={styles.payloadSection}>
      <Text style={styles.payloadLabel}>Payload size</Text>
      <View style={styles.payloadOptions}>
        {sizes.map(size => {
          const selected = size === selectedSize;

          return (
            <TouchableOpacity
              key={size}
              style={[
                styles.payloadButton,
                selected && styles.payloadButtonSelected,
                disabled && styles.buttonDisabled,
              ]}
              onPress={() => onSelect(size)}
              disabled={disabled}
              activeOpacity={0.7}>
              <Text
                style={[
                  styles.payloadButtonText,
                  selected && styles.payloadButtonTextSelected,
                ]}>
                {size.toLocaleString()}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#1a1a2e',
    color: '#ffffff',
    letterSpacing: 0.5,
  },
  card: {
    backgroundColor: '#ffffff',
    marginHorizontal: 12,
    marginTop: 12,
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  cardLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1a1a2e',
    marginBottom: 2,
  },
  cardDescription: {
    fontSize: 11,
    color: '#888888',
    marginBottom: 8,
  },
  payloadSection: {
    marginBottom: 10,
  },
  payloadLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#555555',
    marginBottom: 6,
  },
  payloadOptions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  payloadButton: {
    minWidth: 58,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#cfd8dc',
    backgroundColor: '#ffffff',
    alignItems: 'center',
  },
  payloadButtonSelected: {
    backgroundColor: '#1a1a2e',
    borderColor: '#1a1a2e',
  },
  payloadButtonText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#455a64',
  },
  payloadButtonTextSelected: {
    color: '#ffffff',
  },
  statsBlock: {
    gap: 2,
    marginBottom: 10,
  },
  statText: {
    fontSize: 12,
    color: '#555555',
  },
  statValue: {
    fontWeight: '700',
    color: '#1a1a2e',
  },
  errorText: {
    fontSize: 12,
    color: '#ad1457',
    marginTop: 4,
  },
  errorValue: {
    fontWeight: '700',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 10,
  },
  footer: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  button: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  startButton: {
    backgroundColor: '#2e7d32',
  },
  stopButton: {
    backgroundColor: '#c62828',
  },
  validateButton: {
    backgroundColor: '#1565c0',
  },
  backButton: {
    backgroundColor: '#455a64',
  },
  buttonDisabled: {
    opacity: 0.38,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
});
