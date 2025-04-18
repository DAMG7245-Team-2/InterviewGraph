import { Routes, Route } from "react-router-dom";
import JobDescriptionPage from "@/pages/JobDescriptionPage";
import MockInterview from "@/pages/MockInterview";
import InterviewPrep from "./pages/InterviewPrep";

function App() {
  return (
    <Routes>
      <Route path="/" element={<JobDescriptionPage />} />
      <Route path="/interview" element={<MockInterview />} />
      <Route path="/prep" element={<InterviewPrep />} />
    </Routes>
  );
}

export default App;