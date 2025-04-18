import { Routes, Route } from "react-router-dom";
import JobDescriptionPage from "@/pages/JobDescriptionPage";
import MockInterview from "@/pages/MockInterview";
import InterviewPrep from "./pages/InterviewPrep";
import LandingPage from "./pages/LandingPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/interview-job-description" element={<JobDescriptionPage />} />
      <Route path="/interview" element={<MockInterview />} />
      <Route path="/prep" element={<InterviewPrep />} />
    </Routes>
  );
}

export default App;