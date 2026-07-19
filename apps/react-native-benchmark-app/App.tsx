import React, {useState} from 'react';
import HomeScreen from './screens/HomeScreen';
import Scenario1Screen from './screens/Scenario1Screen';
import Scenario2Screen from './screens/Scenario2Screen';
import Scenario3Screen from './screens/Scenario3Screen';
import Scenario4Screen from './screens/Scenario4Screen';

type Screen = 'Home' | 'Scenario1' | 'Scenario2' | 'Scenario3' | 'Scenario4';

export default function App(): React.JSX.Element {
  const [screen, setScreen] = useState<Screen>('Home');

  switch (screen) {
    case 'Scenario1':
      return <Scenario1Screen onBack={() => setScreen('Home')} />;
    case 'Scenario2':
      return <Scenario2Screen onBack={() => setScreen('Home')} />;
    case 'Scenario3':
      return <Scenario3Screen onBack={() => setScreen('Home')} />;
    case 'Scenario4':
      return <Scenario4Screen onBack={() => setScreen('Home')} />;
    default:
      return <HomeScreen onNavigate={setScreen} />;
  }
}
