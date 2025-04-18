import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import MermaidComponent from '@/components/ui/MermaidComponent';
import { Button } from '@/components/ui/button';
import { Contact, ArrowUp, Printer } from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

export default function InterviewPrep() {
  const [desc, setDesc] = useState("");
  const [report, setReport] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showTop, setShowTop] = useState(false);
  const [hasChangedSinceReport, setHasChangedSinceReport] = useState(false);
  const [selectedDiagram, setSelectedDiagram] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async () => {
    if (desc.trim().length < 50) return;
    try {
      setError("");
      setReport("");
      setLoading(true);

      const res = await fetch(`${BACKEND_URL}/prep`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_description: desc }),
      });

      const responseBody = await res.text();

      if (!res.ok) {
        let errorMsg = "Failed to generate report";
        try {
          const errorData = JSON.parse(responseBody);
          if (errorData && Array.isArray(errorData.detail)) {
            errorMsg = errorData.detail.map((err: { msg: any }) => err.msg).join(', ');
          } else if (errorData?.detail) {
            errorMsg = errorData.detail;
          } else if (errorData?.message) {
            errorMsg = errorData.message;
          }
        } catch {
          if (responseBody && responseBody.trim().length > 0) {
            errorMsg = responseBody;
          }
        }
        throw new Error(errorMsg);
      }

      const jsonData = JSON.parse(responseBody);
      if (!jsonData.final_report) throw new Error("Invalid response - missing final_report");

      setReport(jsonData.final_report);
      setHasChangedSinceReport(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Server error - please try again later");
    } finally {
      setLoading(false);
    }
  };

  const handleScrollTop = () => window.scrollTo({ top: 0, behavior: 'smooth' });
  const handlePrint = () => window.print();

  useEffect(() => {
    const toggleVisibility = () => setShowTop(window.scrollY > 500);
    window.addEventListener('scroll', toggleVisibility);
    return () => window.removeEventListener('scroll', toggleVisibility);
  }, []);

  return (
    <div className="min-h-screen w-full bg-gradient-to-r from-yellow-50 via-rose-100 to-teal-100 bg-[length:400%_400%] animate-gradient-x text-gray-800 flex flex-col items-center justify-start px-6 py-16 relative">
      <div className="absolute top-6 left-6 no-print">
        <Button
          onClick={() => navigate("/")}
          variant="ghost"
          className="text-sm text-gray-600 hover:text-black flex items-center gap-2"
        >
          ← Back to Home
        </Button>
      </div>

      <div className="max-w-5xl w-full space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3 text-neutral-800">
            <Contact className="w-7 h-7 text-neutral-600" />
            <h1 className="text-4xl font-semibold">Interview Prep Assistant</h1>
          </div>
        </div>

        <p className="text-gray-600 max-w-3xl text-md leading-relaxed">
          This AI agent analyzes your job description and provides a focused preparation report tailored for your upcoming mock interview.
        </p>

        <div className="flex flex-col space-y-2">
          <label htmlFor="desc" className="text-md font-medium text-gray-800">
            Job Description
          </label>
          <Textarea
            id="desc"
            rows={6}
            value={desc}
            onChange={(e) => {
              const newVal = e.target.value;
              setDesc(newVal);
              if (report && newVal.trim() !== desc.trim()) {
                setHasChangedSinceReport(true);
              }
            }}
            placeholder="Paste your job description here (minimum 50 characters)..."
            className="rounded-xl border-gray-300 shadow-sm text-base bg-white"
          />

          {(hasChangedSinceReport || (!report && !loading)) && (
            <div className="flex justify-end no-print pt-2">
              <Button
                onClick={handleSubmit}
                disabled={desc.trim().length < 50}
                className={`px-6 py-2 font-semibold rounded-xl text-base shadow-lg transition-all duration-300 ${
                  desc.trim().length < 50
                    ? "bg-gray-300 text-white cursor-not-allowed"
                    : "bg-black hover:bg-neutral-900 text-white"
                }`}
              >
                Generate Prep Report
              </Button>
            </div>
          )}
        </div>

        {loading && !report && !error && (
          <div className="relative flex flex-col items-center justify-center overflow-hidden bg-white/90 backdrop-blur-md rounded-2xl shadow-md p-10 animate-fade-in text-gray-700">
            <div className="absolute inset-0 bg-gradient-to-br from-gray-200 via-transparent to-gray-100 opacity-30 animate-pulse-slow z-0" />
            <div className="relative z-10 flex flex-col items-center space-y-4 text-center">
              <p className="text-xl font-medium animate-pulse">Generating your prep report…</p>
              <div className="flex space-x-2 mt-1">
                <div className="w-3 h-3 bg-neutral-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
                <div className="w-3 h-3 bg-neutral-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <div className="w-3 h-3 bg-neutral-500 rounded-full animate-bounce" />
              </div>
              <p className="text-sm text-gray-500 max-w-md">
                Our agent is working hard to personalize your interview preparation. This won't take long.
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 border border-red-300 bg-red-50 text-red-700 rounded-lg">
            ⚠️ {error}
          </div>
        )}

        {report && !error && (
          <div id="report-markdown" className="p-8 bg-white rounded-2xl shadow-md">
            <ReactMarkdown
              components={{
                code({ node, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  if (match && match[1] === 'mermaid') {
                    return (
                      <div className="flex justify-center overflow-x-auto">
                        <MermaidComponent>{String(children).trim()}</MermaidComponent>
                      </div>
                    );
                  }
                  return (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
                h1: ({ node, ...props }) => <h1 className="text-3xl font-bold mt-6 mb-4 text-black" {...props} />,
                h2: ({ node, ...props }) => <h2 className="text-2xl font-semibold mt-5 mb-3 text-neutral-800" {...props} />,
                h3: ({ node, ...props }) => <h3 className="text-xl font-medium mt-4 mb-2 text-neutral-700" {...props} />,
                p: ({ node, ...props }) => <p className="text-gray-800 leading-relaxed mb-4" {...props} />,
                ul: ({ node, ...props }) => <ul className="list-disc pl-6 mb-4 text-gray-800" {...props} />,
                ol: ({ node, ...props }) => <ol className="list-decimal pl-6 mb-4 text-gray-800" {...props} />,
                li: ({ node, ...props }) => <li className="mb-2" {...props} />,
                a: ({ node, ...props }) => (
                  <a
                    className="text-blue-600 underline hover:text-blue-800"
                    target="_blank"
                    rel="noopener noreferrer"
                    {...props}
                  />
                ),
              }}
              remarkPlugins={[remarkGfm, remarkBreaks]}
            >
              {report}
            </ReactMarkdown>
          </div>
        )}

        {selectedDiagram && (
          <div
            className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
            onClick={() => setSelectedDiagram(null)}
          >
            <div
              className="bg-white rounded-xl shadow-xl p-4 max-w-6xl w-full max-h-[90vh] overflow-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <MermaidComponent>{selectedDiagram}</MermaidComponent>
              <p className="text-center text-sm text-gray-500 mt-2">Click outside to close</p>
            </div>
          </div>
        )}

        {showTop && (
          <>
            <button
              onClick={handlePrint}
              className="fixed bottom-20 right-6 z-50 p-3 bg-white text-black rounded-full shadow-lg hover:bg-gray-100 border border-gray-300 no-print"
            >
              <Printer className="w-5 h-5" />
            </button>
            <button
              onClick={handleScrollTop}
              className="fixed bottom-6 right-6 z-50 p-3 bg-black text-white rounded-full shadow-lg hover:bg-neutral-900 no-print"
            >
              <ArrowUp className="w-5 h-5" />
            </button>
          </>
        )}
      </div>
    </div>
  );
}
