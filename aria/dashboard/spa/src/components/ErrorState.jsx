/**
 * Error alert with retry button.
 * @param {{ error: string|Error, onRetry?: function }} props
 */
export default function ErrorState({ error, onRetry }) {
  const message = error instanceof Error ? error.message : String(error || 'Unknown error');

  return (
    <div style="background: var(--bg-surface); border: 1px solid var(--status-error); border-left-width: 3px; border-radius: var(--radius); padding: 16px;">
      <div class="flex items-start gap-3">
        <svg class="w-5 h-5 mt-0.5 shrink-0" style="color: var(--status-error);" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        <div class="flex-1">
          <p class="text-sm" style="color: var(--status-error);">{message}</p>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            class="text-sm font-medium transition-colors"
            style="color: var(--status-error); background: var(--bg-surface-raised); border-radius: var(--radius); padding: 4px 12px;"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
