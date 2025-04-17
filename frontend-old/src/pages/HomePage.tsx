import { Link } from 'react-router-dom';

const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen w-full max-w-full bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900">
      <div className="w-full px-4 py-8">
        <h1 className="centered text-4xl font-bold text-emerald-500 mb-6">Welcome to InterviewGraph</h1>
        <p className="centered text-lg text-gray-100 mb-8">
          Your AI-powered interview preparation platform. Practice with realistic scenarios,
          get instant feedback, and track your progress over time.
        </p>
        
        <div className="centered bg-gray-800 rounded-lg shadow-xl p-6 mb-8">
          <h2 className="centered text-2xl font-semibold text-gray-100 mb-4">Get Started</h2>
          <div className="flex space-x-4 justify-center">
            <Link
              to="/interview"
              className="bg-emerald-600 text-white px-6 py-3 rounded-md hover:bg-emerald-700 transition-colors"
            >
              Start Interview
            </Link>
            <Link
              to="/prep"
              className="bg-emerald-600 text-white px-6 py-3 rounded-md hover:bg-emerald-700 transition-colors"
            >
              Preparation Guides
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;