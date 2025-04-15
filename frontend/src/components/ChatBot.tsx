import { useEffect, useRef, useState } from "react";

interface ChatBoxProps {
    threadId: string;
}

const ChatBox: React.FC<ChatBoxProps> = ({ threadId }) => {
    const [messages, setMessages] = useState<string[]>([]);
    const [input, setInput] = useState("");
    const ws = useRef<WebSocket | null>(null);

    useEffect(() => {
        ws.current = new WebSocket(`ws://localhost:8000/interview/${threadId}`);
        ws.current.onmessage = (event) => {
            setMessages((prev) => [...prev, event.data]);
        };
        return () => {
            ws.current?.close();
        };
    }, [threadId]);

    const sendMessage = () => {
        if (ws.current && input.trim() !== "") {
            ws.current.send(input);
            setMessages((prev) => [...prev, "You: " + input]);
            setInput("");
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
                />
                <button className="bg-blue-500 text-white px-4 rounded-r" onClick={sendMessage}>
                    Send
                </button>
            </div>
        </div>
    );
};

export default ChatBox;