/**
 * Horizontal bar chart for domain breakdown, pure CSS with theme tokens.
 *
 * @param {{ data: Array<{ domain: string, count: number }>, total: number }} props
 */
export default function DomainChart({ data, total }) {
  if (!data || data.length === 0) return null;

  const maxCount = data[0]?.count || 1;

  return (
    <div class="space-y-2">
      {data.map((item) => {
        const pct = total > 0 ? ((item.count / total) * 100).toFixed(1) : 0;
        const barWidth = maxCount > 0 ? (item.count / maxCount) * 100 : 0;

        return (
          <div key={item.domain} class="flex items-center gap-2">
            <span class="w-28 text-sm text-right truncate" style="color: var(--text-secondary);" title={item.domain}>
              {item.domain}
            </span>
            <div class="flex-1 h-6 overflow-hidden" style="background: var(--bg-inset); border-radius: var(--radius);">
              <div
                class="h-full transition-all"
                style={`background: var(--accent); border-radius: var(--radius); width: ${barWidth}%;`}
              />
            </div>
            <span class="w-20 text-sm data-mono" style="color: var(--text-tertiary);">
              {item.count} ({pct}%)
            </span>
          </div>
        );
      })}
    </div>
  );
}
