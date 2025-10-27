import FileUpload from "./components/FileUpload";
import StatsPanel from "./components/StatsPanel";

function App() {
    return (
        <div
            style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: "100vh",
                backgroundColor: "#121212",
                color: "#e0e0e0",
                fontFamily: "Inter, system-ui, sans-serif",
                gap: "2rem",
            }}
        >
            <h1 style={{ fontSize: "2.5rem", fontWeight: 700, color: "#f5f5f5" }}>
                FinTrack
            </h1>

            <FileUpload />
            <StatsPanel />

        </div>
    );
}

export default App;
