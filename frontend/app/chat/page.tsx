"use client";

import { useState, useEffect, useRef } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

interface Message {
    role: "user" | "assistant";
    content: string;
}

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [sessionId] = useState(() => `session_${Date.now()}`);
    const [ticketCreated, setTicketCreated] = useState(false);
    const [ticketId, setTicketId] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        // Start chat session
        startChat();
    }, []);

    async function startChat() {
        setLoading(true);
        try {
            const res = await fetch(API_BASE + "/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    action: "start"
                })
            });
            const data = await res.json();
            setMessages(data.messages || []);
        } catch (err) {
            console.error("Failed to start chat:", err);
        } finally {
            setLoading(false);
        }
    }

    async function sendMessage() {
        if (!input.trim() || loading) return;

        const userMessage = input.trim();
        setInput("");
        setLoading(true);

        // Add user message optimistically
        setMessages(prev => [...prev, { role: "user", content: userMessage }]);

        try {
            const res = await fetch(API_BASE + "/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: userMessage,
                    action: "continue"
                })
            });
            const data = await res.json();

            // Update with server response
            setMessages(data.messages || []);
            setTicketCreated(data.ticket_created || false);
            setTicketId(data.ticket_id || null);
        } catch (err) {
            console.error("Failed to send message:", err);
            setMessages(prev => [
                ...prev,
                { role: "assistant", content: "Sorry, I encountered an error. Please try again." }
            ]);
        } finally {
            setLoading(false);
            // Focus back on input after sending
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }

    async function resetChat() {
        setLoading(true);
        try {
            const res = await fetch(API_BASE + "/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    action: "reset"
                })
            });
            const data = await res.json();
            setMessages(data.messages || []);
            setTicketCreated(false);
            setTicketId(null);
        } catch (err) {
            console.error("Failed to reset chat:", err);
        } finally {
            setLoading(false);
        }
    }

    return (
        <main className="flex flex-col h-[calc(100vh-10rem)] sm:h-[calc(100vh-8rem)]">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-2">
                <div>
                    <h1 className="text-xl sm:text-2xl font-bold">Ops AI Chatbot</h1>
                    <p className="text-sm text-slate-400">Create tickets through natural conversation</p>
                </div>
                <button
                    onClick={resetChat}
                    className="rounded bg-slate-800 px-3 sm:px-4 py-2 text-xs sm:text-sm font-semibold hover:bg-slate-700 whitespace-nowrap"
                    disabled={loading}
                >
                    Reset Chat
                </button>
            </div>

            {ticketCreated && ticketId && (
                <div className="mb-4 rounded-lg bg-emerald-900/20 border border-emerald-800 p-4">
                    <div className="flex items-center gap-2">
                        <span className="text-2xl">✅</span>
                        <div>
                            <div className="font-semibold text-emerald-300">Ticket Created!</div>
                            <div className="text-sm text-slate-300">
                                Ticket {ticketId} has been created and is being processed.
                                <a href="/tickets/list" className="ml-2 text-emerald-400 hover:underline">
                                    View Tickets
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto rounded-lg bg-slate-900 border border-slate-800 p-2 sm:p-4 space-y-4">
                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                        <div
                            className={`max-w-[85%] sm:max-w-[80%] rounded-lg p-2 sm:p-3 ${msg.role === "user"
                                ? "bg-blue-600 text-white"
                                : "bg-slate-800 text-slate-100"
                                }`}
                        >
                            {msg.role === "assistant" && (
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-lg">🤖</span>
                                    <span className="text-xs font-semibold text-slate-400">Ops Agent</span>
                                </div>
                            )}
                            <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-800 rounded-lg p-3">
                            <div className="flex items-center gap-2">
                                <div className="animate-pulse">🤖</div>
                                <span className="text-sm text-slate-400">Thinking...</span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="mt-4 flex gap-2">
                <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && sendMessage()}
                    placeholder="Type your message..."
                    className="flex-1 rounded-lg bg-slate-900 border border-slate-800 px-3 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={loading}
                    autoFocus
                />
                <button
                    onClick={sendMessage}
                    disabled={loading || !input.trim()}
                    className="rounded-lg bg-blue-600 px-4 sm:px-6 py-2 sm:py-3 text-xs sm:text-sm font-semibold hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                >
                    Send
                </button>
            </div>
        </main>
    );
}