import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";
import InterviewPage from "./pages/InterviewPage.tsx";
import PrepPage from "./pages/PrepPage.tsx";

const App : React.FC = () => {
  return (
    <Router>
      <div className="p-4 space-x-4 bg-gray-100">
        <Link to="/interview" className="font-semibold">Interview Agent</Link>
        <Link to="/prep" className="font-semibold">Prep Agent</Link>
      </div>
      <Routes>
        <Route path="/interview" element={<InterviewPage />} />
        <Route path="/prep" element={<PrepPage />} />
      </Routes>
    </Router>
  );
};

export default App;