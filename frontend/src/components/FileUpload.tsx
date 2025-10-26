import { useState, ChangeEvent } from "react";

export default function FileUpload() {
    const [file, setFile] = useState<File | null>(null);
    const [message, setMessage] = useState("");

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files?.length) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setMessage("Please select a file first.");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("http://127.0.0.1:5001/upload_csv", {
                method: "POST",
                body: formData,
            });

            const data = await res.json();
            if (res.ok) setMessage(data.message);
            else setMessage(`Error: ${data.error}`);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : String(err);
            setMessage(`Upload failed: ${errorMessage}`);
        }
    };

    return (
        <div style={{ textAlign: "center", marginTop: "3rem" }}>
            <h2>Upload Bank Statement (CSV)</h2>
            <input type="file" accept=".csv" onChange={handleFileChange} />
            <br />
            <br />
            <button onClick={handleUpload}>Upload</button>
            <p>{message}</p>
        </div>
    );
}
