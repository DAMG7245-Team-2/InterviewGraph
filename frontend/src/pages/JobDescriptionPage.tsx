import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Sparkles } from "lucide-react";
import { v4 as uuidv4 } from "uuid";
import "@/styles/animated-gradient.css";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

export default function JobDescriptionPage() {
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleStart = async () => {
    if (!jobDescription.trim()) return;

    setLoading(true);
    const threadId = uuidv4();

    try {
      const res = await fetch(`${BACKEND_URL}/interview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: jobDescription, thread_id: threadId })
      });

      const data = await res.json();

      if (
        typeof data?.message === "string" &&
        data.message.toLowerCase().includes("please provide a valid job description")
      ) {
        alert("Please provide a valid job description.");
      } else {
        localStorage.setItem("job_description", jobDescription);
        localStorage.setItem("thread_id", threadId);
        navigate("/interview", { state: { fromJobDescription: true } });
      }
    } catch (err) {
      console.error("Validation error:", err);
      alert("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const isJobDescEmpty = jobDescription.trim().length === 0;

  return (
    <div className="animated-gradient min-h-screen flex items-center justify-center px-4">
      <div className="absolute top-6 left-6">
  <Button
    onClick={() => navigate("/")}
    variant="ghost"
    className="text-sm text-gray-600 hover:text-black flex items-center gap-2"
  >
    ← Back to Home
  </Button>
</div>
      <div className="bg-white shadow-2xl rounded-3xl p-10 max-w-3xl w-full space-y-8 border border-purple-100 backdrop-blur-md bg-opacity-90">
        <div className="text-center space-y-3">
          <h1 className="text-5xl font-extrabold text-black-600 flex items-center justify-center gap-2">
            <Sparkles className="w-8 h-8 text-purple-400 animate-pulse" />
            Start Your Mock Interview
          </h1>
          <p className="text-gray-700 text-lg">
            Paste a job description below to begin your personalized mock interview session.
          </p>
        </div>

        <div className="flex flex-col space-y-2">
          <label htmlFor="jobDesc" className="text-md font-medium text-gray-800">
            Job Description
          </label>
          <Textarea
            id="jobDesc"
            rows={8}
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the job description here..."
            className="rounded-xl border-gray-300 shadow-sm text-base"
          />
        </div>

        <div className="flex justify-center pt-2">
          <Button
            onClick={handleStart}
            disabled={isJobDescEmpty || loading}
            className={`px-6 py-3 font-semibold rounded-xl text-base shadow-lg transition-all duration-300 ${
              isJobDescEmpty
                ? "bg-gray-300 text-white cursor-not-allowed"
                : loading
                ? "bg-purple-500 text-white cursor-wait"
                : "bg-purple-200 hover:bg-purple-300 text-gray-900"
            }`}
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <svg
                  className="animate-spin h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v4l3.5-3.5L12 0v4a8 8 0 010 16v-4l-3.5 3.5L12 24v-4a8 8 0 01-8-8z"
                  />
                </svg>
                Validating...
              </div>
            ) : (
              "Start Mock Interview"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
