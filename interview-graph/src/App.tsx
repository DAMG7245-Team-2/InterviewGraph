import { Routes, Route } from "react-router-dom";
import JobDescriptionPage from "@/pages/JobDescriptionPage";
import MockInterview from "@/pages/MockInterview";

function App() {
  return (
    <Routes>
      <Route path="/job-description" element={<JobDescriptionPage />} />
      <Route path="/interview" element={<MockInterview />} />
    </Routes>
  );
}

export default App;