import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
} from 'react-native';

type Screen = 'Scenario1' | 'Scenario2' | 'Scenario3' | 'Scenario4';

interface Props {
  onNavigate: (screen: Screen) => void;
}

export default function HomeScreen({onNavigate}: Props): React.JSX.Element {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      <Text style={styles.title}>Benchmark App</Text>
      <View style={styles.menu}>
        <TouchableOpacity
          style={styles.menuButton}
          onPress={() => onNavigate('Scenario1')}
          activeOpacity={0.7}>
          <Text style={styles.menuButtonText}>Scenario 1: Real-Time Updates</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.menuButton}
          onPress={() => onNavigate('Scenario2')}
          activeOpacity={0.7}>
          <Text style={styles.menuButtonText}>Scenario 2: Large List Scroll</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.menuButton}
          onPress={() => onNavigate('Scenario3')}
          activeOpacity={0.7}>
          <Text style={styles.menuButtonText}>Scenario 3: Animations</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.menuButton}
          onPress={() => onNavigate('Scenario4')}
          activeOpacity={0.7}>
          <Text style={styles.menuButtonText}>Scenario 4: JS-Native Communication</Text>
        </TouchableOpacity>
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
    fontSize: 20,
    fontWeight: '700',
    textAlign: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
    backgroundColor: '#1a1a2e',
    color: '#ffffff',
    letterSpacing: 0.5,
  },
  menu: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    gap: 16,
  },
  menuButton: {
    backgroundColor: '#1a1a2e',
    paddingVertical: 16,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
  },
  menuButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
  },
});
