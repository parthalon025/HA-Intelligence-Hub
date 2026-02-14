import { useState } from 'preact/hooks';
import useCache from '../hooks/useCache.js';
import useComputed from '../hooks/useComputed.js';
import { putJson } from '../api.js';
import HeroCard from '../components/HeroCard.jsx';
import PageBanner from '../components/PageBanner.jsx';
import CollapsibleSection from '../components/CollapsibleSection.jsx';
import LoadingState from '../components/LoadingState.jsx';
import ErrorState from '../components/ErrorState.jsx';
import UsefulnessBar from '../components/UsefulnessBar.jsx';
import CapabilityDetail from '../components/CapabilityDetail.jsx';

/** Humanize a snake_case name: "power_monitoring" -> "Power monitoring" */
function humanize(name) {
  const spaced = (name || '').replace(/_/g, ' ');
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

/** Known capability detail fields (not entity lists or metadata). */
const DETAIL_FIELDS = new Set([
  'supports_color', 'supports_brightness', 'supports_color_temp',
  'measurement_unit', 'modes',
]);

/**
 * Plain-language explanations for each capability's predictability.
 * Shown when the user toggles or hovers — helps non-technical users
 * understand what "can predict" means for their specific devices.
 */
const PREDICT_EXPLANATIONS = {
  power_monitoring: {
    why: 'Power usage follows daily patterns — morning coffee, evening TV, overnight baseline. ARIA learns your typical wattage curves and flags unusual spikes or drops.',
    on: 'ARIA will predict your expected power draw and alert when it deviates.',
    off: 'Power predictions disabled. ARIA will still track power but won\'t flag anomalies.',
  },
  lighting: {
    why: 'Lights follow routines — on at sunset, off at bedtime. ARIA learns which lights are typically on at what time of day.',
    on: 'ARIA will predict which lights should be on and notice unexpected changes.',
    off: 'Light predictions disabled. ARIA will still count lights but won\'t predict patterns.',
  },
  occupancy: {
    why: 'Presence follows your schedule — leave for work, come home in the evening. ARIA learns your typical comings and goings.',
    on: 'ARIA will predict when you\'re likely home and notice unexpected absences or arrivals.',
    off: 'Occupancy predictions disabled. ARIA will still track presence but won\'t predict it.',
  },
  climate: {
    why: 'Thermostats follow schedules and seasons. ARIA learns your comfort patterns and heating/cooling cycles.',
    on: 'ARIA will predict temperature trends and notice when climate behavior changes.',
    off: 'Climate predictions disabled. ARIA will still monitor temperature data.',
  },
  battery_devices: {
    why: 'Batteries drain predictably — sensors last weeks, tablets last hours. ARIA learns each device\'s discharge curve.',
    on: 'ARIA will predict when batteries need charging and flag unusual drain.',
    off: 'Battery predictions disabled. Levels are still tracked.',
  },
  motion: {
    why: 'Motion sensors are inherently reactive — they fire when someone walks by. Individual triggers are hard to predict, but daily patterns (busy mornings, quiet nights) can be learned.',
    on: 'ARIA will learn your typical motion patterns and flag unusual quiet or busy periods.',
    off: 'Motion predictions off. This is the default because individual motion events are noisy.',
  },
  doors_windows: {
    why: 'Door and window sensors track openings. Some follow routines (garage door at 8am), others are random (bathroom door). Predictions work best when you have consistent habits.',
    on: 'ARIA will learn your door/window patterns and notice unusual activity.',
    off: 'Door/window predictions off. This is the default because contact events vary widely.',
  },
  locks: {
    why: 'Smart locks often follow routines — lock at bedtime, unlock in the morning. If your lock usage is consistent, predictions can spot when something breaks the pattern.',
    on: 'ARIA will learn your locking patterns and notice when they change.',
    off: 'Lock predictions off. This is the default because lock events are security-sensitive.',
  },
  media: {
    why: 'Media playback depends on mood, not schedule. But if you have routines (morning news, bedtime podcast), ARIA can learn those patterns.',
    on: 'ARIA will learn your media habits and predict typical playback times.',
    off: 'Media predictions off. This is the default because playback is usually on-demand.',
  },
  vacuum: {
    why: 'Robot vacuums usually run on their own schedule, set in the robot\'s app. ARIA can learn when cleaning typically happens.',
    on: 'ARIA will learn your vacuum schedule and notice missed or extra runs.',
    off: 'Vacuum predictions off. Most vacuums have their own scheduling.',
  },
};

const DEFAULT_EXPLANATION = {
  why: 'ARIA can attempt to learn patterns for this capability based on your historical data.',
  on: 'Predictions enabled — ARIA will look for patterns.',
  off: 'Predictions disabled — ARIA will still track data but won\'t predict.',
};

function PredictToggle({ name, canPredict, onToggle }) {
  const [busy, setBusy] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const explain = PREDICT_EXPLANATIONS[name] || DEFAULT_EXPLANATION;

  async function handleToggle() {
    setBusy(true);
    try {
      await onToggle(name, !canPredict);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="text-sm font-medium" style="color: var(--text-secondary)">Predictions</span>
          <button
            onClick={() => setShowHelp(!showHelp)}
            class="text-xs cursor-pointer"
            style="color: var(--accent); background: none; border: none; padding: 0;"
            title="Why?"
          >
            {showHelp ? 'hide' : 'why?'}
          </button>
        </div>
        <button
          onClick={handleToggle}
          disabled={busy}
          class="relative inline-flex items-center h-6 w-11 rounded-full cursor-pointer transition-colors"
          style={`background: ${canPredict ? 'var(--accent)' : 'var(--bg-inset)'}; border: 2px solid ${canPredict ? 'var(--accent)' : 'var(--border-subtle)'}; opacity: ${busy ? '0.5' : '1'};`}
          title={canPredict ? 'Click to disable predictions' : 'Click to enable predictions'}
        >
          <span
            class="inline-block h-4 w-4 rounded-full transition-transform"
            style={`background: ${canPredict ? 'var(--bg-base)' : 'var(--text-tertiary)'}; transform: translateX(${canPredict ? '20px' : '2px'});`}
          />
        </button>
      </div>

      <p class="text-xs" style={`color: ${canPredict ? 'var(--status-healthy)' : 'var(--text-tertiary)'}`}>
        {canPredict ? explain.on : explain.off}
      </p>

      {showHelp && (
        <div class="t-callout p-2 text-xs" style="color: var(--text-secondary); line-height: 1.5;">
          {explain.why}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// CapabilityCard — single capability in the grid
// ---------------------------------------------------------------------------

function CapabilityCard({ name, capability, onTogglePredict, onAction }) {
  const [expanded, setExpanded] = useState(false);

  const entities = capability.entities || [];
  const entityCount = capability.entity_count || entities.length;
  const canPredict = capability.can_predict ?? false;
  const usefulness = capability.usefulness ?? null;
  const source = capability.source || null; // 'seed' | 'organic'
  const layer = capability.layer || null;   // 'domain' | 'behavioral'
  const status = capability.status || 'promoted';
  const stabilityStreak = capability.stability_streak ?? null;

  return (
    <div
      class="t-frame"
      data-label={humanize(name)}
      style="padding: 1rem; cursor: pointer;"
      onClick={() => setExpanded(!expanded)}
    >
      {/* Header row: name + badges */}
      <div class="flex items-center justify-between mb-2" style="flex-wrap: wrap; gap: 4px;">
        <h3
          class="text-base font-bold"
          style="color: var(--text-primary); margin: 0;"
        >
          {humanize(name)}
        </h3>
        <div class="flex items-center gap-1" style="flex-wrap: wrap;">
          {/* Entity count badge */}
          <span
            class="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
            style="background: var(--accent-glow); color: var(--accent); white-space: nowrap;"
          >
            {entityCount} {entityCount === 1 ? 'entity' : 'entities'}
          </span>

          {/* Source badge */}
          {source && (
            <span
              class="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
              style={`white-space: nowrap; ${
                source === 'organic'
                  ? 'background: var(--status-healthy-glow); color: var(--status-healthy);'
                  : 'background: var(--bg-surface-raised); color: var(--text-tertiary);'
              }`}
            >
              {source}
            </span>
          )}

          {/* Layer badge */}
          {layer && (
            <span
              class="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
              style={`white-space: nowrap; ${
                layer === 'behavioral'
                  ? 'background: color-mix(in srgb, var(--accent-purple) 15%, transparent); color: var(--accent-purple);'
                  : 'background: var(--bg-surface-raised); color: var(--text-secondary);'
              }`}
            >
              {layer}
            </span>
          )}
        </div>
      </div>

      {/* Usefulness bar */}
      {usefulness != null && (
        <div style="margin-bottom: 8px;">
          <UsefulnessBar value={usefulness} label="Usefulness" />
        </div>
      )}

      {/* Stability streak for candidates */}
      {status === 'candidate' && stabilityStreak != null && (
        <div
          style="font-size: var(--type-label); color: var(--text-tertiary); font-family: var(--font-mono); margin-bottom: 8px;"
        >
          Stability streak: <span style={`color: ${stabilityStreak >= 7 ? 'var(--status-healthy)' : 'var(--text-secondary)'};`}>{stabilityStreak}d</span>
        </div>
      )}

      {/* Prediction toggle — only for promoted capabilities */}
      {status === 'promoted' && (
        <div
          class="mb-2 pb-2"
          style="border-bottom: 1px solid var(--border-subtle);"
          onClick={(e) => e.stopPropagation()}
        >
          <PredictToggle name={name} canPredict={canPredict} onToggle={onTogglePredict} />
        </div>
      )}

      {/* Expanded detail view */}
      {expanded && (
        <div onClick={(e) => e.stopPropagation()}>
          <CapabilityDetail name={name} capability={capability} onAction={onAction} />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Discovery status bar
// ---------------------------------------------------------------------------

function DiscoveryStatus({ data }) {
  if (!data) return null;

  const meta = data.discovery_metadata || data.metadata || {};
  const lastRun = meta.last_organic_run || meta.last_run || null;
  const autonomyMode = meta.autonomy_mode || null;
  const namingBackend = meta.naming_backend || null;

  if (!lastRun && !autonomyMode && !namingBackend) return null;

  return (
    <div
      class="t-frame"
      data-label="Discovery"
      style="padding: 0.75rem;"
    >
      <div class="flex items-center gap-4" style="flex-wrap: wrap; font-size: var(--type-label); font-family: var(--font-mono);">
        {lastRun && (
          <span style="color: var(--text-secondary);">
            Last run: <span style="color: var(--text-primary);">{formatTimestamp(lastRun)}</span>
          </span>
        )}
        {autonomyMode && (
          <span style="color: var(--text-secondary);">
            Mode: <span style="color: var(--accent);">{autonomyMode}</span>
          </span>
        )}
        {namingBackend && (
          <span style="color: var(--text-secondary);">
            Naming: <span style="color: var(--text-primary);">{namingBackend}</span>
          </span>
        )}
      </div>
    </div>
  );
}

function formatTimestamp(iso) {
  if (!iso) return '\u2014';
  try {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now - d;
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return iso;
  }
}

// ---------------------------------------------------------------------------
// Main Capabilities page
// ---------------------------------------------------------------------------

export default function Capabilities() {
  const { data, loading, error, refetch } = useCache('capabilities');

  const capabilities = useComputed(() => {
    if (!data || !data.data) return [];
    const inner = data.data;
    return Object.entries(inner).map(([name, cap]) => ({ name, ...cap }));
  }, [data]);

  // Split into status groups
  const promoted = useComputed(() => {
    return capabilities.filter((c) => c.status === 'promoted' || !c.status);
  }, [capabilities]);

  const candidates = useComputed(() => {
    return capabilities.filter((c) => c.status === 'candidate');
  }, [capabilities]);

  const archived = useComputed(() => {
    return capabilities.filter((c) => c.status === 'archived');
  }, [capabilities]);

  // Total entity count across all capabilities
  const totalEntities = useComputed(() => {
    return capabilities.reduce((sum, cap) => sum + (cap.entity_count || (cap.entities || []).length), 0);
  }, [capabilities]);

  async function handleTogglePredict(capName, newValue) {
    try {
      await putJson(`/api/capabilities/${capName}/can-predict`, { can_predict: newValue });
      refetch();
    } catch (err) {
      console.error('Failed to toggle can_predict:', err);
    }
  }

  function handleAction() {
    refetch();
  }

  const heroDelta = `${promoted.length} promoted \u00B7 ${candidates.length} candidate${candidates.length !== 1 ? 's' : ''} \u00B7 ${totalEntities} entities`;

  if (loading && !data) {
    return (
      <div class="space-y-6">
        <PageBanner page="CAPABILITIES" subtitle="Detected home capabilities and features." />
        <LoadingState type="cards" />
      </div>
    );
  }

  if (error) {
    return (
      <div class="space-y-6">
        <PageBanner page="CAPABILITIES" subtitle="Detected home capabilities and features." />
        <ErrorState error={error} onRetry={refetch} />
      </div>
    );
  }

  return (
    <div class="space-y-6 animate-page-enter">
      <PageBanner page="CAPABILITIES" subtitle="Detected home capabilities and features." />

      {/* Hero — total capabilities */}
      <HeroCard
        value={capabilities.length}
        label="capabilities"
        delta={heroDelta}
        loading={loading}
      />

      {/* Discovery status bar */}
      <DiscoveryStatus data={data} />

      {/* Explanation */}
      <div class="t-callout p-3 text-sm" style="color: var(--text-secondary); line-height: 1.5;">
        ARIA automatically detects what your home can do by scanning your entities.
        Each capability can be toggled for <strong style="color: var(--text-primary)">predictions</strong> — when enabled, ARIA learns
        the patterns for that capability and flags when something changes. Organic discovery
        finds new groupings automatically; candidates are promoted once they prove stable.
      </div>

      {capabilities.length === 0 ? (
        <div class="t-callout" style="padding: 0.75rem;">
          <span class="text-sm" style="color: var(--text-secondary)">
            No capabilities detected yet. Capabilities are identified during discovery by matching
            entity domains and device classes. They appear after the first successful discovery scan.
          </span>
        </div>
      ) : (
        <div class="space-y-6">
          {/* Promoted section */}
          {promoted.length > 0 && (
            <CollapsibleSection
              title="Promoted"
              subtitle="Active capabilities tracked by ARIA."
              summary={`${promoted.length} capabilities`}
              defaultOpen={true}
              loading={loading}
            >
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 stagger-children">
                {promoted.map((cap) => (
                  <CapabilityCard
                    key={cap.name}
                    name={cap.name}
                    capability={cap}
                    onTogglePredict={handleTogglePredict}
                    onAction={handleAction}
                  />
                ))}
              </div>
            </CollapsibleSection>
          )}

          {/* Candidates section */}
          {candidates.length > 0 && (
            <CollapsibleSection
              title="Candidates"
              subtitle="Organically discovered capabilities awaiting promotion."
              summary={`${candidates.length} candidates`}
              defaultOpen={true}
              loading={loading}
            >
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 stagger-children">
                {candidates.map((cap) => (
                  <CapabilityCard
                    key={cap.name}
                    name={cap.name}
                    capability={cap}
                    onTogglePredict={handleTogglePredict}
                    onAction={handleAction}
                  />
                ))}
              </div>
            </CollapsibleSection>
          )}

          {/* Archived section */}
          {archived.length > 0 && (
            <CollapsibleSection
              title="Archived"
              subtitle="Capabilities removed from active tracking."
              summary={`${archived.length} archived`}
              defaultOpen={false}
              loading={loading}
            >
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 stagger-children">
                {archived.map((cap) => (
                  <CapabilityCard
                    key={cap.name}
                    name={cap.name}
                    capability={cap}
                    onTogglePredict={handleTogglePredict}
                    onAction={handleAction}
                  />
                ))}
              </div>
            </CollapsibleSection>
          )}
        </div>
      )}
    </div>
  );
}
