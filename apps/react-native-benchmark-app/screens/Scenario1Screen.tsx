import React, {useCallback, useEffect, useRef, useState} from 'react';
import {
  FlatList,
  ListRenderItemInfo,
  SafeAreaView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

declare const performance: {now: () => number};

interface DataItem {
  id: number;
  name: string;
  baseValue: number;
  currentValue: number;
  changePercent: number;
  previousValue: number;
}

type TestStatus = 'Idle' | 'Running' | 'Finished' | 'Stopped';

interface Metrics {
  avgLatency: number;
  minLatency: number;
  maxLatency: number;
  p50Latency: number;
  p95Latency: number;
  p99Latency: number;
  latencySamples: number;
  totalUpdates: number;
  measuredDurationMs: number;
  stoppedEarly: boolean;
}

interface Props {
  onBack: () => void;
}

const ITEM_COUNT = 20;
const INTERVAL_OPTIONS = [1000, 200, 100, 50];
const WARMUP_DURATION_MS = 10_000;
const MEASUREMENT_DURATION_MS = 60_000;

function generateInitialData(): DataItem[] {
  return Array.from({length: ITEM_COUNT}, (_, index) => {
    const baseValue = 100 + index * 5;
    return {
      id: index,
      name: `ITEM_${String(index + 1).padStart(2, '0')}`,
      baseValue,
      currentValue: baseValue,
      changePercent: 0,
      previousValue: baseValue,
    };
  });
}

function computeNewValue(baseValue: number, tick: number, itemIndex: number): number {
  return (
    baseValue +
    4 * Math.sin(tick / 8 + itemIndex * 0.7) +
    1.5 * Math.cos(tick / 5 + itemIndex * 0.35)
  );
}

function percentile(sorted: number[], percentileValue: number): number {
  if (sorted.length === 0) {
    return 0;
  }

  const index = Math.min(
    Math.floor((percentileValue / 100) * sorted.length),
    sorted.length - 1,
  );
  return sorted[index];
}

function getItemColor(item: DataItem): string {
  if (item.currentValue > item.previousValue) {
    return '#00aa00';
  }
  if (item.currentValue < item.previousValue) {
    return '#cc0000';
  }
  return '#888888';
}

export default function Scenario1Screen({onBack}: Props): React.JSX.Element {
  const [data, setData] = useState<DataItem[]>(generateInitialData);
  const [status, setStatus] = useState<TestStatus>('Idle');
  const [selectedInterval, setSelectedInterval] = useState(100);
  const [updateCount, setUpdateCount] = useState(0);
  const [isWarmup, setIsWarmup] = useState(false);
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  const updateIndexRef = useRef(0);
  const updateCountRef = useRef(0);
  const statusRef = useRef<TestStatus>('Idle');
  const isWarmupRef = useRef(true);
  const intervalRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const warmupTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const measurementTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const schedulerActiveRef = useRef(false);

  const latencySamplesRef = useRef<number[]>([]);
  const dataGeneratedAtRef = useRef(0);
  const pendingLatencySeqRef = useRef(0);
  const lastRecordedSeqRef = useRef(0);
  const measurementStartRef = useRef(0);

  const clearTimers = useCallback(() => {
    schedulerActiveRef.current = false;

    if (intervalRef.current !== null) {
      clearTimeout(intervalRef.current);
      intervalRef.current = null;
    }
    if (warmupTimerRef.current !== null) {
      clearTimeout(warmupTimerRef.current);
      warmupTimerRef.current = null;
    }
    if (measurementTimerRef.current !== null) {
      clearTimeout(measurementTimerRef.current);
      measurementTimerRef.current = null;
    }
  }, []);

  const finalizeMetrics = useCallback((stoppedEarly: boolean) => {
    const measuredDurationMs =
      measurementStartRef.current > 0
        ? Date.now() - measurementStartRef.current
        : 0;

    requestAnimationFrame(() => {
      const latencies = latencySamplesRef.current;
      const sorted = [...latencies].sort((a, b) => a - b);
      const avgLatency =
        latencies.length > 0
          ? latencies.reduce((sum, latency) => sum + latency, 0) / latencies.length
          : 0;

      setMetrics({
        avgLatency,
        minLatency: sorted.length > 0 ? sorted[0] : 0,
        maxLatency: sorted.length > 0 ? sorted[sorted.length - 1] : 0,
        p50Latency: percentile(sorted, 50),
        p95Latency: percentile(sorted, 95),
        p99Latency: percentile(sorted, 99),
        latencySamples: latencies.length,
        totalUpdates: updateCountRef.current,
        measuredDurationMs,
        stoppedEarly,
      });
    });
  }, []);

  const performUpdate = useCallback(() => {
    const tick = updateIndexRef.current;

    if (!isWarmupRef.current) {
      dataGeneratedAtRef.current = performance.now();
      pendingLatencySeqRef.current += 1;
    }

    setData(previousData =>
      previousData.map((item, index) => {
        const newValue = computeNewValue(item.baseValue, tick, index);
        return {
          ...item,
          previousValue: item.currentValue,
          currentValue: newValue,
          changePercent: ((newValue - item.baseValue) / item.baseValue) * 100,
        };
      }),
    );

    updateIndexRef.current += 1;

    if (!isWarmupRef.current) {
      updateCountRef.current += 1;
      setUpdateCount(currentValue => currentValue + 1);

      const capturedSeq = pendingLatencySeqRef.current;
      const capturedAt = dataGeneratedAtRef.current;

      requestAnimationFrame(() => {
        if (
          statusRef.current === 'Running' &&
          !isWarmupRef.current &&
          capturedAt > 0 &&
          capturedSeq > lastRecordedSeqRef.current
        ) {
          latencySamplesRef.current.push(performance.now() - capturedAt);
          lastRecordedSeqRef.current = capturedSeq;
        }
      });
    }
  }, []);

  const finishTest = useCallback(() => {
    statusRef.current = 'Finished';
    setStatus('Finished');
    setIsWarmup(false);
    clearTimers();
    finalizeMetrics(false);
  }, [clearTimers, finalizeMetrics]);

  const stopTest = useCallback(() => {
    statusRef.current = 'Stopped';
    setStatus('Stopped');
    setIsWarmup(false);
    clearTimers();
    finalizeMetrics(true);
  }, [clearTimers, finalizeMetrics]);

  const startTest = useCallback(() => {
    updateIndexRef.current = 0;
    updateCountRef.current = 0;
    latencySamplesRef.current = [];
    dataGeneratedAtRef.current = 0;
    pendingLatencySeqRef.current = 0;
    lastRecordedSeqRef.current = 0;
    measurementStartRef.current = 0;
    isWarmupRef.current = true;
    schedulerActiveRef.current = false;

    setData(generateInitialData());
    setUpdateCount(0);
    setMetrics(null);
    setIsWarmup(true);
    statusRef.current = 'Running';
    setStatus('Running');

    schedulerActiveRef.current = true;
    const interval = selectedInterval;
    const startedAt = Date.now();
    let tick = 1;

    const schedule = () => {
      if (!schedulerActiveRef.current) {
        return;
      }

      performUpdate();

      const nextTickDelay = startedAt + tick * interval - Date.now();
      tick += 1;
      intervalRef.current = setTimeout(schedule, Math.max(0, nextTickDelay));
    };

    intervalRef.current = setTimeout(schedule, interval);

    warmupTimerRef.current = setTimeout(() => {
      isWarmupRef.current = false;
      measurementStartRef.current = Date.now();
      setIsWarmup(false);
    }, WARMUP_DURATION_MS);

    measurementTimerRef.current = setTimeout(
      finishTest,
      WARMUP_DURATION_MS + MEASUREMENT_DURATION_MS,
    );
  }, [finishTest, performUpdate, selectedInterval]);

  useEffect(() => clearTimers, [clearTimers]);

  const renderItem = useCallback(
    ({item}: ListRenderItemInfo<DataItem>) => {
      const color = getItemColor(item);
      const sign = item.changePercent >= 0 ? '+' : '';

      return (
        <View style={styles.listItem}>
          <Text style={styles.itemName}>{item.name}</Text>
          <Text style={[styles.itemValue, {color}]}>
            {item.currentValue.toFixed(2)}
          </Text>
          <Text style={[styles.itemChange, {color}]}> 
            {sign}
            {item.changePercent.toFixed(2)}%
          </Text>
        </View>
      );
    },
    [],
  );

  const keyExtractor = useCallback((item: DataItem) => item.id.toString(), []);
  const isRunning = status === 'Running';
  const statusLabel = isRunning && isWarmup ? 'Running (Warmup)' : status;

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      <Text style={styles.title}>Real-Time Updates Benchmark</Text>

      <View style={styles.statusSection}>
        <Text style={styles.statusText}>
          Status: <Text style={styles.statusValue}>{statusLabel}</Text>
        </Text>
        <Text style={styles.statusText}>
          Interval: <Text style={styles.statusValue}>{selectedInterval} ms</Text>
        </Text>
        <Text style={styles.statusText}>
          Updates: <Text style={styles.statusValue}>{updateCount}</Text>
        </Text>
      </View>

      <View style={styles.controlsSection}>
        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={[styles.button, styles.startButton, isRunning && styles.buttonDisabled]}
            onPress={startTest}
            disabled={isRunning}
            activeOpacity={0.7}>
            <Text style={styles.buttonText}>Start</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.button, styles.stopButton, !isRunning && styles.buttonDisabled]}
            onPress={stopTest}
            disabled={!isRunning}
            activeOpacity={0.7}>
            <Text style={styles.buttonText}>Stop</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.intervalRow}>
          {INTERVAL_OPTIONS.map(interval => {
            const selected = selectedInterval === interval;

            return (
              <TouchableOpacity
                key={interval}
                style={[
                  styles.intervalButton,
                  selected && styles.intervalButtonSelected,
                  isRunning && styles.buttonDisabled,
                ]}
                onPress={() => setSelectedInterval(interval)}
                disabled={isRunning}
                activeOpacity={0.7}>
                <Text
                  style={[
                    styles.intervalButtonText,
                    selected && styles.intervalButtonTextSelected,
                  ]}>
                  {interval} ms
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <TouchableOpacity
          style={[styles.button, styles.backButton, isRunning && styles.buttonDisabled]}
          onPress={onBack}
          disabled={isRunning}
          activeOpacity={0.7}>
          <Text style={styles.buttonText}>Back to Menu</Text>
        </TouchableOpacity>
      </View>

      {metrics !== null && (
        <View style={styles.metricsSection}>
          <Text style={styles.metricsTitle}>
            Results{metrics.stoppedEarly ? ' (stopped early)' : ''}
          </Text>
          <View style={styles.metricsGrid}>
            <Text style={styles.metricsText}>Avg Latency: <Text style={styles.metricsValue}>{metrics.avgLatency.toFixed(2)} ms</Text></Text>
            <Text style={styles.metricsText}>Min Latency: <Text style={styles.metricsValue}>{metrics.minLatency.toFixed(2)} ms</Text></Text>
            <Text style={styles.metricsText}>Max Latency: <Text style={styles.metricsValue}>{metrics.maxLatency.toFixed(2)} ms</Text></Text>
            <Text style={styles.metricsText}>p50 Latency: <Text style={styles.metricsValue}>{metrics.p50Latency.toFixed(2)} ms</Text></Text>
            <Text style={styles.metricsText}>p95 Latency: <Text style={styles.metricsValue}>{metrics.p95Latency.toFixed(2)} ms</Text></Text>
            <Text style={styles.metricsText}>p99 Latency: <Text style={styles.metricsValue}>{metrics.p99Latency.toFixed(2)} ms</Text></Text>
            <Text style={styles.metricsText}>Latency Samples: <Text style={styles.metricsValue}>{metrics.latencySamples}</Text></Text>
            <Text style={styles.metricsText}>Total Updates: <Text style={styles.metricsValue}>{metrics.totalUpdates}</Text></Text>
            <Text style={styles.metricsText}>Measured Duration: <Text style={styles.metricsValue}>{metrics.measuredDurationMs} ms</Text></Text>
          </View>
        </View>
      )}

      <View style={styles.listHeader}>
        <Text style={styles.listHeaderText}>Name</Text>
        <Text style={styles.listHeaderText}>Value</Text>
        <Text style={styles.listHeaderText}>Change</Text>
      </View>
      <FlatList
        data={data}
        renderItem={renderItem}
        keyExtractor={keyExtractor}
        style={styles.list}
        contentContainerStyle={styles.listContent}
        scrollEnabled={!isRunning}
      />
    </SafeAreaView>
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
  statusSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  statusText: {
    fontSize: 12,
    color: '#555555',
  },
  statusValue: {
    fontWeight: '700',
    color: '#1a1a2e',
  },
  controlsSection: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    gap: 8,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 10,
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
  intervalRow: {
    flexDirection: 'row',
    gap: 6,
  },
  intervalButton: {
    flex: 1,
    paddingVertical: 7,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#eeeeee',
    borderWidth: 1,
    borderColor: '#cccccc',
  },
  intervalButtonSelected: {
    backgroundColor: '#1a1a2e',
    borderColor: '#1a1a2e',
  },
  intervalButtonText: {
    fontSize: 11,
    color: '#444444',
    fontWeight: '600',
  },
  intervalButtonTextSelected: {
    color: '#ffffff',
  },
  metricsSection: {
    marginHorizontal: 12,
    marginTop: 8,
    padding: 10,
    backgroundColor: '#ffffff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  metricsTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#1a1a2e',
    marginBottom: 6,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
  },
  metricsText: {
    fontSize: 12,
    color: '#555555',
    width: '48%',
  },
  metricsValue: {
    fontWeight: '700',
    color: '#1a1a2e',
  },
  listHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#e8e8e8',
    marginTop: 8,
  },
  listHeaderText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#444444',
    flex: 1,
    textAlign: 'center',
  },
  list: {
    flex: 1,
  },
  listContent: {
    paddingBottom: 8,
  },
  listItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 9,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  itemName: {
    flex: 1,
    fontSize: 12,
    fontWeight: '600',
    color: '#222222',
  },
  itemValue: {
    flex: 1,
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
  itemChange: {
    flex: 1,
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'right',
  },
});
