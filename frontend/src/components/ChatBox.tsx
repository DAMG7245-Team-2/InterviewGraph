import { useState, useRef, useEffect } from "react";

interface ChatBoxProps {
    threadId: string;
}

interface ChatMessage {
    role: "user" | "agent" | "error";
    content: string;
}

const ChatBox: React.FC<ChatBoxProps> = ({ threadId }) => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const sendMessage = async () => {
        const trimmed = input.trim();
        if (!trimmed || loading) return;

        const userMessage: ChatMessage = { role: "user", content: trimmed };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setLoading(true);

        try {
            const res = await fetch("http://localhost:8000/interview/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message: trimmed,
                    thread_id: threadId,
                }),
            });

            const text = await res.text();

            setMessages((prev) => [
                ...prev,
                { role: "agent", content: text },
            ]);
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                { role: "error", content: "Failed to connect to assistant." },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter") {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <div className="flex flex-col w-full max-w-2xl mx-auto h-[600px] border rounded-lg shadow bg-white overflow-hidden">
            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                {messages.map((msg, i) => (
                    <div
                        key={i}
                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                        <div
                            className={`max-w-xs px-4 py-2 rounded-lg text-sm ${
                                msg.role === "user"
                                    ? "bg-blue-500 text-white rounded-br-none"
                                    : msg.role === "agent"
                                    ? "bg-gray-200 text-gray-800 rounded-bl-none"
                                    : "bg-red-100 text-red-600"
                            }`}
                        >
                            {msg.content}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="flex justify-start">
                        <div className="text-sm text-gray-500 italic">Agent is typing...</div>
                    </div>
                )}

                <div ref={bottomRef} />
            </div>

            {/* Input Bar */}
            <div className="border-t p-3 bg-white flex">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Send a message..."
                    className="flex-1 px-3 py-2 border rounded-l focus:outline-none"
                    disabled={loading}
                />
                <button
                    onClick={sendMessage}
                    disabled={loading || !input.trim()}
                    className="bg-blue-500 text-white px-4 rounded-r hover:bg-blue-600 disabled:opacity-50"
                >
                    Send
                </button>
            </div>
        </div>
    );
};

export default ChatBox;