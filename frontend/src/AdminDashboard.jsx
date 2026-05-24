/**
 * Admin Dashboard — Tabs for managing PDFs, FAQs, Navigation, Chat Logs, AI Config.
 */

import { useState, useEffect } from "react";
import { useAuth } from "./AuthContext";
import { documents, faqs, navigation, chatLogs, aiConfig } from "./api";
import {
  FileUp, HelpCircle, Compass, MessageSquare, Cpu, Trash2,
  Edit3, Plus, Save, X, Upload, ArrowLeft, Loader2
} from "lucide-react";

const TABS = [
  { key: "documents", label: "Knowledge Base", icon: FileUp },
  { key: "faqs", label: "FAQs", icon: HelpCircle },
  { key: "navigation", label: "Navigation", icon: Compass },
  { key: "chatlogs", label: "Chat Logs", icon: MessageSquare },
  { key: "aiconfig", label: "AI Config", icon: Cpu },
];

export default function AdminDashboard() {
  const { isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState("documents");

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg">Access Denied</p>
          <p className="text-gray-500 mt-2">You need admin privileges to access this page.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <a href="/" className="text-gray-400 hover:text-white transition-colors">
              <ArrowLeft size={20} />
            </a>
            <h1 className="text-xl font-bold text-white">Admin Dashboard</h1>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-gray-900 border-b border-gray-800 px-6">
        <div className="max-w-6xl mx-auto flex gap-1 overflow-x-auto">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === tab.key
                    ? "border-blue-500 text-blue-400"
                    : "border-transparent text-gray-400 hover:text-gray-300"
                }`}
              >
                <Icon size={16} />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 py-6">
        {activeTab === "documents" && <DocumentsTab />}
        {activeTab === "faqs" && <FAQsTab />}
        {activeTab === "navigation" && <NavigationTab />}
        {activeTab === "chatlogs" && <ChatLogsTab />}
        {activeTab === "aiconfig" && <AIConfigTab />}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════
//  Documents Tab
// ═══════════════════════════════════════════

function DocumentsTab() {
  const [docs, setDocs] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadDocs(); }, []);

  const loadDocs = async () => {
    try {
      const data = await documents.list();
      setDocs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      await documents.upload(file, file.name.replace(/\.pdf$/i, ""));
      loadDocs();
    } catch (err) {
      alert("Upload failed: " + err.message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this document and all its chunks?")) return;
    try {
      await documents.delete(id);
      loadDocs();
    } catch (err) {
      alert("Delete failed: " + err.message);
    }
  };

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white">Knowledge Base</h2>
        <label className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg cursor-pointer transition-colors text-sm">
          <Upload size={16} />
          {uploading ? "Processing..." : "Upload PDF"}
          <input type="file" accept=".pdf" onChange={handleUpload} className="hidden" disabled={uploading} />
        </label>
      </div>

      {docs.length === 0 ? (
        <EmptyState message="No documents uploaded yet" />
      ) : (
        <div className="grid gap-3">
          {docs.map((doc) => (
            <div key={doc.id} className="bg-gray-900 border border-gray-800 rounded-xl px-5 py-4 flex items-center justify-between">
              <div>
                <p className="text-white font-medium">{doc.title}</p>
                <p className="text-gray-500 text-sm mt-1">
                  {doc.chunk_count} chunks &middot; Uploaded {new Date(doc.created_at).toLocaleDateString()}
                  {doc.uploaded_by_name && ` by ${doc.uploaded_by_name}`}
                </p>
              </div>
              <button onClick={() => handleDelete(doc.id)} className="text-gray-500 hover:text-red-400 transition-colors">
                <Trash2 size={18} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════
//  FAQs Tab
// ═══════════════════════════════════════════

function FAQsTab() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // null or FAQ id
  const [form, setForm] = useState({ question: "", answer: "", category: "General" });
  const [showForm, setShowForm] = useState(false);

  useEffect(() => { loadFAQs(); }, []);

  const loadFAQs = async () => {
    try {
      const data = await faqs.list();
      setItems(data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const startEdit = (faq) => {
    setForm({ question: faq.question, answer: faq.answer, category: faq.category });
    setEditing(faq.id);
    setShowForm(true);
  };

  const startNew = () => {
    setForm({ question: "", answer: "", category: "General" });
    setEditing(null);
    setShowForm(true);
  };

  const handleSave = async () => {
    try {
      if (editing) {
        await faqs.update(editing, form);
      } else {
        await faqs.create(form);
      }
      loadFAQs();
      setShowForm(false);
      setEditing(null);
    } catch (err) {
      alert("Save failed: " + err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this FAQ?")) return;
    try {
      await faqs.delete(id);
      loadFAQs();
    } catch (err) { alert("Delete failed: " + err.message); }
  };

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white">FAQs</h2>
        <button onClick={startNew} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
          <Plus size={16} /> Add FAQ
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-4">
          <h3 className="text-white font-medium mb-3">{editing ? "Edit FAQ" : "New FAQ"}</h3>
          <div className="space-y-3">
            <input
              value={form.question} onChange={(e) => setForm({ ...form, question: e.target.value })}
              placeholder="Question" className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <textarea
              value={form.answer} onChange={(e) => setForm({ ...form, answer: e.target.value })}
              placeholder="Answer" rows={3} className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <input
              value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
              placeholder="Category" className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex gap-2">
              <button onClick={handleSave} className="flex items-center gap-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                <Save size={14} /> Save
              </button>
              <button onClick={() => { setShowForm(false); setEditing(null); }} className="flex items-center gap-1 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                <X size={14} /> Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {items.length === 0 && !showForm ? (
        <EmptyState message="No FAQs yet" />
      ) : (
        <div className="space-y-2">
          {items.map((faq) => (
            <div key={faq.id} className="bg-gray-900 border border-gray-800 rounded-xl px-5 py-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <span className="text-xs bg-blue-900/50 text-blue-300 px-2 py-0.5 rounded-full">{faq.category}</span>
                  <p className="text-white mt-2 text-sm font-medium">{faq.question}</p>
                  <p className="text-gray-400 mt-1 text-sm">{faq.answer}</p>
                </div>
                <div className="flex gap-2 ml-3 flex-shrink-0">
                  <button onClick={() => startEdit(faq)} className="text-gray-500 hover:text-blue-400 transition-colors">
                    <Edit3 size={16} />
                  </button>
                  <button onClick={() => handleDelete(faq.id)} className="text-gray-500 hover:text-red-400 transition-colors">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════
//  Navigation Tab
// ═══════════════════════════════════════════

function NavigationTab() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ intent: "", question: "", answer: "" });
  const [showForm, setShowForm] = useState(false);

  useEffect(() => { loadNav(); }, []);

  const loadNav = async () => {
    try {
      const data = await navigation.list();
      setItems(data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const startEdit = (item) => {
    setForm({ intent: item.intent, question: item.question, answer: item.answer });
    setEditing(item.id);
    setShowForm(true);
  };

  const startNew = () => {
    setForm({ intent: "", question: "", answer: "" });
    setEditing(null);
    setShowForm(true);
  };

  const handleSave = async () => {
    try {
      if (editing) {
        await navigation.update(editing, form);
      } else {
        await navigation.create(form);
      }
      loadNav();
      setShowForm(false);
      setEditing(null);
    } catch (err) {
      alert("Save failed: " + err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this navigation guide?")) return;
    try {
      await navigation.delete(id);
      loadNav();
    } catch (err) { alert("Delete failed: " + err.message); }
  };

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white">Navigation Guides</h2>
        <button onClick={startNew} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
          <Plus size={16} /> Add Guide
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-4">
          <h3 className="text-white font-medium mb-3">{editing ? "Edit Guide" : "New Guide"}</h3>
          <div className="space-y-3">
            <input
              value={form.intent} onChange={(e) => setForm({ ...form, intent: e.target.value })}
              placeholder="Intent (e.g., create_project)" className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              value={form.question} onChange={(e) => setForm({ ...form, question: e.target.value })}
              placeholder="User question (e.g., How do I create a project?)" className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <textarea
              value={form.answer} onChange={(e) => setForm({ ...form, answer: e.target.value })}
              placeholder="Navigation steps" rows={2} className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <div className="flex gap-2">
              <button onClick={handleSave} className="flex items-center gap-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                <Save size={14} /> Save
              </button>
              <button onClick={() => { setShowForm(false); setEditing(null); }} className="flex items-center gap-1 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                <X size={14} /> Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {items.length === 0 && !showForm ? (
        <EmptyState message="No navigation guides yet" />
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <div key={item.id} className="bg-gray-900 border border-gray-800 rounded-xl px-5 py-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <span className="text-xs bg-purple-900/50 text-purple-300 px-2 py-0.5 rounded-full">{item.intent}</span>
                  <p className="text-white mt-2 text-sm font-medium">{item.question}</p>
                  <p className="text-gray-400 mt-1 text-sm">{item.answer}</p>
                </div>
                <div className="flex gap-2 ml-3 flex-shrink-0">
                  <button onClick={() => startEdit(item)} className="text-gray-500 hover:text-blue-400 transition-colors">
                    <Edit3 size={16} />
                  </button>
                  <button onClick={() => handleDelete(item.id)} className="text-gray-500 hover:text-red-400 transition-colors">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════
//  Chat Logs Tab
// ═══════════════════════════════════════════

function ChatLogsTab() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedSession, setExpandedSession] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await chatLogs.list();
        setLogs(data);
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <Spinner />;

  return (
    <div>
      <h2 className="text-lg font-semibold text-white mb-6">Chat Logs</h2>
      {logs.length === 0 ? (
        <EmptyState message="No chat logs yet" />
      ) : (
        <div className="space-y-2">
          {logs.map((log) => (
            <div key={log.session.id} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              <button
                onClick={() => setExpandedSession(expandedSession === log.session.id ? null : log.session.id)}
                className="w-full px-5 py-3 flex items-center justify-between hover:bg-gray-800 transition-colors"
              >
                <div className="text-left">
                  <p className="text-white text-sm font-medium">{log.session.title}</p>
                  <p className="text-gray-500 text-xs mt-0.5">
                    User: {log.user} &middot; {log.messages.length} messages &middot; {new Date(log.session.started_at).toLocaleString()}
                  </p>
                </div>
                <span className="text-gray-500">{expandedSession === log.session.id ? "▲" : "▼"}</span>
              </button>

              {expandedSession === log.session.id && (
                <div className="border-t border-gray-800 px-5 py-3 space-y-2 max-h-80 overflow-y-auto">
                  {log.messages.map((msg) => (
                    <div key={msg.id} className={`text-sm ${msg.role === "user" ? "text-blue-300" : "text-gray-300"}`}>
                      <span className={`font-medium ${msg.role === "user" ? "text-blue-400" : "text-green-400"}`}>
                        {msg.role === "user" ? "User" : "AI"}:
                      </span>{" "}
                      {msg.message}
                      {msg.response_time && (
                        <span className="text-gray-600 text-xs ml-2">({msg.response_time}s)</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════
//  AI Config Tab
// ═══════════════════════════════════════════

function AIConfigTab() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({});

  useEffect(() => {
    (async () => {
      try {
        const data = await aiConfig.get();
        setConfig(data);
        setForm({
          provider_name: data.provider_name,
          api_base_url: data.api_base_url,
          model_name: data.model_name,
          api_key: "",
          temperature: data.temperature,
          max_tokens: data.max_tokens,
          embedding_model: data.embedding_model,
        });
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    })();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = { ...form };
      if (!payload.api_key) delete payload.api_key;
      await aiConfig.update(payload);
      alert("Configuration saved successfully!");
    } catch (err) {
      alert("Save failed: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Spinner />;
  if (!config) return <EmptyState message="Could not load AI configuration" />;

  return (
    <div>
      <h2 className="text-lg font-semibold text-white mb-6">AI Configuration</h2>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 max-w-2xl space-y-4">
        <ConfigField label="Provider Name" value={form.provider_name} onChange={(v) => setForm({ ...form, provider_name: v })} />
        <ConfigField label="API Base URL" value={form.api_base_url} onChange={(v) => setForm({ ...form, api_base_url: v })} />
        <ConfigField label="LLM Model" value={form.model_name} onChange={(v) => setForm({ ...form, model_name: v })} hint="Must be pulled in Ollama (e.g., llama3.2, mistral, phi3)" />
        <ConfigField label="API Key" value={form.api_key || ""} onChange={(v) => setForm({ ...form, api_key: v })} type="password" hint="Optional for Ollama. Leave blank if not needed." />
        <ConfigField label="Temperature" value={String(form.temperature)} onChange={(v) => setForm({ ...form, temperature: parseFloat(v) || 0.7 })} hint="0.0 (deterministic) to 1.0 (creative)" />
        <ConfigField label="Max Tokens" value={String(form.max_tokens)} onChange={(v) => setForm({ ...form, max_tokens: parseInt(v) || 2048 })} />
        <ConfigField label="Embedding Model" value={form.embedding_model} onChange={(v) => setForm({ ...form, embedding_model: v })} hint="Must be pulled in Ollama (e.g., nomic-embed-text)" />

        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-6 py-2.5 rounded-lg text-sm transition-colors mt-4"
        >
          {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
          {saving ? "Saving..." : "Save Configuration"}
        </button>
      </div>
    </div>
  );
}

// ─── Shared UI Components ───

function ConfigField({ label, value, onChange, type = "text", hint }) {
  return (
    <div>
      <label className="text-gray-300 text-sm block mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      {hint && <p className="text-gray-500 text-xs mt-1">{hint}</p>}
    </div>
  );
}

function EmptyState({ message }) {
  return (
    <div className="text-center py-12 text-gray-500">
      <p>{message}</p>
    </div>
  );
}

function Spinner() {
  return (
    <div className="flex justify-center py-12">
      <Loader2 size={32} className="animate-spin text-blue-500" />
    </div>
  );
}
