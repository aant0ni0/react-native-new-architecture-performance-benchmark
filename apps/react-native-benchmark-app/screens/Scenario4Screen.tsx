import React, {useCallback, useEffect, useRef, useState} from 'react';
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

const SIMPLE_OP_COUNT = 100_000;
const ARRAY_OP_COUNT = 10_000;
const ARRAY_SIZE = 1_000;
const SHARED_ARRAY = Array.from({length: ARRAY_SIZE}, (_, index) => index);

type TestStatus = 'Idle' | 'Running' | 'Finished' | 'Stopped';

type AsyncOperation = () => Promise<number>;

interface BenchmarkResult {
  durationMs: number;
  completedOps: number;
}

interface Props {
  onBack: () => void;
}

interface TestCardProps {
  label: string;
  description: string;
  status: TestStatus;
  result: BenchmarkResult | null;
  running: boolean;
  anyRunning: boolean;
  onStart: () => void;
  onStop: () => void;
}

export default function Scenario4Screen({onBack}: Props): React.JSX.Element {
  const [status1, setStatus1] = useState<TestStatus>('Idle');
  const [result1, setResult1] = useState<BenchmarkResult | null>(null);
  const [status2, setStatus2] = useState<TestStatus>('Idle');
  const [result2, setResult2] = useState<BenchmarkResult | null>(null);

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

  const isAnyRunning = status1 === 'Running' || status2 === 'Running';

  const runBenchmark = useCallback(
    async (
      operationCount: number,
      shouldStopRef: React.MutableRefObject<boolean>,
      setStatus: React.Dispatch<React.SetStateAction<TestStatus>>,
      setResult: React.Dispatch<React.SetStateAction<BenchmarkResult | null>>,
      statusRef: React.MutableRefObject<TestStatus>,
      operationFactory: (index: number) => AsyncOperation,
    ) => {
      shouldStopRef.current = false;
      statusRef.current = 'Running';
      setStatus('Running');
      setResult(null);

      const startMs = Date.now();
      let completed = 0;

      for (let index = 0; index < operationCount; index++) {
        if (shouldStopRef.current) {
          break;
        }

        await operationFactory(index)();
        completed += 1;
      }

      if (!isMounted.current) {
        return;
      }

      const stoppedEarly = shouldStopRef.current && completed < operationCount;
      statusRef.current = stoppedEarly ? 'Stopped' : 'Finished';
      setStatus(stoppedEarly ? 'Stopped' : 'Finished');
      setResult({
        durationMs: Date.now() - startMs,
        completedOps: completed,
      });
    },
    [],
  );

  const startTest1 = useCallback(async () => {
    if (statusRef1.current === 'Running' || statusRef2.current === 'Running') {
      return;
    }

    await runBenchmark(
      SIMPLE_OP_COUNT,
      shouldStop1,
      setStatus1,
      setResult1,
      statusRef1,
      index => () => nativeIncrement(index),
    );
  }, [runBenchmark]);

  const stopTest1 = useCallback(() => {
    if (statusRef1.current !== 'Running') {
      return;
    }
    shouldStop1.current = true;
  }, []);

  const startTest2 = useCallback(async () => {
    if (statusRef1.current === 'Running' || statusRef2.current === 'Running') {
      return;
    }

    await runBenchmark(
      ARRAY_OP_COUNT,
      shouldStop2,
      setStatus2,
      setResult2,
      statusRef2,
      () => () => nativeSumArray(SHARED_ARRAY),
    );
  }, [runBenchmark]);

  const stopTest2 = useCallback(() => {
    if (statusRef2.current !== 'Running') {
      return;
    }
    shouldStop2.current = true;
  }, []);

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
          running={status1 === 'Running'}
          anyRunning={isAnyRunning}
          onStart={startTest1}
          onStop={stopTest1}
        />

        <TestCard
          label="Test 2: Complex (array)"
          description={`${ARRAY_OP_COUNT.toLocaleString()} round-trips, sum of ${ARRAY_SIZE.toLocaleString()} elements`}
          status={status2}
          result={result2}
          running={status2 === 'Running'}
          anyRunning={isAnyRunning}
          onStart={startTest2}
          onStop={stopTest2}
        />
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
  running,
  anyRunning,
  onStart,
  onStop,
}: TestCardProps): React.JSX.Element {
  const opsPerSecond =
    result && result.durationMs > 0
      ? Math.round(result.completedOps / (result.durationMs / 1000))
      : null;

  return (
    <View style={styles.card}>
      <Text style={styles.cardLabel}>{label}</Text>
      <Text style={styles.cardDescription}>{description}</Text>

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
