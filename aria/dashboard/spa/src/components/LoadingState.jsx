/**
 * Skeleton loading placeholders.
 * @param {{ type: 'stats' | 'table' | 'cards' | 'full' }} props
 */
export default function LoadingState({ type = 'full' }) {
  if (type === 'stats') {
    return (
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} class="t-card" style="padding: 16px;">
            <div class="h-8 w-16 animate-pulse mb-2" style="background: var(--bg-inset); border-radius: var(--radius);" />
            <div class="h-4 w-24 animate-pulse" style="background: var(--bg-inset); border-radius: var(--radius);" />
          </div>
        ))}
      </div>
    );
  }

  if (type === 'table') {
    return (
      <div class="t-card" style="overflow: hidden;">
        {/* Header row */}
        <div class="flex gap-4 px-4 py-3" style="border-bottom: 1px solid var(--border-subtle);">
          {[...Array(4)].map((_, i) => (
            <div key={i} class="h-4 animate-pulse flex-1" style="background: var(--bg-inset); border-radius: var(--radius);" />
          ))}
        </div>
        {/* Body rows */}
        {[...Array(6)].map((_, i) => (
          <div key={i} class="flex gap-4 px-4 py-3" style="border-bottom: 1px solid var(--border-subtle);">
            {[...Array(4)].map((_, j) => (
              <div key={j} class="h-4 animate-pulse flex-1" style="background: var(--bg-surface-raised); border-radius: var(--radius);" />
            ))}
          </div>
        ))}
      </div>
    );
  }

  if (type === 'cards') {
    return (
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} class="t-card" style="padding: 16px;">
            <div class="h-5 w-32 animate-pulse mb-3" style="background: var(--bg-inset); border-radius: var(--radius);" />
            <div class="h-4 w-full animate-pulse mb-2" style="background: var(--bg-surface-raised); border-radius: var(--radius);" />
            <div class="h-4 w-3/4 animate-pulse" style="background: var(--bg-surface-raised); border-radius: var(--radius);" />
          </div>
        ))}
      </div>
    );
  }

  // type === 'full'
  return (
    <div class="space-y-6">
      {/* Stats skeleton */}
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} class="t-card" style="padding: 16px;">
            <div class="h-8 w-16 animate-pulse mb-2" style="background: var(--bg-inset); border-radius: var(--radius);" />
            <div class="h-4 w-24 animate-pulse" style="background: var(--bg-inset); border-radius: var(--radius);" />
          </div>
        ))}
      </div>
      {/* Table skeleton */}
      <div class="t-card" style="overflow: hidden;">
        {[...Array(4)].map((_, i) => (
          <div key={i} class="flex gap-4 px-4 py-3" style="border-bottom: 1px solid var(--border-subtle);">
            {[...Array(4)].map((_, j) => (
              <div key={j} class="h-4 animate-pulse flex-1" style="background: var(--bg-surface-raised); border-radius: var(--radius);" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
