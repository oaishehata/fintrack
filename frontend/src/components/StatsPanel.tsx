import { useEffect, useState } from "react";

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
}

export default function StatsPanel() {
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchStats = async () => {
        try {
            const res = await fetch("http://127.0.0.1:5001/stats", {
                headers: { Accept: "application/json" },
            });

            const text = await res.text();
            try {
                const data = JSON.parse(text);
                setStats(data);
                console.log("📊 Stats response:", data);
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
            } catch (parseErr) {
                console.error("⚠️ Failed to parse JSON:", text);
                throw new Error("Invalid JSON received from server");
            }
        } catch (err) {
            console.error("Failed to fetch stats:", err);
            setError("Unable to load stats.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStats();
    }, []);

    if (loading) return <p style={{ color: "#aaa" }}>Loading stats...</p>;
    if (error) return <p style={{ color: "#ff6b6b" }}>{error}</p>;
    if (!stats) return <p style={{ color: "#ff6b6b" }}>No data available.</p>;

    return (
        <div
            style={{
                backgroundColor: "#1b1b1b",
                borderRadius: "1rem",
                padding: "1.5rem",
                width: "100%",
                maxWidth: "450px",
                textAlign: "left",
                border: "1px solid #333",
                color: "#e0e0e0",
                margin: "1.5rem auto",
            }}
        >
            <h3
                style={{
                    marginBottom: "1rem",
                    color: "#fff",
                    borderBottom: "1px solid #333",
                    paddingBottom: "0.5rem",
                }}
            >
                📊 Database Summary
            </h3>

            <p><strong>Total Transactions:</strong> {stats.total_transactions}</p>
            <p><strong>Total CAD$:</strong> {stats.total_cad.toFixed(2)}</p>

            <h4 style={{ marginTop: "1rem", color: "#ddd" }}>By Category:</h4>
            <ul style={{ listStyle: "none", padding: 0 }}>
                {stats.categories.map((cat) => (
                    <li key={cat.category} style={{ marginBottom: "0.4rem" }}>
                        <strong>{cat.category}</strong>: {cat.count} txns (${cat.total_cad.toFixed(2)})
                    </li>
                ))}
            </ul>
        </div>
    );
}
