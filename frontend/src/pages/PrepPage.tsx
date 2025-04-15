import PrepForm from "../components/PrepForm.tsx";

const PrepPage: React.FC = () => {
    return (
        <div className="p-6">
            <h1 className="text-x1 font-bold mb-4">Prep Agent</h1>
            <PrepForm />
        </div>
    );
};

export default PrepPage;