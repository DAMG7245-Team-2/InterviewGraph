import { useState } from "react";

const PrepForm: React.FC = () => {
    const [desc, setDesc] = useState("");
    const[report, setReport] = useState("");

    const handleSubmit = async () => {
        const res = await fetch("http://localhost:8000/prep", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                job_description: desc,
            }),
        });
        const data = await res.json();
        setReport(data);
    };

    return (
        <div>
            <textarea
                className="w-full border p-2 rounded mb-2"
                rows={5}
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                placeholder="Paste job description here..."
            />
            <button className="bg-green-600 text-white px-4 py-2 rounded" onClick={handleSubmit}>
                Generate Report
            </button>
            {report && (
                <div className="mt-4 p-3 bg-white border rounded shadow">
                    <pre>{report}</pre>
                </div>
            )}
        </div>
    );
};

export default PrepForm;