import { useState, ChangeEvent } from "react";

export default function FileUpload() {
    const [file, setFile] = useState<File | null>(null);
    const [message, setMessage] = useState("");
    const [uploading, setUploading] = useState(false);

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files?.length) {
            setFile(e.target.files[0]);
            setMessage("");
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setMessage("⚠️ Please select a file first.");
            return;
        }

        setUploading(true);
        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("http://127.0.0.1:5001/upload_csv", {
                method: "POST",
                body: formData,
            });

            const data = await res.json();
            if (res.ok) setMessage(`✅ ${data.message}`);
            else setMessage(`❌ Error: ${data.error}`);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : String(err);
            setMessage(`❌ Upload failed: ${errorMessage}`);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div
            style={{
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
                height: "100vh",
                backgroundColor: "#121212",
                color: "#e0e0e0",
                fontFamily: "Inter, system-ui, sans-serif",
                margin: 0,
            }}
        >
            <h1
                style={{
                    fontSize: "2.5rem",
                    fontWeight: 700,
                    marginBottom: "2rem",
                    color: "#f5f5f5",
                    textAlign: "center",
                }}
            >
                FinTrack
            </h1>

            <div
                style={{
                    backgroundColor: "#1e1e1e",
                    padding: "2.5rem",
                    borderRadius: "1rem",
                    width: "90%",
                    maxWidth: "420px",
                    boxShadow: "0 4px 25px rgba(0,0,0,0.3)",
                    textAlign: "center",
                    border: "1px solid #333",
                }}
            >
                <h2 style={{ fontSize: "1.4rem", marginBottom: "1.5rem", color: "#fff" }}>
                    Upload Bank Statement (CSV)
                </h2>

                <label
                    style={{
                        display: "block",
                        padding: "0.6rem 1rem",
                        borderRadius: "0.5rem",
                        backgroundColor: "#2b2b2b",
                        border: "1px solid #444",
                        color: "#ccc",
                        cursor: "pointer",
                        marginBottom: "1rem",
                    }}
                >
                    {file ? file.name : "Choose a CSV file"}
                    <input
                        type="file"
                        accept=".csv"
                        onChange={handleFileChange}
                        style={{ display: "none" }}
                    />
                </label>

                <button
                    onClick={handleUpload}
                    disabled={uploading}
                    style={{
                        backgroundColor: uploading ? "#555" : "#4CAF50",
                        color: "white",
                        fontWeight: 600,
                        border: "none",
                        borderRadius: "0.5rem",
                        padding: "0.7rem 1.5rem",
                        width: "100%",
                        cursor: uploading ? "not-allowed" : "pointer",
                        transition: "background-color 0.2s ease",
                    }}
                >
                    {uploading ? "Uploading..." : "Upload"}
                </button>

                {message && (
                    <p
                        style={{
                            marginTop: "1.5rem",
                            color: message.includes("Error") || message.includes("failed") ? "#ff6b6b" : "#4caf50",
                            fontSize: "0.95rem",
                            fontWeight: 500,
                        }}
                    >
                        {message}
                    </p>
                )}
            </div>
        </div>
    );
}