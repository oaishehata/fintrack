import "./App.css";
import FileUpload from "./components/FileUpload";
import StatsPanel from "./components/StatsPanel";

function App() {
    return (
        <div className="page">
            <div className="orb orb-1" />
            <div className="orb orb-2" />
            <div className="orb orb-3" />

            <main className="shell">
                <header className="hero">
                    <div className="hero-eyebrow">Recurring intelligence</div>
                    <div className="hero-row">
                        <h1>FinTrack</h1>
                        <span className="pill live">Live</span>
                    </div>
                    <p className="lede">
                        Upload statements, classify spending, and spot duplicate transactions before they slip
                        through. Modern, fast, and built for finance ops.
                    </p>
                </header>

                <div className="grid">
                    <FileUpload />
                    <StatsPanel />
                </div>
            </main>
        </div>
    );
}

export default App;
