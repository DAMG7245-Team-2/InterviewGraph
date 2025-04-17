import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Sparkles } from "lucide-react";
import "@/styles/animated-gradient.css";

export default function JobDescriptionPage() {
  const [jobDescription, setJobDescription] = useState("");
  const navigate = useNavigate();

  const handleStart = () => {
    if (jobDescription.trim()) {
      localStorage.setItem("job_description", jobDescription);
      navigate("/interview", { state: { fromJobDescription: true } });
    }
  };

  const isJobDescEmpty = jobDescription.trim().length === 0;

  return (
    <div className="animated-gradient min-h-screen flex items-center justify-center px-4">
      <div className="bg-white shadow-2xl rounded-3xl p-10 max-w-3xl w-full space-y-8 border border-purple-100 backdrop-blur-md bg-opacity-90">
        <div className="text-center space-y-2">
          <h1 className="text-5xl font-extrabold text-lavender-600 flex items-center justify-center gap-3">
            <Sparkles className="w-10 h-10 text-purple-400 animate-pulse" /> Start Your Mock Interview
          </h1>
          <p className="text-gray-600 text-lg">Paste a job description below to generate your personalized mock interview.</p>
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
            disabled={isJobDescEmpty}
            className={`px-6 py-3 font-semibold rounded-xl text-base shadow-lg transition-all duration-300 ${
              isJobDescEmpty ? "bg-gray-300 text-white cursor-not-allowed" : "bg-purple-200 hover:bg-purple-300 text-gray-900"
            }`}
          >
            Start Interview
          </Button>
        </div>
      </div>
    </div>
  );
}
