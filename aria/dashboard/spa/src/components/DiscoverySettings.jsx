import { useState, useEffect } from 'preact/hooks';
import { fetchJson, putJson, postJson } from '../api.js';

const AUTONOMY_MODES = [
  {
    value: 'suggest_and_wait',
    label: 'Suggest & Wait',
    description: 'Show candidates, you promote manually',
  },
  {
    value: 'auto_promote',
    label: 'Auto-Promote',
    description: 'Promote when usefulness stays above threshold',
  },
  {
    value: 'autonomous',
    label: 'Autonomous',
    description: 'ARIA manages promotion and archival',
  },
];

const NAMING_BACKENDS = [
  {
    value: 'heuristic',
    label: 'Heuristic',
    pro: 'Free, instant, deterministic',
    con: 'Generic names',
  },
  {
    value: 'ollama',
    label: 'Ollama',
    pro: 'Natural language names',
    con: '+45min Ollama slot per run',
  },
  {
    value: 'external_llm',
    label: 'External LLM',
    pro: 'Best quality names',
    con: 'API cost per run',
  },
];

export default function DiscoverySettings({ onClose }) {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);
  const [runMsg, setRunMsg] = useState(null);

  useEffect(() => {
    fetchJson('/api/settings/discovery')
      .then((data) => {
        setSettings(data);
        setError(null);
      })
      .catch((err) => setError(err.message || String(err)))
      .finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    setSaving(true);
    setSaveMsg(null);
    try {
      await putJson('/api/settings/discovery', settings);
      setSaveMsg('Saved');
      setTimeout(() => setSaveMsg(null), 2000);
    } catch (err) {
      setSaveMsg(`Error: ${err.message}`);
    } finally {
      setSaving(false);
    }
  }

  async function handleRun() {
    setRunning(true);
    setRunMsg(null);
    try {
      await postJson('/api/discovery/run', {});
      setRunMsg('Discovery run started');
      setTimeout(() => setRunMsg(null), 3000);
    } catch (err) {
      setRunMsg(`Error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  }

  function updateField(key, value) {
    setSettings((prev) => ({ ...prev, [key]: value }));
  }

  if (loading) {
    return (
      <div class="t-frame" data-label="Discovery Settings">
        <div style="padding: 24px; text-align: center;">
          <span style="color: var(--text-tertiary); font-family: var(--font-mono); font-size: var(--type-label);">
            Loading settings...
          </span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div class="t-frame" data-label="Discovery Settings">
        <div style="padding: 24px; text-align: center;">
          <span style="color: var(--status-error); font-family: var(--font-mono); font-size: var(--type-label);">
            {error}
          </span>
        </div>
      </div>
    );
  }

  if (!settings) return null;

  return (
    <div class="t-frame" data-label="Discovery Settings">
      <div style="padding: 16px; display: flex; flex-direction: column; gap: 24px;">

        {/* Autonomy Mode */}
        <fieldset style="border: none; margin: 0; padding: 0;">
          <legend
            style="font-family: var(--font-mono); font-size: var(--type-body); font-weight: 700; color: var(--text-primary); margin-bottom: 8px;"
          >
            Autonomy Mode
          </legend>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            {AUTONOMY_MODES.map((mode) => (
              <label
                key={mode.value}
                style={`
                  display: flex; align-items: flex-start; gap: 8px; padding: 8px 12px;
                  border-radius: var(--radius); cursor: pointer;
                  background: ${settings.autonomy_mode === mode.value ? 'var(--bg-inset)' : 'transparent'};
                  border: 1px solid ${settings.autonomy_mode === mode.value ? 'var(--accent)' : 'var(--border-subtle)'};
                `}
              >
                <input
                  type="radio"
                  name="autonomy_mode"
                  value={mode.value}
                  checked={settings.autonomy_mode === mode.value}
                  onChange={() => updateField('autonomy_mode', mode.value)}
                  style="accent-color: var(--accent); margin-top: 2px; flex-shrink: 0;"
                />
                <div>
                  <span style="font-family: var(--font-mono); font-size: var(--type-body); color: var(--text-primary); font-weight: 600;">
                    {mode.label}
                  </span>
                  <p style="font-family: var(--font-mono); font-size: var(--type-label); color: var(--text-secondary); margin: 2px 0 0;">
                    {mode.description}
                  </p>
                </div>
              </label>
            ))}
          </div>

          {/* Auto-promote threshold inputs */}
          {settings.autonomy_mode === 'auto_promote' && (
            <div
              style="margin-top: 12px; margin-left: 28px; padding: 12px; background: var(--bg-inset); border-radius: var(--radius); border: 1px solid var(--border-subtle);"
            >
              <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                <span style="font-family: var(--font-mono); font-size: var(--type-label); color: var(--text-secondary);">
                  Promote at
                </span>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={settings.promote_threshold ?? 50}
                  onInput={(e) => updateField('promote_threshold', Number(e.target.value))}
                  style="width: 60px; padding: 4px 8px; font-family: var(--font-mono); font-size: var(--type-body); background: var(--bg-inset); border: 1px solid var(--border-subtle); border-radius: var(--radius); color: var(--text-primary);"
                />
                <span style="font-family: var(--font-mono); font-size: var(--type-label); color: var(--text-secondary);">
                  % for
                </span>
                <input
                  type="number"
                  min="1"
                  max="90"
                  value={settings.promote_days ?? 7}
                  onInput={(e) => updateField('promote_days', Number(e.target.value))}
                  style="width: 60px; padding: 4px 8px; font-family: var(--font-mono); font-size: var(--type-body); background: var(--bg-inset); border: 1px solid var(--border-subtle); border-radius: var(--radius); color: var(--text-primary);"
                />
                <span style="font-family: var(--font-mono); font-size: var(--type-label); color: var(--text-secondary);">
                  days
                </span>
              </div>
            </div>
          )}
        </fieldset>

        {/* Naming Backend */}
        <fieldset style="border: none; margin: 0; padding: 0;">
          <legend
            style="font-family: var(--font-mono); font-size: var(--type-body); font-weight: 700; color: var(--text-primary); margin-bottom: 8px;"
          >
            Naming Backend
          </legend>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            {NAMING_BACKENDS.map((backend) => (
              <label
                key={backend.value}
                style={`
                  display: flex; align-items: flex-start; gap: 8px; padding: 8px 12px;
                  border-radius: var(--radius); cursor: pointer;
                  background: ${settings.naming_backend === backend.value ? 'var(--bg-inset)' : 'transparent'};
                  border: 1px solid ${settings.naming_backend === backend.value ? 'var(--accent)' : 'var(--border-subtle)'};
                `}
              >
                <input
                  type="radio"
                  name="naming_backend"
                  value={backend.value}
                  checked={settings.naming_backend === backend.value}
                  onChange={() => updateField('naming_backend', backend.value)}
                  style="accent-color: var(--accent); margin-top: 2px; flex-shrink: 0;"
                />
                <div>
                  <span style="font-family: var(--font-mono); font-size: var(--type-body); color: var(--text-primary); font-weight: 600;">
                    {backend.label}
                  </span>
                  <div style="display: flex; gap: 12px; margin-top: 2px; flex-wrap: wrap;">
                    <span style="font-family: var(--font-mono); font-size: var(--type-label); color: var(--status-healthy);">
                      + {backend.pro}
                    </span>
                    <span style="font-family: var(--font-mono); font-size: var(--type-label); color: var(--status-warning);">
                      - {backend.con}
                    </span>
                  </div>
                </div>
              </label>
            ))}
          </div>
        </fieldset>

        {/* Status messages */}
        {(saveMsg || runMsg) && (
          <div style="font-family: var(--font-mono); font-size: var(--type-label);">
            {saveMsg && (
              <span style={`color: ${saveMsg.startsWith('Error') ? 'var(--status-error)' : 'var(--status-healthy)'};`}>
                {saveMsg}
              </span>
            )}
            {saveMsg && runMsg && <span style="margin: 0 8px; color: var(--text-tertiary);">|</span>}
            {runMsg && (
              <span style={`color: ${runMsg.startsWith('Error') ? 'var(--status-error)' : 'var(--status-healthy)'};`}>
                {runMsg}
              </span>
            )}
          </div>
        )}

        {/* Action buttons */}
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <button
            onClick={handleSave}
            disabled={saving}
            style="padding: 6px 16px; border: none; border-radius: var(--radius); font-family: var(--font-mono); font-size: var(--type-label); font-weight: 600; cursor: pointer; background: var(--accent); color: var(--bg-base);"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
          <button
            onClick={handleRun}
            disabled={running}
            style="padding: 6px 16px; border: none; border-radius: var(--radius); font-family: var(--font-mono); font-size: var(--type-label); font-weight: 600; cursor: pointer; background: var(--bg-inset); color: var(--text-secondary);"
          >
            {running ? 'Running...' : 'Run Now'}
          </button>
          {onClose && (
            <button
              onClick={onClose}
              style="padding: 6px 16px; border: none; border-radius: var(--radius); font-family: var(--font-mono); font-size: var(--type-label); font-weight: 600; cursor: pointer; background: var(--bg-inset); color: var(--text-secondary);"
            >
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
