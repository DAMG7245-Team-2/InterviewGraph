import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

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
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-4">
      <div className="bg-white shadow-xl rounded-3xl p-10 max-w-2xl w-full space-y-6">
        <h1 className="text-4xl font-bold text-center text-lavender-600">Start Your Mock Interview</h1>
        <div className="space-y-2">
          <label htmlFor="jobDesc" className="text-lg font-medium text-gray-800">
            Enter Job Description
          </label>
          <Textarea
            id="jobDesc"
            rows={6}
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the job description here..."
            className="rounded-xl border-gray-300 shadow-sm"
          />
        </div>
        <div className="flex justify-center">
          <Button
            onClick={handleStart}
            disabled={isJobDescEmpty}
            className={`px-6 py-3 font-semibold rounded-md shadow-md transition-colors duration-300 ${
              isJobDescEmpty
                ? "bg-gray-300 text-white cursor-not-allowed"
                : "bg-purple-200 hover:bg-purple-300 text-gray-900"
            }`}
          >
            Start Interview
          </Button>
        </div>
      </div>
    </div>
  );
}
