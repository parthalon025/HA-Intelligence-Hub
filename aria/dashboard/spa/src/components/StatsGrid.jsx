/**
 * Responsive stats grid.
 * @param {{ items: Array<{ label: string, value: string|number, warning?: boolean }> }} props
 */
export default function StatsGrid({ items }) {
  if (!items || items.length === 0) return null;

  return (
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      {items.map((item, i) => (
        <div
          key={i}
          class="t-card"
          style={`padding: 16px;${item.warning ? ' border-color: var(--status-warning); border-width: 2px;' : ''}`}
        >
          <div
            class="data-mono"
            style={`font-size: 1.5rem; font-weight: 700; color: ${item.warning ? 'var(--status-warning)' : 'var(--accent)'};`}
          >
            {item.value}
          </div>
          <div style="font-size: 0.875rem; color: var(--text-tertiary); margin-top: 4px;">{item.label}</div>
        </div>
      ))}
    </div>
  );
}
