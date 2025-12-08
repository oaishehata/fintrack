import { useEffect, useMemo, useState } from "react";

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
    const [classifying, setClassifying] = useState(false);

    const formatCurrency = (value: number) =>
        value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    const fetchStats = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch("http://127.0.0.1:5001/stats", {
                headers: { Accept: "application/json" },
            });

            const text = await res.text();
            try {
                const data = JSON.parse(text);
                setStats(data);
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
            } catch (parseErr) {
                throw new Error("Invalid JSON received from server");
            }
        } catch (err) {
            setError("Unable to load stats.");
        } finally {
            setLoading(false);
        }
    };

    const fetchProgress = async () => {
        try {
            const res = await fetch("http://127.0.0.1:5001/classification_progress");
            const data = await res.json();
            setProgress(data);
            setProgressError(null);
        } catch {
            setProgressError("Unable to load classification progress.");
        }
    };

    const startClassification = async () => {
        setClassifying(true);
        try {
            const res = await fetch("http://127.0.0.1:5001/classify", { method: "POST" });
            const data = await res.json();
            if (!res.ok) throw new Error(data?.error || "Failed to start classification");
            setProgress((prev) => prev ? { ...prev, running: true } : prev);
            fetchProgress();
        } catch (err) {
            const msg = err instanceof Error ? err.message : "Failed to start classification";
            setProgressError(msg);
        } finally {
            setClassifying(false);
        }
    };

    useEffect(() => {
        fetchStats();
        fetchProgress();
        const interval = setInterval(() => {
            fetchProgress();
        }, 2500);
        return () => clearInterval(interval);
    }, []);

    const maxCategoryTotal = useMemo(() => {
        if (!stats || stats.categories.length === 0) return 1;
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
                <div className="actions">
                    <button className="btn ghost" onClick={fetchStats} disabled={loading}>
                        {loading ? "Refreshing…" : "Refresh"}
                    </button>
                    <button className="btn ghost" onClick={startClassification} disabled={classifying}>
                        {classifying ? "Starting…" : "Reclassify"}
                    </button>
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

                <div className="stat-card attention">
                    <p className="stat-label">Duplicate groups</p>
                    <div className="stat-value">{stats.duplicate_groups}</div>
                    <span className="chip warning">
                        {stats.duplicate_transactions} extra txns flagged
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
        </section>
    );
}
