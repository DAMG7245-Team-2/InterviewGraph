import { useState } from "react";

interface ChatBoxProps {
    threadId: string;
}

const ChatBox: React.FC<ChatBoxProps> = ({ threadId }) => {
    const [messages, setMessages] = useState<string[]>([]);
    const [input, setInput] = useState("");

    const sendMessage = () => {
        if (input.trim() !== "") {
            setMessages((prev) => [...prev, "You: " + input]);
            setInput("");
            fetch("http://localhost:8000/interview/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message: input,
                    thread_id: threadId,
                }),
            })
                .then((res) => res.text())
                .then((responseText) => {
                    setMessages((prev) => [...prev, "Agent: " + responseText]);
                })
                .catch((error) => {
                    console.error("Error:", error);
                    setMessages((prev) => [...prev, "Error sending message"]);
                });
        }
    };

    return (
        <div>
            <div className="border h-64 overflow-y-scroll p-2 bg-white rounded shadow">
                {messages.map((msg, i) => (
                    <div key={i} className="text-sm mb-1">{msg}</div>
                ))}
            </div>
            <div className="flex mt-2">
                <input
                    className="border flex-1 px-2 py-1 rounded-1"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                />
                <button className="bg-blue-500 text-white px-4 rounded-r" onClick={sendMessage}>
                    Send
                </button>
            </div>
        </div>
    );
};

export default ChatBox;