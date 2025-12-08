import { useEffect, useMemo, useState, useCallback } from "react";

interface CategoryStat {
    category: string;
    count: number;
    total_cad: number;
}

interface Stats {
    total_transactions: number;
    total_cad: number;
    total_usd: number;
    categories: CategoryStat[];
    duplicate_transactions: number;
    duplicate_groups: number;
    recent_30d_count: number;
    recent_30d_total_cad: number;
    avg_daily_30d: number;
    monthly_trend: { month: string; count: number; total_cad: number }[];
    recurring_merchants: { merchant: string; txns: number; active_months: number; total_cad: number; avg_cad: number }[];
}

interface Progress {
    running: boolean;
    total: number;
    unclassified: number;
    classified: number;
    percent: number;
}

export default function StatsPanel() {
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [progress, setProgress] = useState<Progress | null>(null);
    const [progressError, setProgressError] = useState<string | null>(null);

    const formatCurrency = (value: number) =>
        value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    const normalizeStats = (data: Partial<Stats>): Stats => ({
        total_transactions: data.total_transactions ?? 0,
        total_cad: data.total_cad ?? 0,
        total_usd: data.total_usd ?? 0,
        categories: data.categories ?? [],
        duplicate_transactions: data.duplicate_transactions ?? 0,
        duplicate_groups: data.duplicate_groups ?? 0,
        recent_30d_count: data.recent_30d_count ?? 0,
        recent_30d_total_cad: data.recent_30d_total_cad ?? 0,
        avg_daily_30d: data.avg_daily_30d ?? 0,
        monthly_trend: data.monthly_trend ?? [],
        recurring_merchants: data.recurring_merchants ?? [],
    });

    const fetchStats = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch("http://127.0.0.1:5001/stats", {
                headers: { Accept: "application/json" },
            });

            const text = await res.text();
            try {
                const data = JSON.parse(text);
                setStats(normalizeStats(data));
            } catch {
                throw new Error("Invalid JSON received from server");
            }
        } catch {
            setError("Unable to load stats.");
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchProgress = useCallback(async () => {
        try {
            const res = await fetch("http://127.0.0.1:5001/classification_progress");
            const data = await res.json();
            setProgress(data);
            setProgressError(null);
        } catch {
            setProgressError("Unable to load classification progress.");
        }
    }, []);

    useEffect(() => {
        fetchStats();
        fetchProgress();
        const interval = setInterval(() => {
            fetchProgress();
        }, 2500);
        return () => clearInterval(interval);
    }, [fetchStats, fetchProgress]);

    useEffect(() => {
        const handler = () => {
            fetchStats();
            fetchProgress();
        };
        window.addEventListener("stats-refresh", handler);
        return () => window.removeEventListener("stats-refresh", handler);
    }, [fetchStats, fetchProgress]);

    useEffect(() => {
        if (!progress) return;

        if (progress.running) {
            const refreshInterval = setInterval(() => {
                fetchStats();
            }, 3000);
            return () => clearInterval(refreshInterval);
        }

        if (progress.total > 0 && progress.unclassified === 0) {
            fetchStats();
        }
    }, [progress, fetchStats]);

    const maxCategoryTotal = useMemo(() => {
        if (!stats || !stats.categories || stats.categories.length === 0) return 1;
        return Math.max(...stats.categories.map((c) => c.total_cad), 1);
    }, [stats]);

    if (loading) {
        return (
            <section className="panel stats-panel">
                <div className="panel-header">
                    <div>
                        <p className="eyebrow">Insights</p>
                        <h3>Spending & Duplicate Watch</h3>
                    </div>
                </div>
                <p className="helper">Loading stats…</p>
            </section>
        );
    }
    if (error) {
        return (
            <section className="panel stats-panel">
                <div className="panel-header">
                    <div>
                        <p className="eyebrow">Insights</p>
                        <h3>Spending & Duplicate Watch</h3>
                    </div>
                </div>
                <p className="helper error">{error}</p>
            </section>
        );
    }
    if (!stats) {
        return (
            <section className="panel stats-panel">
                <div className="panel-header">
                    <div>
                        <p className="eyebrow">Insights</p>
                        <h3>Spending & Duplicate Watch</h3>
                    </div>
                </div>
                <p className="helper error">No data available.</p>
            </section>
        );
    }

    const duplicateRate = stats.total_transactions
        ? Math.min(100, Math.round((stats.duplicate_transactions / stats.total_transactions) * 100))
        : 0;
    const topCategory = stats.categories[0];

    return (
        <section className="panel stats-panel">
            <div className="panel-header">
                <div>
                    <p className="eyebrow">Insights</p>
                    <h3>Spending & Duplicate Watch</h3>
                </div>
            </div>

            <div className="stat-grid">
                <div className="stat-card">
                    <p className="stat-label">Total transactions</p>
                    <div className="stat-value">{stats.total_transactions.toLocaleString()}</div>
                    <span className="chip subtle">
                        Across {stats.categories.length} categories
                    </span>
                </div>

                <div className="stat-card">
                    <p className="stat-label">Total volume (CAD)</p>
                    <div className="stat-value">${formatCurrency(stats.total_cad)}</div>
                    <span className="chip subtle">USD: ${formatCurrency(stats.total_usd)}</span>
                </div>

                <div className="stat-card">
                    <p className="stat-label">Last 30 days</p>
                    <div className="stat-value">${formatCurrency(stats.recent_30d_total_cad)}</div>
                    <span className="chip subtle">
                        {stats.recent_30d_count} txns · ${formatCurrency(stats.avg_daily_30d)} avg/day
                    </span>
                </div>
            </div>

            {progress && (
                <div className="progress-card">
                    <div className="progress-header">
                        <div>
                            <p className="stat-label">Classification progress</p>
                            <div className="stat-value small">
                                {progress.classified}/{progress.total} ({progress.percent}%)
                            </div>
                        </div>
                        <span className={`chip ${progress.running ? "success" : "subtle"}`}>
                            {progress.running ? "Running" : "Idle"}
                        </span>
                    </div>
                    <div className="progress-bar">
                        <div
                            className="progress-fill"
                            style={{ width: `${Math.min(progress.percent, 100)}%` }}
                        />
                    </div>
                    {progress.unclassified > 0 && (
                        <p className="helper">
                            {progress.unclassified} transactions remaining to classify.
                        </p>
                    )}
                    {progressError && <p className="helper error">{progressError}</p>}
                </div>
            )}

            <div className="insights-row">
                <div className="ring-card">
                    <div
                        className="ring"
                        style={{
                            background: `conic-gradient(#ff7f50 ${duplicateRate * 3.6}deg, rgba(255,255,255,0.06) 0deg)`,
                        }}
                    >
                        <div className="ring-center">
                            <div className="ring-value">{duplicateRate}%</div>
                            <span>duplicate rate</span>
                        </div>
                    </div>
                    <p className="helper">
                        {stats.duplicate_groups} groups · {stats.duplicate_transactions} duplicates over {stats.total_transactions} txns
                    </p>
                </div>

                <div className="categories-card">
                    <div className="categories-header">
                        <div>
                            <p className="eyebrow">Category breakdown</p>
                            <h4>Where money flows</h4>
                        </div>
                        {topCategory && (
                            <span className="chip success">
                                Top: {topCategory.category} (${formatCurrency(topCategory.total_cad)})
                            </span>
                        )}
                    </div>
                    <ul className="category-list">
                        {stats.categories.map((cat) => {
                            const width = Math.max(6, Math.round((cat.total_cad / maxCategoryTotal) * 100));
                            return (
                                <li key={cat.category} className="category-row">
                                    <div className="category-meta">
                                        <span className="category-name">{cat.category}</span>
                                        <span className="category-amount">${formatCurrency(cat.total_cad)}</span>
                                    </div>
                                    <div className="category-bar">
                                        <div
                                            className="category-fill"
                                            style={{ width: `${width}%` }}
                                            aria-label={`${cat.category} ${width}%`}
                                        />
                                    </div>
                                    <div className="category-count">{cat.count} txns</div>
                                </li>
                            );
                        })}
                    </ul>
                </div>
            </div>

            <div className="insights-row">
                <div className="categories-card">
                    <div className="categories-header">
                        <div>
                            <p className="eyebrow">Recurring merchants</p>
                            <h4>Likely recurring payments</h4>
                        </div>
                        <span className="chip subtle">
                            {stats.recurring_merchants.length} found
                        </span>
                    </div>
                    {stats.recurring_merchants.length === 0 ? (
                        <p className="helper">No recurring patterns detected yet.</p>
                    ) : (
                        <ul className="category-list">
                            {stats.recurring_merchants.map((m) => (
                                <li key={m.merchant} className="category-row">
                                    <div className="category-meta">
                                        <span className="category-name">{m.merchant}</span>
                                        <span className="category-amount">${formatCurrency(m.total_cad)}</span>
                                    </div>
                                    <div className="category-bar">
                                        <div
                                            className="category-fill"
                                            style={{ width: `${Math.min(100, Math.max(10, Math.round((m.txns / stats.total_transactions) * 100))) }%` }}
                                        />
                                    </div>
                                    <div className="category-count">
                                        {m.txns} txns · {m.active_months} months · avg ${formatCurrency(m.avg_cad)}
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div className="trend-card">
                    <div className="categories-header">
                        <div>
                            <p className="eyebrow">Monthly cadence</p>
                            <h4>Last 6 months</h4>
                        </div>
                    </div>
                    {stats.monthly_trend.length === 0 ? (
                        <p className="helper">No dated transactions yet.</p>
                    ) : (
                        <ul className="trend-list">
                            {stats.monthly_trend.map((m) => {
                                const max = Math.max(...stats.monthly_trend.map((x) => x.total_cad), 1);
                                const width = Math.max(8, Math.round((m.total_cad / max) * 100));
                                return (
                                    <li key={m.month} className="trend-row">
                                        <div className="trend-meta">
                                            <span className="trend-month">{m.month}</span>
                                            <span className="trend-amount">${formatCurrency(m.total_cad)}</span>
                                        </div>
                                        <div className="trend-bar">
                                            <div className="trend-fill" style={{ width: `${width}%` }} />
                                        </div>
                                        <div className="trend-count">{m.count} txns</div>
                                    </li>
                                );
                            })}
                        </ul>
                    )}
                </div>
            </div>
        </section>
    );
}
