import { useState, ChangeEvent } from "react";

export default function FileUpload() {
    const [file, setFile] = useState<File | null>(null);
    const [message, setMessage] = useState("");
    const [uploading, setUploading] = useState(false);
    const [resetting, setResetting] = useState(false);

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files?.length) {
            setFile(e.target.files[0]);
            setMessage("");
        }
    };

    const handleReset = async () => {
        const confirmed = window.confirm("This will delete all transactions. Proceed?");
        if (!confirmed) return;
        setResetting(true);
        setMessage("");
        try {
            const res = await fetch("http://127.0.0.1:5001/reset", { method: "POST" });
            const text = await res.text();
            let data: { message?: string; error?: string } = {};
            try {
                data = JSON.parse(text);
            } catch {
                data = { message: text };
            }

            if (res.ok) {
                setMessage(`✅ ${data.message || "Database reset."}`);
                setFile(null);
                window.dispatchEvent(new Event("stats-refresh"));
            } else {
                setMessage(`❌ Error: ${data.error || data.message || "Reset failed"}`);
            }
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : String(err);
            setMessage(`❌ Reset failed: ${errorMessage}`);
        } finally {
            setResetting(false);
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
            if (res.ok) {
                setMessage(`✅ ${data.message}`);
                window.dispatchEvent(new Event("stats-refresh"));
            } else setMessage(`❌ Error: ${data.error}`);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : String(err);
            setMessage(`❌ Upload failed: ${errorMessage}`);
        } finally {
            setUploading(false);
        }
    };

    return (
        <section className="panel upload-panel">
            <div className="panel-header">
                <div>
                    <p className="eyebrow">Data ingest</p>
                    <h3>Upload transactions</h3>
                </div>
                <span className="chip subtle">{uploading ? "Uploading…" : "Ready"}</span>
            </div>

            <label className="dropzone">
                <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="file-input"
                />
                <div>
                    <div className="dropzone-title">
                        {file ? "Replace file" : "Drop CSV here or click to browse"}
                    </div>
                    <p className="dropzone-subtitle">
                        Bank statement CSV · Columns: Account Type, Number, Date, Description, Amount
                    </p>
                </div>
                <div className="file-pill">
                    {file ? file.name : "No file selected"}
                </div>
            </label>

            <div className="upload-actions">
                <div className="actions">
                    <button
                        onClick={handleUpload}
                        disabled={uploading}
                        className="btn primary"
                    >
                        {uploading ? "Uploading…" : "Upload & classify"}
                    </button>
                    <button
                        onClick={handleReset}
                        disabled={resetting || uploading}
                        className="btn danger"
                    >
                        {resetting ? "Resetting…" : "Reset DB"}
                    </button>
                </div>
                <p className="helper">
                    We parse, normalize dates, and auto-classify spending. Large files run in the background.
                </p>
                {message && (
                    <p className={`helper ${message.includes("Error") || message.includes("failed") ? "error" : "success"}`}>
                        {message}
                    </p>
                )}
            </div>
        </section>
    );
}
