import { Section, Callout } from './utils.jsx';

export function ShapAttributions({ shap }) {
  if (!shap || !shap.available) {
    return (
      <Section
        title="Feature Attributions (SHAP)"
        subtitle="SHAP values explain WHY ARIA made a prediction. Each bar shows how much a feature pushed the prediction up or down. Longer bars = more influence."
      >
        <Callout>SHAP attributions require trained ML models. They'll appear after the first training cycle.</Callout>
      </Section>
    );
  }

  const attributions = shap.attributions || [];
  const maxContrib = Math.max(...attributions.map(a => Math.abs(a.contribution)), 0.001);

  return (
    <Section
      title="Feature Attributions (SHAP)"
      subtitle="SHAP values explain WHY ARIA made a prediction. Each bar shows how much a feature pushed the prediction up or down. Longer bars = more influence."
      summary={shap.model_type || 'active'}
    >
      <div class="space-y-3">
        {/* Model badge */}
        {shap.model_type && (
          <div>
            <span class="text-xs font-medium rounded-full px-2.5 py-0.5"
              style="background: var(--accent-glow); color: var(--accent)">
              {shap.model_type}
            </span>
          </div>
        )}

        {/* Bar chart */}
        {attributions.length > 0 ? (
          <div class="t-frame p-4" data-label="attributions">
            <div class="space-y-1">
              {attributions.map((a, i) => (
                <div key={i} class="flex items-center gap-2" style="height: 24px;">
                  <span class="text-xs w-32 text-right truncate" style="color: var(--text-secondary); flex-shrink: 0;">
                    {a.feature.replace(/_/g, ' ')}
                  </span>
                  <div class="flex-1 flex items-center" style="position: relative; min-width: 0;">
                    {/* Center line */}
                    <div style="position: absolute; left: 50%; width: 1px; height: 100%; background: var(--border-subtle);" />
                    {/* Bar */}
                    <div style={`
                      position: absolute;
                      ${a.direction === 'positive' ? 'left: 50%' : 'right: 50%'};
                      width: ${Math.abs(a.contribution) / maxContrib * 50}%;
                      height: 16px;
                      background: ${a.direction === 'positive' ? 'var(--accent)' : 'var(--accent-purple)'};
                      opacity: 0.7;
                      border-radius: 2px;
                    `} />
                  </div>
                  <span class="text-xs w-12 data-mono" style="color: var(--text-tertiary); flex-shrink: 0;">
                    {a.contribution > 0 ? '+' : ''}{a.contribution.toFixed(3)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <Callout>No feature attributions computed yet.</Callout>
        )}

        {/* Legend */}
        <div class="flex items-center gap-4 text-xs pt-2" style="color: var(--text-tertiary)">
          <div class="flex items-center gap-1">
            <span class="inline-block w-3 h-3 rounded" style="background: var(--accent); opacity: 0.7;" />
            <span>Pushes prediction up</span>
          </div>
          <div class="flex items-center gap-1">
            <span class="inline-block w-3 h-3 rounded" style="background: var(--accent-purple); opacity: 0.7;" />
            <span>Pushes prediction down</span>
          </div>
        </div>
      </div>
    </Section>
  );
}
