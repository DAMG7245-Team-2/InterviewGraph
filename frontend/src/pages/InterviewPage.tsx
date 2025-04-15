import ChatBox from "../components/ChatBox.tsx";

const InterviewPage: React.FC = () => {
    return (
        <div className="p-6">
            <h1 className="text-x1 font-bold mb-4">Interview Agent</h1>
            <ChatBox threadId="interview" />
        </div>
    );
};

export default InterviewPage;