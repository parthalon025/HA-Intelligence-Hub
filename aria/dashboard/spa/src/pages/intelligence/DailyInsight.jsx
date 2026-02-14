import { Section, Callout } from './utils.jsx';

export function DailyInsight({ insight }) {
  if (!insight) {
    return (
      <Section
        title="Daily Insight"
        subtitle="An AI-generated analysis of your home's patterns. Generated each night at 11:30 PM from the day's data."
      >
        <Callout>No insight report yet. The first report is generated after the first full pipeline run.</Callout>
      </Section>
    );
  }

  const lines = (insight.report || '').split('\n');

  return (
    <Section
      title="Daily Insight"
      subtitle="AI analysis of what happened yesterday and what to watch for. Generated nightly from your full data set."
      summary={insight.date}
    >
      <div class="t-frame p-4" data-label="insight">
        <span class="inline-block rounded px-2 py-0.5 text-xs mb-3" style="background: var(--bg-surface-raised); color: var(--text-tertiary)">{insight.date}</span>
        <div class="space-y-2" style="color: var(--text-secondary)">
          {lines.map((line, i) => {
            if (line.startsWith('###')) return <h3 key={i} class="text-sm font-bold mt-3" style="color: var(--text-primary)">{line.replace(/^###\s*/, '')}</h3>;
            if (line.trim() === '') return null;
            return <p key={i} class="text-sm leading-relaxed">{line}</p>;
          })}
        </div>
      </div>
    </Section>
  );
}
