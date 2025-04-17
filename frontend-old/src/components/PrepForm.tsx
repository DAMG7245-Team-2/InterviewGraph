import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import MermaidComponent from './MermaidComponent';

const PrepForm: React.FC = () => {
  const [desc, setDesc] = useState('');
  const [report, setReport] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    try {
      setError("");
      setReport("");
      console.log("Starting API call");
      const res = await fetch("http://localhost:8000/prep", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ job_description: desc }),
      });

      console.log("API response status:", res.status);
      const responseBody = await res.text();
      console.log("Raw API response:", responseBody);

      if (!res.ok) {
        let errorMsg = "Failed to generate report";
        try {
          const errorData = JSON.parse(responseBody);
          if (errorData && Array.isArray(errorData.detail)) {
            errorMsg = errorData.detail.map((err: { msg: any; }) => err.msg).join(', ');
          } else if (errorData && errorData.detail) {
            errorMsg = errorData.detail;
          } else if (errorData && errorData.message) {
            errorMsg = errorData.message;
          }
        } catch {
          if (responseBody && responseBody.trim().length > 0) {
            errorMsg = responseBody;
          }
        }
        throw new Error(errorMsg);
      }

      let jsonData;
      try {
        jsonData = JSON.parse(responseBody);
      } catch {
        throw new Error("Invalid response format from server");
      }
      if (!jsonData.final_report) {
        throw new Error("Invalid response format - missing final_report");
      }
      setReport(jsonData.final_report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Server error - please try again later");
      setReport("");
      console.error("API Error:", err);
    }
  };

  return (
    <div>
      <textarea
        className=" w-full text-white border p-2 rounded mb-2"
        rows={5}
        value={desc}
        onChange={(e) => setDesc(e.target.value)}
        placeholder="Paste job description here..."
      />
      <div className='flex justify-center mt-4'>
        <button
          className=" !bg-emerald-600 hover:!bg-emerald-700 !text-white px-6 py-3 rounded-full shadow-lg shadow-emerald-700/50 transition-colors duration-200 focus:ring-2 focus:ring-emerald-700 focus:ring-offset-2"
          onClick={handleSubmit}
        >
          Generate Report
        </button>
      </div>
      
      {error && (
        <div className="mt-4 p-4 bg-red-900/30 border border-red-700 rounded-lg animate-fade-in">
          <div className="flex items-center text-red-400">
            <span className="mr-2">⚠️</span>
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}
      {report && !error && (
        <div className="mt-4 p-6 bg-gray-800 border border-gray-700 rounded-lg shadow-xl transition-all duration-300 ease-out overflow-y-auto hover:shadow-2xl">
          <div className="justify-center prose prose-invert dark:prose-invert max-w-none text-left text-gray-100 markdown">
            <ReactMarkdown
              components={{
                code({ node, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  if (match && match[1] === 'mermaid') {
                    return (<MermaidComponent>{String(children).trim()}</MermaidComponent>)
                  }
                  return (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
              }}
                remarkPlugins={[remarkGfm, remarkBreaks]}
            >
              {report}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
};

export default PrepForm;