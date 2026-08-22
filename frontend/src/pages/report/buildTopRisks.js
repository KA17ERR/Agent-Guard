const SEVERITY_RANK = { low: 1, medium: 2, high: 3, critical: 4 };

/**
 * Builds the "Top Risks" list from real Failure records attached to a
 * run's traces (GET /api/test-runs/{run_id}/traces). Groups failures by
 * category, keeping the highest-severity instance of each as the
 * representative explanation/recommendation, then ranks groups by worst
 * severity first, occurrence count second. Nothing here is invented --
 * every field comes from a real, persisted Failure row.
 */
export function buildTopRisks(traces, limit = 5) {
  const byCategory = new Map();

  for (const trace of traces || []) {
    for (const failure of trace.failures || []) {
      const existing = byCategory.get(failure.category);
      if (!existing) {
        byCategory.set(failure.category, { category: failure.category, count: 1, worst: failure });
      } else {
        existing.count += 1;
        if (SEVERITY_RANK[failure.severity] > SEVERITY_RANK[existing.worst.severity]) {
          existing.worst = failure;
        }
      }
    }
  }

  return Array.from(byCategory.values())
    .sort((a, b) => {
      const rankDiff = SEVERITY_RANK[b.worst.severity] - SEVERITY_RANK[a.worst.severity];
      if (rankDiff !== 0) return rankDiff;
      return b.count - a.count;
    })
    .slice(0, limit);
}
