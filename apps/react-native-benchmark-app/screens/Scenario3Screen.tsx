import React, {useCallback, useEffect, useRef, useState} from 'react';
import {
  Animated,
  Easing,
  SafeAreaView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

const BOX_COUNT = 15;
const MEASUREMENT_DURATION_MS = 60_000;
const TRANSLATE_X_RANGE = 50;
const TRANSLATE_Y_RANGE = 40;
const BASE_ANIM_X_MS = 1200;
const BASE_ANIM_Y_MS = 900;
const BASE_ANIM_SCALE_MS = 1500;
const BASE_ANIM_ROT_MS = 2000;
const ANIM_STEP_MS = 50;
const BOX_COLORS = [
  '#e53935', '#1e88e5', '#43a047',
  '#fb8c00', '#8e24aa', '#00acc1',
];

type TestStatus = 'Idle' | 'Running' | 'Finished' | 'Stopped';

interface Props {
  onBack: () => void;
}

export default function Scenario3Screen({onBack}: Props): React.JSX.Element {
  const [status, setStatus] = useState<TestStatus>('Idle');
  const [measuredDurationMs, setMeasuredDurationMs] = useState<number | null>(null);
  const [jsFps, setJsFps] = useState<number | null>(null);
  const [useNativeDriver, setUseNativeDriver] = useState(false);

  const statusRef = useRef<TestStatus>('Idle');
  const measurementStartRef = useRef(0);
  const measurementTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fpsFrameCountRef = useRef(0);
  const fpsRafRef = useRef<number | null>(null);
  const fpsIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const jsDriverValues = useRef({
    x: Array.from({length: BOX_COUNT}, () => new Animated.Value(0)),
    y: Array.from({length: BOX_COUNT}, () => new Animated.Value(0)),
    scale: Array.from({length: BOX_COUNT}, () => new Animated.Value(0)),
    rot: Array.from({length: BOX_COUNT}, () => new Animated.Value(0)),
  }).current;

  const nativeDriverValues = useRef({
    x: Array.from({length: BOX_COUNT}, () => new Animated.Value(0)),
    y: Array.from({length: BOX_COUNT}, () => new Animated.Value(0)),
    scale: Array.from({length: BOX_COUNT}, () => new Animated.Value(0)),
    rot: Array.from({length: BOX_COUNT}, () => new Animated.Value(0)),
  }).current;

  // React Native Animated.Value instances should not be mixed between JS and
  // native drivers. Keep a separate value bank for each driver so the runtime
  // selector never reuses the same Animated.Value with both mechanisms.
  const activeValues = useNativeDriver ? nativeDriverValues : jsDriverValues;
  const animX = activeValues.x;
  const animY = activeValues.y;
  const animScale = activeValues.scale;
  const animRot = activeValues.rot;

  const runningAnimsRef = useRef<Animated.CompositeAnimation[]>([]);

  const stopFpsMeasurement = useCallback(() => {
    if (fpsRafRef.current !== null) {
      cancelAnimationFrame(fpsRafRef.current);
      fpsRafRef.current = null;
    }
    if (fpsIntervalRef.current !== null) {
      clearInterval(fpsIntervalRef.current);
      fpsIntervalRef.current = null;
    }
  }, []);

  const startFpsMeasurement = useCallback(() => {
    fpsFrameCountRef.current = 0;

    const countFrame = () => {
      fpsFrameCountRef.current += 1;
      fpsRafRef.current = requestAnimationFrame(countFrame);
    };

    fpsRafRef.current = requestAnimationFrame(countFrame);
    fpsIntervalRef.current = setInterval(() => {
      setJsFps(fpsFrameCountRef.current);
      fpsFrameCountRef.current = 0;
    }, 1000);
  }, []);

  const stopAnimations = useCallback(() => {
    runningAnimsRef.current.forEach(animation => animation.stop());
    runningAnimsRef.current = [];
    animX.forEach(value => value.setValue(0));
    animY.forEach(value => value.setValue(0));
    animScale.forEach(value => value.setValue(0));
    animRot.forEach(value => value.setValue(0));
  }, [animRot, animScale, animX, animY]);

  const finishTest = useCallback(
    (stoppedEarly: boolean) => {
      const duration =
        measurementStartRef.current > 0
          ? Date.now() - measurementStartRef.current
          : 0;

      if (measurementTimerRef.current !== null) {
        clearTimeout(measurementTimerRef.current);
        measurementTimerRef.current = null;
      }

      stopAnimations();
      stopFpsMeasurement();
      statusRef.current = stoppedEarly ? 'Stopped' : 'Finished';
      setStatus(stoppedEarly ? 'Stopped' : 'Finished');
      setMeasuredDurationMs(duration);
    },
    [stopAnimations, stopFpsMeasurement],
  );

  const startTest = useCallback(() => {
    stopAnimations();

    measurementStartRef.current = Date.now();
    statusRef.current = 'Running';
    setStatus('Running');
    setMeasuredDurationMs(null);
    setJsFps(null);

    const easeInOut = Easing.inOut(Easing.ease);
    const animations: Animated.CompositeAnimation[] = [];

    for (let index = 0; index < BOX_COUNT; index++) {
      const durationX = BASE_ANIM_X_MS + index * ANIM_STEP_MS;
      const durationY = BASE_ANIM_Y_MS + index * ANIM_STEP_MS;
      const durationScale = BASE_ANIM_SCALE_MS + index * ANIM_STEP_MS;
      const durationRotation = BASE_ANIM_ROT_MS + index * ANIM_STEP_MS;

      const loopX = Animated.loop(
        Animated.sequence([
          Animated.timing(animX[index], {
            toValue: 1,
            duration: durationX,
            easing: easeInOut,
            useNativeDriver,
          }),
          Animated.timing(animX[index], {
            toValue: -1,
            duration: durationX,
            easing: easeInOut,
            useNativeDriver,
          }),
        ]),
      );

      const loopY = Animated.loop(
        Animated.sequence([
          Animated.timing(animY[index], {
            toValue: 1,
            duration: durationY,
            easing: easeInOut,
            useNativeDriver,
          }),
          Animated.timing(animY[index], {
            toValue: -1,
            duration: durationY,
            easing: easeInOut,
            useNativeDriver,
          }),
        ]),
      );

      const loopScale = Animated.loop(
        Animated.sequence([
          Animated.timing(animScale[index], {
            toValue: 1,
            duration: durationScale,
            easing: easeInOut,
            useNativeDriver,
          }),
          Animated.timing(animScale[index], {
            toValue: 0,
            duration: durationScale,
            easing: easeInOut,
            useNativeDriver,
          }),
        ]),
      );

      const loopRot = Animated.loop(
        Animated.timing(animRot[index], {
          toValue: 1,
          duration: durationRotation,
          easing: Easing.linear,
          useNativeDriver,
        }),
      );

      loopX.start();
      loopY.start();
      loopScale.start();
      loopRot.start();
      animations.push(loopX, loopY, loopScale, loopRot);
    }

    runningAnimsRef.current = animations;
    startFpsMeasurement();
    measurementTimerRef.current = setTimeout(
      () => finishTest(false),
      MEASUREMENT_DURATION_MS,
    );
  }, [animRot, animScale, animX, animY, finishTest, startFpsMeasurement, stopAnimations, useNativeDriver]);

  useEffect(
    () => () => {
      if (measurementTimerRef.current !== null) {
        clearTimeout(measurementTimerRef.current);
      }
      stopAnimations();
      stopFpsMeasurement();
    },
    [stopAnimations, stopFpsMeasurement],
  );

  const isRunning = status === 'Running';

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      <Text style={styles.title}>Animations Benchmark</Text>

      <View style={styles.statusSection}>
        <Text style={styles.statusText}>
          Status: <Text style={styles.statusValue}>{status}</Text>
        </Text>
        <Text style={styles.statusText}>
          Animated Boxes: <Text style={styles.statusValue}>{BOX_COUNT}</Text>
        </Text>
        <Text style={styles.statusText}>
          Driver:{' '}
          <Text style={styles.statusValue}>
            {useNativeDriver ? 'Native-driven' : 'JS-driven'}
          </Text>
        </Text>
        {(isRunning || jsFps !== null) && (
          <Text style={styles.statusText}>
            JS FPS: <Text style={styles.statusValue}>{jsFps ?? '...'}</Text>
          </Text>
        )}
        {measuredDurationMs !== null && (
          <Text style={styles.statusText}>
            Measured Duration: <Text style={styles.statusValue}>{measuredDurationMs} ms</Text>
          </Text>
        )}
      </View>

      <View style={styles.controlsSection}>
        <View style={styles.driverSection}>
          <Text style={styles.driverLabel}>Animation driver</Text>
          <View style={styles.driverButtonRow}>
            <TouchableOpacity
              style={[
                styles.driverButton,
                !useNativeDriver && styles.driverButtonSelected,
                isRunning && styles.buttonDisabled,
              ]}
              onPress={() => setUseNativeDriver(false)}
              disabled={isRunning}
              activeOpacity={0.7}>
              <Text
                style={[
                  styles.driverButtonText,
                  !useNativeDriver && styles.driverButtonTextSelected,
                ]}>
                JS-driven
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.driverButton,
                useNativeDriver && styles.driverButtonSelected,
                isRunning && styles.buttonDisabled,
              ]}
              onPress={() => setUseNativeDriver(true)}
              disabled={isRunning}
              activeOpacity={0.7}>
              <Text
                style={[
                  styles.driverButtonText,
                  useNativeDriver && styles.driverButtonTextSelected,
                ]}>
                Native-driven
              </Text>
            </TouchableOpacity>
          </View>
        </View>
        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={[styles.button, styles.startButton, isRunning && styles.buttonDisabled]}
            onPress={startTest}
            disabled={isRunning}
            activeOpacity={0.7}>
            <Text style={styles.buttonText}>Start Test</Text>
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

      <View style={styles.grid}>
        {Array.from({length: 5}, (_, row) => (
          <View key={row} style={styles.gridRow}>
            {[0, 1, 2].map(column => {
              const index = row * 3 + column;
              const translateX = animX[index].interpolate({
                inputRange: [-1, 1],
                outputRange: [-TRANSLATE_X_RANGE, TRANSLATE_X_RANGE],
              });
              const translateY = animY[index].interpolate({
                inputRange: [-1, 1],
                outputRange: [-TRANSLATE_Y_RANGE, TRANSLATE_Y_RANGE],
              });
              const scale = animScale[index].interpolate({
                inputRange: [0, 1],
                outputRange: [1, 1.5],
              });
              const rotate = animRot[index].interpolate({
                inputRange: [0, 1],
                outputRange: ['0deg', '360deg'],
              });

              return (
                <Animated.View
                  key={index}
                  style={[
                    styles.box,
                    {backgroundColor: BOX_COLORS[index % BOX_COLORS.length]},
                    {transform: [{translateX}, {translateY}, {scale}, {rotate}]},
                  ]}
                />
              );
            })}
          </View>
        ))}
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
  driverSection: {
    gap: 6,
  },
  driverLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#555555',
  },
  driverButtonRow: {
    flexDirection: 'row',
    gap: 10,
  },
  driverButton: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#cfd8dc',
    backgroundColor: '#ffffff',
    alignItems: 'center',
  },
  driverButtonSelected: {
    borderColor: '#1a1a2e',
    backgroundColor: '#1a1a2e',
  },
  driverButtonText: {
    color: '#455a64',
    fontSize: 12,
    fontWeight: '600',
  },
  driverButtonTextSelected: {
    color: '#ffffff',
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
  grid: {
    flex: 1,
    justifyContent: 'space-evenly',
    paddingVertical: 16,
    paddingHorizontal: 24,
    overflow: 'visible',
  },
  gridRow: {
    flexDirection: 'row',
    justifyContent: 'space-evenly',
    alignItems: 'center',
    overflow: 'visible',
  },
  box: {
    width: 56,
    height: 56,
    borderRadius: 8,
  },
});
