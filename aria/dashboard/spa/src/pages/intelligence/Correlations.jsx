import { Section, Callout } from './utils.jsx';

export function Correlations({ correlations }) {
  const hasData = correlations && correlations.length > 0;

  return (
    <Section
      title="Correlations"
      subtitle={hasData
        ? 'Devices that change together. Strong correlations suggest automation opportunities or shared failure modes.'
        : 'Devices that tend to change together \u2014 useful for creating automations or finding shared failure points.'
      }
      summary={hasData ? correlations.length + " pairs" : null}
    >
      {!hasData ? (
        <Callout>No correlations yet. Needs enough data to detect statistically reliable relationships between devices.</Callout>
      ) : (
        <div class="t-frame overflow-x-auto" data-label="correlations">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-xs uppercase" style="border-bottom: 1px solid var(--border-subtle); color: var(--text-tertiary)">
                <th class="px-4 py-2">Entity A</th>
                <th class="px-4 py-2">Entity B</th>
                <th class="px-4 py-2">Strength</th>
                <th class="px-4 py-2">Direction</th>
              </tr>
            </thead>
            <tbody>
              {correlations.map((c, i) => (
                <tr key={i} style="border-bottom: 1px solid var(--border-subtle)">
                  <td class="px-4 py-2 data-mono text-xs">{c.entity_a || c[0]}</td>
                  <td class="px-4 py-2 data-mono text-xs">{c.entity_b || c[1]}</td>
                  <td class="px-4 py-2">{c.strength || c[2]}</td>
                  <td class="px-4 py-2">{c.direction || c[3] || '\u2014'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Section>
  );
}
