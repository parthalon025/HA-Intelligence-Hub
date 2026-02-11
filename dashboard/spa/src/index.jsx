import { render } from 'preact';
import { useEffect } from 'preact/hooks';
import { connectWebSocket, fetchCategory, getCategory, wsConnected, wsMessage } from './store.js';

function App() {
  // Connect WebSocket on mount
  useEffect(() => {
    connectWebSocket();
    // Kick off an initial fetch to prove the data layer works
    fetchCategory('entities');
  }, []);

  const entities = getCategory('entities');
  const state = entities.value;

  return (
    <div class="p-4 text-white">
      <h1 class="text-xl font-bold mb-4">HA Intelligence Hub</h1>

      <div class="mb-2 text-sm">
        <span class={wsConnected.value ? 'text-green-400' : 'text-red-400'}>
          WS: {wsMessage.value || (wsConnected.value ? 'connected' : 'disconnected')}
        </span>
      </div>

      <div class="text-sm text-gray-400">
        {state.loading && <p>Loading entities...</p>}
        {state.error && <p class="text-red-400">Error: {state.error}</p>}
        {state.data && <p>Entities cache loaded ({JSON.stringify(Object.keys(state.data)).slice(0, 120)}...)</p>}
        {state.stale && <p class="text-yellow-400">Stale — refreshing...</p>}
      </div>
    </div>
  );
}

render(<App />, document.getElementById('app'));
