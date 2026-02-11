import { useEffect } from 'preact/hooks';
import Router from 'preact-router';
import { connectWebSocket, disconnectWebSocket } from './store.js';
import Sidebar from './components/Sidebar.jsx';
import Home from './pages/Home.jsx';
import Discovery from './pages/Discovery.jsx';
import Capabilities from './pages/Capabilities.jsx';
import Predictions from './pages/Predictions.jsx';
import Patterns from './pages/Patterns.jsx';
import Automations from './pages/Automations.jsx';

/**
 * Custom hash-based history for preact-router.
 * Converts hash URLs (#/path) into the pathname-based API that preact-router expects.
 */
function createHashHistory() {
  const listeners = [];

  function getLocation() {
    const hash = window.location.hash || '#/';
    const path = hash.replace(/^#/, '') || '/';
    const qIdx = path.indexOf('?');
    return {
      pathname: qIdx >= 0 ? path.slice(0, qIdx) : path,
      search: qIdx >= 0 ? path.slice(qIdx) : '',
    };
  }

  function notify() {
    const location = getLocation();
    listeners.forEach((cb) => cb({ location }));
  }

  window.addEventListener('hashchange', notify);

  return {
    location: getLocation(),
    listen(callback) {
      listeners.push(callback);
      return () => {
        const idx = listeners.indexOf(callback);
        if (idx >= 0) listeners.splice(idx, 1);
      };
    },
    push(path) {
      window.location.hash = '#' + path;
    },
    replace(path) {
      const url = window.location.pathname + window.location.search + '#' + path;
      window.history.replaceState(null, '', url);
      notify();
    },
  };
}

const hashHistory = createHashHistory();

export default function App() {
  useEffect(() => {
    connectWebSocket();
    return () => disconnectWebSocket();
  }, []);

  // Ensure hash has a default route
  if (!window.location.hash) {
    window.location.hash = '#/';
  }

  return (
    <div class="min-h-screen bg-gray-50">
      <Sidebar />

      {/* Content area: offset for sidebar on desktop, bottom padding for tab bar on mobile */}
      <main class="md:ml-60 pb-16 md:pb-0 min-h-screen">
        <div class="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <Router history={hashHistory}>
            <Home path="/" />
            <Discovery path="/discovery" />
            <Capabilities path="/capabilities" />
            <Predictions path="/predictions" />
            <Patterns path="/patterns" />
            <Automations path="/automations" />
          </Router>
        </div>
      </main>
    </div>
  );
}
