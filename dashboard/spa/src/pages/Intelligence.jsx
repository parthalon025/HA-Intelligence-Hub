import { useState } from 'preact/hooks';
import useCache from '../hooks/useCache.js';
import useComputed from '../hooks/useComputed.js';
import LoadingState from '../components/LoadingState.jsx';
import ErrorState from '../components/ErrorState.jsx';
import { Callout } from './intelligence/utils.jsx';
import { LearningProgress } from './intelligence/LearningProgress.jsx';
import { HomeRightNow } from './intelligence/HomeRightNow.jsx';
import { ActivitySection } from './intelligence/ActivitySection.jsx';
import { TrendsOverTime } from './intelligence/TrendsOverTime.jsx';
import { PredictionsVsActuals } from './intelligence/PredictionsVsActuals.jsx';
import { Baselines } from './intelligence/Baselines.jsx';
import { DailyInsight } from './intelligence/DailyInsight.jsx';
import { Correlations } from './intelligence/Correlations.jsx';
import { SystemStatus } from './intelligence/SystemStatus.jsx';
import { Configuration } from './intelligence/Configuration.jsx';

export default function Intelligence() {
  const { data, loading, error, refetch } = useCache('intelligence');

  const intel = useComputed(() => {
    if (!data || !data.data) return null;
    return data.data;
  }, [data]);

  if (loading && !data) {
    return (
      <div class="space-y-6">
        <h1 class="text-2xl font-bold text-gray-900">Intelligence</h1>
        <LoadingState type="cards" />
      </div>
    );
  }

  if (error) {
    return (
      <div class="space-y-6">
        <h1 class="text-2xl font-bold text-gray-900">Intelligence</h1>
        <ErrorState error={error} onRetry={refetch} />
      </div>
    );
  }

  if (!intel) {
    return (
      <div class="space-y-6">
        <h1 class="text-2xl font-bold text-gray-900">Intelligence</h1>
        <Callout>Intelligence data is loading. The engine collects its first snapshot automatically via cron.</Callout>
      </div>
    );
  }

  return (
    <div class="space-y-8">
      <h1 class="text-2xl font-bold text-gray-900">Intelligence</h1>

      <LearningProgress maturity={intel.data_maturity} />
      <HomeRightNow intraday={intel.intraday_trend} baselines={intel.baselines} />
      <ActivitySection activity={intel.activity} />
      <TrendsOverTime trendData={intel.trend_data} intradayTrend={intel.intraday_trend} />
      <PredictionsVsActuals predictions={intel.predictions} intradayTrend={intel.intraday_trend} />
      <Baselines baselines={intel.baselines} />
      <DailyInsight insight={intel.daily_insight} />
      <Correlations correlations={intel.correlations} />
      <SystemStatus runLog={intel.run_log} mlModels={intel.ml_models} metaLearning={intel.meta_learning} />
      <Configuration config={intel.config} />
    </div>
  );
}
