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

interface ScrollItem {
  id: number;
  name: string;
  subtitle: string;
  value: number;
  status: 'ACTIVE' | 'INACTIVE';
}

type TestStatus = 'Idle' | 'Running' | 'Finished' | 'Stopped';

interface Props {
  onBack: () => void;
}

const ITEM_COUNT = 1000;
const ITEM_HEIGHT = 64;
const SCROLL_STEP = 200;
const SCROLL_TICK_MS = 16;
const MEASUREMENT_DURATION_MS = 60_000;
const DEFAULT_CONTAINER_HEIGHT = 600;

function generateScrollData(): ScrollItem[] {
  return Array.from({length: ITEM_COUNT}, (_, index) => ({
    id: index,
    name: `ITEM_${String(index + 1).padStart(4, '0')}`,
    subtitle: index % 2 === 0 ? 'Category A' : 'Category B',
    value: 100 + index * 0.75,
    status: index % 2 === 0 ? 'ACTIVE' : 'INACTIVE',
  }));
}

const SCROLL_DATA = generateScrollData();

export default function Scenario2Screen({onBack}: Props): React.JSX.Element {
  const [status, setStatus] = useState<TestStatus>('Idle');
  const [scrollCycles, setScrollCycles] = useState(0);
  const [measuredDurationMs, setMeasuredDurationMs] = useState<number | null>(null);

  const statusRef = useRef<TestStatus>('Idle');
  const scrollLoopActiveRef = useRef(false);
  const scrollCyclesRef = useRef(0);
  const scrollOffsetRef = useRef(0);
  const containerHeightRef = useRef(DEFAULT_CONTAINER_HEIGHT);
  const measurementStartRef = useRef(0);

  const schedulerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const measurementTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flatListRef = useRef<FlatList<ScrollItem>>(null);

  const clearTimers = useCallback(() => {
    scrollLoopActiveRef.current = false;

    if (schedulerRef.current !== null) {
      clearTimeout(schedulerRef.current);
      schedulerRef.current = null;
    }
    if (measurementTimerRef.current !== null) {
      clearTimeout(measurementTimerRef.current);
      measurementTimerRef.current = null;
    }
  }, []);

  const finishTest = useCallback(
    (stoppedEarly: boolean) => {
      const duration =
        measurementStartRef.current > 0
          ? Date.now() - measurementStartRef.current
          : 0;

      clearTimers();
      statusRef.current = stoppedEarly ? 'Stopped' : 'Finished';
      setStatus(stoppedEarly ? 'Stopped' : 'Finished');
      setMeasuredDurationMs(duration);
    },
    [clearTimers],
  );

  const startTest = useCallback(() => {
    scrollCyclesRef.current = 0;
    scrollOffsetRef.current = 0;
    measurementStartRef.current = Date.now();

    setScrollCycles(0);
    setMeasuredDurationMs(null);
    statusRef.current = 'Running';
    setStatus('Running');

    flatListRef.current?.scrollToOffset({offset: 0, animated: false});

    scrollLoopActiveRef.current = true;
    const startedAt = Date.now();
    let tick = 1;

    const scrollTick = () => {
      if (!scrollLoopActiveRef.current) {
        return;
      }

      const maxOffset = ITEM_COUNT * ITEM_HEIGHT - containerHeightRef.current;
      let nextOffset = scrollOffsetRef.current + SCROLL_STEP;

      if (nextOffset >= maxOffset) {
        nextOffset = 0;
        scrollCyclesRef.current += 1;
        setScrollCycles(scrollCyclesRef.current);
        flatListRef.current?.scrollToOffset({offset: 0, animated: false});
      } else {
        flatListRef.current?.scrollToOffset({offset: nextOffset, animated: false});
      }

      scrollOffsetRef.current = nextOffset;

      const nextTickDelay = startedAt + tick * SCROLL_TICK_MS - Date.now();
      tick += 1;
      schedulerRef.current = setTimeout(scrollTick, Math.max(0, nextTickDelay));
    };

    schedulerRef.current = setTimeout(scrollTick, SCROLL_TICK_MS);
    measurementTimerRef.current = setTimeout(
      () => finishTest(false),
      MEASUREMENT_DURATION_MS,
    );
  }, [finishTest]);

  useEffect(() => clearTimers, [clearTimers]);

  const renderItem = useCallback(
    ({item}: ListRenderItemInfo<ScrollItem>) => (
      <View style={styles.listItem}>
        <View style={styles.itemLeft}>
          <Text style={styles.itemName}>{item.name}</Text>
          <Text style={styles.itemSubtitle}>{item.subtitle}</Text>
        </View>
        <Text style={styles.itemValue}>{item.value.toFixed(2)}</Text>
        <Text
          style={[
            styles.itemStatus,
            item.status === 'ACTIVE' ? styles.statusActive : styles.statusInactive,
          ]}>
          {item.status}
        </Text>
      </View>
    ),
    [],
  );

  const keyExtractor = useCallback((item: ScrollItem) => item.id.toString(), []);
  const getItemLayout = useCallback(
    (_: unknown, index: number) => ({
      length: ITEM_HEIGHT,
      offset: ITEM_HEIGHT * index,
      index,
    }),
    [],
  );

  const isRunning = status === 'Running';

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      <Text style={styles.title}>Large List Scroll Benchmark</Text>

      <View style={styles.statusSection}>
        <Text style={styles.statusText}>
          Status: <Text style={styles.statusValue}>{status}</Text>
        </Text>
        <Text style={styles.statusText}>
          List Size: <Text style={styles.statusValue}>{ITEM_COUNT}</Text>
        </Text>
        <Text style={styles.statusText}>
          Scroll Cycles: <Text style={styles.statusValue}>{scrollCycles}</Text>
        </Text>
        {measuredDurationMs !== null && (
          <Text style={styles.statusText}>
            Measured Duration: <Text style={styles.statusValue}>{measuredDurationMs} ms</Text>
          </Text>
        )}
      </View>

      <View style={styles.controlsSection}>
        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={[styles.button, styles.startButton, isRunning && styles.buttonDisabled]}
            onPress={startTest}
            disabled={isRunning}
            activeOpacity={0.7}>
            <Text style={styles.buttonText}>Start Auto Scroll</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.button, styles.stopButton, !isRunning && styles.buttonDisabled]}
            onPress={() => finishTest(true)}
            disabled={!isRunning}
            activeOpacity={0.7}>
            <Text style={styles.buttonText}>Stop</Text>
          </TouchableOpacity>
        </View>
        <TouchableOpacity
          style={[styles.button, styles.backButton, isRunning && styles.buttonDisabled]}
          onPress={onBack}
          disabled={isRunning}
          activeOpacity={0.7}>
          <Text style={styles.buttonText}>Back to Menu</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.listHeader}>
        <Text style={styles.listHeaderTextWide}>Name / Category</Text>
        <Text style={styles.listHeaderText}>Value</Text>
        <Text style={styles.listHeaderText}>Status</Text>
      </View>

      <View
        style={styles.listContainer}
        onLayout={event => {
          containerHeightRef.current = event.nativeEvent.layout.height;
        }}>
        <FlatList
          ref={flatListRef}
          data={SCROLL_DATA}
          renderItem={renderItem}
          keyExtractor={keyExtractor}
          getItemLayout={getItemLayout}
          style={styles.list}
          scrollEnabled={!isRunning}
          removeClippedSubviews
        />
      </View>
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
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    gap: 2,
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
  listHeader: {
    flexDirection: 'row',
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#e8e8e8',
    marginTop: 8,
  },
  listHeaderText: {
    flex: 1,
    fontSize: 11,
    fontWeight: '700',
    color: '#444444',
    textAlign: 'center',
  },
  listHeaderTextWide: {
    flex: 2,
    fontSize: 11,
    fontWeight: '700',
    color: '#444444',
    textAlign: 'center',
  },
  listContainer: {
    flex: 1,
  },
  list: {
    flex: 1,
  },
  listItem: {
    height: ITEM_HEIGHT,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  itemLeft: {
    flex: 2,
    justifyContent: 'center',
  },
  itemName: {
    fontSize: 12,
    fontWeight: '600',
    color: '#222222',
  },
  itemSubtitle: {
    fontSize: 10,
    color: '#888888',
    marginTop: 2,
  },
  itemValue: {
    flex: 1,
    fontSize: 12,
    fontWeight: '600',
    color: '#1a1a2e',
    textAlign: 'center',
  },
  itemStatus: {
    flex: 1,
    fontSize: 11,
    fontWeight: '700',
    textAlign: 'right',
  },
  statusActive: {
    color: '#00aa00',
  },
  statusInactive: {
    color: '#888888',
  },
});
