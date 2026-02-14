/**
 * UsefulnessBar — horizontal percentage bar for capability usefulness.
 *
 * Color thresholds:
 *   >= 70  → --status-healthy (green)
 *   >= 40  → --status-warning (orange)
 *   < 40   → --status-error (red)
 *
 * @param {Object} props
 * @param {number} props.value - Percentage 0-100
 * @param {string} props.label - Bar label text
 * @param {string} [props.sublabel] - Secondary label (right-aligned)
 */
export default function UsefulnessBar({ value, label, sublabel }) {
  const pct = Math.max(0, Math.min(100, value || 0));
  const color =
    pct >= 70
      ? 'var(--status-healthy)'
      : pct >= 40
        ? 'var(--status-warning)'
        : 'var(--status-error)';

  return (
    <div class="space-y-1">
      <div class="flex items-center justify-between">
        <span
          style="font-size: var(--type-label); color: var(--text-secondary); font-family: var(--font-mono);"
        >
          {label}
        </span>
        <span
          style="font-size: var(--type-label); font-family: var(--font-mono);"
        >
          {sublabel && (
            <span style="color: var(--text-tertiary); margin-right: 6px;">{sublabel}</span>
          )}
          <span style={`color: ${color};`}>{Math.round(pct)}%</span>
        </span>
      </div>
      <div
        style="height: 6px; border-radius: 3px; background: var(--bg-inset); overflow: hidden;"
      >
        <div
          style={`height: 100%; width: ${pct}%; background: ${color}; border-radius: 3px; transition: width 0.3s ease;`}
        />
      </div>
    </div>
  );
}
