/**
 * ChatWidget — Floating AI chatbot with streaming responses.
 * Renders as a floating bubble in bottom-right corner.
 */

import { useState, useRef, useEffect, useCallback } from "react";
import { useAuth } from "./AuthContext";
import { chat as chatApi } from "./api";
import { MessageCircle, X, Send, Trash2, Plus, LogOut, Settings } from "lucide-react";
import { marked } from "marked";

// Configure marked for safe rendering
marked.setOptions({ breaks: true, gfm: true });

export default function ChatWidget() {
  const { user, logout, isAdmin } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [showSessionList, setShowSessionList] = useState(false);

  const messagesEndRef = useRef(null);
  const abortRef = useRef(null);

  // ─── Load sessions on mount ───
  useEffect(() => {
    if (isOpen) loadSessions();
  }, [isOpen]);

  // ─── Scroll to bottom ───
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadSessions = async () => {
    try {
      const data = await chatApi.listSessions();
      setSessions(data);
    } catch (err) {
      console.error("Failed to load sessions:", err);
    }
  };

  const loadMessages = async (sessionId) => {
    try {
      const data = await chatApi.getMessages(sessionId);
      setMessages(data);
      setActiveSession(sessionId);
      setShowSessionList(false);
    } catch (err) {
      console.error("Failed to load messages:", err);
    }
  };

  const startNewChat = () => {
    setActiveSession(null);
    setMessages([]);
    setShowSessionList(false);
  };

  const deleteSession = async (e, sessionId) => {
    e.stopPropagation();
    try {
      await chatApi.deleteSession(sessionId);
      if (activeSession === sessionId) {
        setActiveSession(null);
        setMessages([]);
      }
      loadSessions();
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  };

  // ─── Send message with streaming ───
  const sendMessage = useCallback(async () => {
    if (!input.trim() || isStreaming) return;

    const userMsg = input.trim();
    setInput("");

    // Add user message to UI immediately
    setMessages((prev) => [...prev, { role: "user", message: userMsg, created_at: new Date().toISOString() }]);

    // Add placeholder for assistant
    setMessages((prev) => [...prev, { role: "assistant", message: "", created_at: new Date().toISOString(), streaming: true }]);
    setIsStreaming(true);

    let fullResponse = "";
    let newSessionId = activeSession;

    const controller = chatApi.queryStream(userMsg, activeSession || undefined, {
      onToken: (token) => {
        fullResponse += token;
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            message: fullResponse,
          };
          return updated;
        });
      },
      onDone: (metadata) => {
        setIsStreaming(false);
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            message: fullResponse,
            streaming: false,
            response_time: metadata.response_time,
          };
          return updated;
        });
        if (metadata.session_id) {
          setActiveSession(metadata.session_id);
        }
        loadSessions();
      },
      onError: (err) => {
        setIsStreaming(false);
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            message: `Error: ${err.message}`,
            streaming: false,
            error: true,
          };
          return updated;
        });
      },
    });

    abortRef.current = controller;
  }, [input, isStreaming, activeSession]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const stopStreaming = () => {
    if (abortRef.current) {
      abortRef.current.abort();
      setIsStreaming(false);
    }
  };

  // ─── Render markdown content ───
  const renderMessage = (msg) => {
    if (msg.role === "user") {
      return <p className="whitespace-pre-wrap">{msg.message}</p>;
    }
    // Render assistant messages as markdown
    try {
      const html = marked.parse(msg.message || "");
      return <div className="prose prose-sm max-w-none prose-invert" dangerouslySetInnerHTML={{ __html: html }} />;
    } catch {
      return <p className="whitespace-pre-wrap">{msg.message}</p>;
    }
  };

  return (
    <>
      {/* ─── Floating Button ─── */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-2xl transition-all duration-300 hover:scale-105"
        >
          <MessageCircle size={28} />
        </button>
      )}

      {/* ─── Chat Window ─── */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-[420px] h-[600px] bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
          {/* ─── Header ─── */}
          <div className="bg-blue-600 px-4 py-3 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2">
              <MessageCircle size={20} className="text-white" />
              <span className="text-white font-semibold">AI Assistant</span>
            </div>
            <div className="flex items-center gap-2">
              {isAdmin && (
                <a href="/admin" className="text-white/70 hover:text-white" title="Admin Dashboard">
                  <Settings size={18} />
                </a>
              )}
              {user && (
                <button onClick={logout} className="text-white/70 hover:text-white" title="Logout">
                  <LogOut size={18} />
                </button>
              )}
              <button onClick={() => setIsOpen(false)} className="text-white/70 hover:text-white">
                <X size={20} />
              </button>
            </div>
          </div>

          {/* ─── Session Tabs ─── */}
          <div className="bg-gray-800 px-3 py-2 flex items-center gap-2 flex-shrink-0 border-b border-gray-700">
            <button
              onClick={startNewChat}
              className="flex items-center gap-1 text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg transition-colors"
            >
              <Plus size={14} /> New Chat
            </button>
            <button
              onClick={() => setShowSessionList(!showSessionList)}
              className="text-xs text-gray-400 hover:text-white px-2 py-1.5 transition-colors"
            >
              History ({sessions.length})
            </button>
          </div>

          {/* ─── Session List Dropdown ─── */}
          {showSessionList && (
            <div className="bg-gray-800 border-b border-gray-700 max-h-40 overflow-y-auto flex-shrink-0">
              {sessions.length === 0 ? (
                <p className="text-gray-500 text-xs px-4 py-3">No previous chats</p>
              ) : (
                sessions.map((s) => (
                  <div
                    key={s.id}
                    onClick={() => loadMessages(s.id)}
                    className={`flex items-center justify-between px-4 py-2 cursor-pointer hover:bg-gray-700 transition-colors ${
                      activeSession === s.id ? "bg-gray-700" : ""
                    }`}
                  >
                    <span className="text-sm text-gray-300 truncate flex-1">{s.title}</span>
                    <button
                      onClick={(e) => deleteSession(e, s.id)}
                      className="text-gray-500 hover:text-red-400 ml-2 flex-shrink-0"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))
              )}
            </div>
          )}

          {/* ─── Messages Area ─── */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 mt-12">
                <MessageCircle size={48} className="mx-auto mb-3 opacity-30" />
                <p className="text-sm">Ask me anything about system design,</p>
                <p className="text-sm">FAQs, or how to navigate the app.</p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white rounded-br-md"
                      : msg.error
                      ? "bg-red-900/50 text-red-300 rounded-bl-md"
                      : "bg-gray-800 text-gray-200 rounded-bl-md"
                  }`}
                >
                  {renderMessage(msg)}
                  {msg.streaming && (
                    <span className="inline-block w-2 h-4 bg-blue-400 animate-pulse ml-1" />
                  )}
                  {!msg.streaming && msg.response_time && (
                    <p className="text-[10px] text-gray-500 mt-1">{msg.response_time}s</p>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* ─── Input Area ─── */}
          <div className="bg-gray-800 px-4 py-3 border-t border-gray-700 flex-shrink-0">
            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your question..."
                rows={1}
                className="flex-1 bg-gray-700 text-white rounded-xl px-4 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400"
                disabled={isStreaming}
              />
              {isStreaming ? (
                <button
                  onClick={stopStreaming}
                  className="bg-red-600 hover:bg-red-700 text-white rounded-xl p-2.5 transition-colors"
                >
                  <X size={20} />
                </button>
              ) : (
                <button
                  onClick={sendMessage}
                  disabled={!input.trim()}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-xl p-2.5 transition-colors"
                >
                  <Send size={20} />
                </button>
              )}
            </div>
            <p className="text-[10px] text-gray-500 mt-1.5 text-center">
              Powered by Ollama (on-premises) {user ? `· ${user.username}` : ""}
            </p>
          </div>
        </div>
      )}
    </>
  );
}
