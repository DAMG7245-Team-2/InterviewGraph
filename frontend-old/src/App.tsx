import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";
import InterviewPage from "./pages/InterviewPage.tsx";
import PrepPage from "./pages/PrepPage.tsx";
import HomePage from "./pages/HomePage.tsx";

const App : React.FC = () => {
  return (
    <Router>
      <div className="w-full p-4 space-x-4 bg-gray-800">
        <Link to="/" className="font-semibold text-emerald-500 hover:text-emerald-300">Home</Link>
        <Link to="/interview" className="font-semibold text-emerald-500 hover:text-emerald-300">Interview Agent</Link>
        <Link to="/prep" className="font-semibold text-emerald-500 hover:text-emerald-300">Prep Agent</Link>
      </div>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/interview" element={<InterviewPage />} />
        <Route path="/prep" element={<PrepPage />} />
      </Routes>
    </Router>
  );
};

export default App;