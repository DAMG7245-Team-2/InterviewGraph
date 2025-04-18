import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Sparkles, Mic, NotebookText } from "lucide-react";
import "@/styles/animated-gradient.css";

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="animated-gradient min-h-screen flex flex-col items-center justify-center px-6 py-16 text-gray-800">
      <div className="max-w-4xl w-full space-y-12 text-center">
        <div className="space-y-4">
          <h1 className="text-5xl font-extrabold flex items-center justify-center gap-3 text-gray-900">
            <Sparkles className="w-8 h-8 text-purple-500 animate-pulse" />
            AI-Powered Interview Companion
          </h1>
          <p className="text-lg text-gray-700 max-w-2xl mx-auto">
            Elevate your interview prep with intelligent tools designed to simulate real interview scenarios and provide personalized preparation material tailored to your job description.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 animate-fade-in delay-[200ms]">
          <div className="p-6 bg-white/90 backdrop-blur-md rounded-2xl shadow-xl text-left space-y-4 border border-purple-100 transform transition-transform duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-purple-200">
            <div className="flex items-center gap-3 text-purple-600">
              <Mic className="w-6 h-6" />
              <h2 className="text-2xl font-semibold">Mock Interview</h2>
            </div>
            <p className="text-sm text-gray-600">
              Simulate a realistic AI-powered interview. Answer questions aloud or by typing, get feedback on your performance, and track your interview duration.
            </p>
            <Button
              onClick={() => navigate("/interview-job-description")}
              className="bg-purple-200 hover:bg-purple-300 text-gray-900"
            >
              Start Mock Interview
            </Button>
          </div>

          <div className="p-6 bg-white/90 backdrop-blur-md rounded-2xl shadow-xl text-left space-y-4 border border-emerald-100 transform transition-transform duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-emerald-200">
            <div className="flex items-center gap-3 text-emerald-600">
              <NotebookText className="w-6 h-6" />
              <h2 className="text-2xl font-semibold">Interview Prep</h2>
            </div>
            <p className="text-sm text-gray-600">
              Paste your job description and receive an AI-generated prep report with key skills, topics, sample questions, and flowcharts to study beforehand.
            </p>
            <Button
              onClick={() => navigate("/prep")}
              className="bg-emerald-200 hover:bg-emerald-300 text-gray-900"
            >
              Go to Prep Assistant
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
