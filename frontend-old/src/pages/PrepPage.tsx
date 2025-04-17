import PrepForm from "../components/PrepForm";

const PrepPage: React.FC = () => {
    return (
        <div className="min-h-screen w-full max-w-full bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900">
            <div className="w-full px-4 py-8">
                <h1 className="centered text-4xl font-bold text-emerald-500 mb-6">Prep Agent</h1>
                <div className="bg-gray-800 rounded-lg shadow-xl p-6 mb-8">
                    <PrepForm />
                </div>
            </div>
        </div>
    );
};

export default PrepPage;