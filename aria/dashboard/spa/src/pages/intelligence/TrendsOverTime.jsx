import { Section, Callout } from './utils.jsx';
import TimeChart from '../../components/TimeChart.jsx';

function toUPlotData(records, timeKey, metrics) {
  const timestamps = records.map(r => {
    if (timeKey === 'date') {
      return Math.floor(new Date(r.date).getTime() / 1000);
    } else {
      const now = new Date();
      return Math.floor(new Date(now.getFullYear(), now.getMonth(), now.getDate(), r.hour).getTime() / 1000);
    }
  });
  const series = metrics.map(m => records.map(r => r[m] ?? null));
  return [timestamps, ...series];
}

export function TrendsOverTime({ trendData, intradayTrend }) {
  const hasTrend = trendData && trendData.length > 0;
  const hasIntraday = intradayTrend && intradayTrend.length > 0;

  if (!hasTrend && !hasIntraday) {
    return (
      <Section
        title="Trends Over Time"
        subtitle="Spot when something changed — a new device, a routine shift, or a problem building."
      >
        <Callout>No trend data yet. Daily snapshots are collected each night at 11:30 PM.</Callout>
      </Section>
    );
  }

  // Detect notable changes in daily trend
  let trendNote = null;
  if (hasTrend && trendData.length >= 2) {
    const last = trendData[trendData.length - 1];
    const prev = trendData[trendData.length - 2];
    const changes = [];
    if (last.power_watts != null && prev.power_watts != null) {
      const d = last.power_watts - prev.power_watts;
      if (Math.abs(d) > 50) changes.push(`Power ${d > 0 ? 'up' : 'down'} ${Math.abs(Math.round(d))}W vs yesterday`);
    }
    if (last.unavailable != null && prev.unavailable != null) {
      const d = last.unavailable - prev.unavailable;
      if (d > 10) changes.push(`${d} more entities unavailable than yesterday — check your network`);
    }
    if (changes.length > 0) trendNote = changes.join('. ') + '.';
  }

  const dailySeries = [
    { label: 'Power (W)', color: 'var(--accent)' },
    { label: 'Lights On', color: 'var(--accent-warm)' },
    { label: 'Unavailable', color: 'var(--status-error)' },
  ];

  const intradaySeries = [
    { label: 'Power (W)', color: 'var(--accent-dim)' },
    { label: 'Unavailable', color: 'var(--status-error)' },
  ];

  return (
    <Section
      title="Trends Over Time"
      subtitle="Spot when something changed — a new device, a routine shift, or a problem building."
    >
      {trendNote && <Callout>{trendNote}</Callout>}
      <div class="t-frame" data-label="trends">
        {hasTrend && (
          <div class="space-y-3">
            <div class="text-xs font-bold uppercase" style="color: var(--text-tertiary)">Daily (30d)</div>
            <TimeChart
              data={toUPlotData(trendData, 'date', ['power_watts', 'lights_on', 'unavailable'])}
              series={dailySeries}
              height={140}
            />
          </div>
        )}
        {hasIntraday && (
          <div class="space-y-3">
            <div class="text-xs font-bold uppercase" style="color: var(--text-tertiary)">Today (Intraday)</div>
            <TimeChart
              data={toUPlotData(intradayTrend, 'hour', ['power_watts', 'unavailable'])}
              series={intradaySeries}
              height={100}
            />
          </div>
        )}
      </div>
    </Section>
  );
}
