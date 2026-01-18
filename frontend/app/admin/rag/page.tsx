"use client";

import { useState, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

interface Document {
    id: string;
    filename: string;
    size: number;
    uploaded_at: string;
    uploaded_by: string;
    status: string;
    trained: boolean;
    chunk_count: number;
    trained_at?: string;
    error?: string;
}

export default function AdminRAGPage() {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [searching, setSearching] = useState(false);

    useEffect(() => {
        fetchDocuments();
    }, []);

    const fetchDocuments = async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_BASE}/documents`);
            const data = await res.json();
            if (data.success) {
                setDocuments(data.documents);
            }
        } catch (error) {
            console.error("Failed to fetch documents:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedFile(e.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        try {
            setUploading(true);
            const formData = new FormData();
            formData.append("file", selectedFile);
            formData.append("uploaded_by", "admin");

            const res = await fetch(`${API_BASE}/documents/upload`, {
                method: "POST",
                body: formData,
            });

            const data = await res.json();
            if (data.success) {
                alert("Document uploaded successfully!");
                setSelectedFile(null);
                fetchDocuments();
            } else {
                alert("Upload failed: " + (data.detail || "Unknown error"));
            }
        } catch (error) {
            console.error("Upload failed:", error);
            alert("Upload failed: " + error);
        } finally {
            setUploading(false);
        }
    };

    const handleTrain = async (docId: string) => {
        if (!confirm("Train this document? This will process and add it to the RAG database.")) {
            return;
        }

        try {
            const res = await fetch(`${API_BASE}/documents/${docId}/train`, {
                method: "POST",
            });

            const data = await res.json();
            if (data.success) {
                alert("Document trained successfully!");
                fetchDocuments();
            } else {
                alert("Training failed: " + (data.detail || "Unknown error"));
            }
        } catch (error) {
            console.error("Training failed:", error);
            alert("Training failed: " + error);
        }
    };

    const handleDelete = async (docId: string) => {
        if (!confirm("Delete this document? This action cannot be undone.")) {
            return;
        }

        try {
            const res = await fetch(`${API_BASE}/documents/${docId}`, {
                method: "DELETE",
            });

            const data = await res.json();
            if (data.success) {
                alert("Document deleted successfully!");
                fetchDocuments();
            } else {
                alert("Deletion failed: " + (data.detail || "Unknown error"));
            }
        } catch (error) {
            console.error("Deletion failed:", error);
            alert("Deletion failed: " + error);
        }
    };

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;

        try {
            setSearching(true);
            const formData = new FormData();
            formData.append("query", searchQuery);
            formData.append("k", "5");

            const res = await fetch(`${API_BASE}/documents/search`, {
                method: "POST",
                body: formData,
            });

            const data = await res.json();
            if (data.success) {
                setSearchResults(data.results);
            }
        } catch (error) {
            console.error("Search failed:", error);
        } finally {
            setSearching(false);
        }
    };

    const formatBytes = (bytes: number) => {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const sizes = ["Bytes", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString();
    };

    return (
        <main className="space-y-6 sm:space-y-8">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl sm:text-3xl font-bold">RAG Document Management</h1>
                <a
                    href="/"
                    className="text-sm text-blue-400 hover:text-blue-300"
                >
                    ← Back to Home
                </a>
            </div>

            <p className="text-sm text-slate-300">
                Upload and manage company documents for the RAG Agent. Supported formats: PDF, MD, TXT, DOC, DOCX
            </p>

            {/* Upload Section */}
            <div className="rounded-lg bg-slate-900 border border-slate-800 p-6 space-y-4">
                <h2 className="text-xl font-semibold text-amber-300">📤 Upload Document</h2>

                <div className="flex flex-col sm:flex-row gap-4">
                    <div className="flex-1">
                        <input
                            type="file"
                            accept=".pdf,.md,.txt,.doc,.docx"
                            onChange={handleFileSelect}
                            className="w-full px-4 py-2 rounded bg-slate-800 border border-slate-700 text-white text-sm"
                        />
                        {selectedFile && (
                            <p className="mt-2 text-xs text-slate-400">
                                Selected: {selectedFile.name} ({formatBytes(selectedFile.size)})
                            </p>
                        )}
                    </div>

                    <button
                        onClick={handleUpload}
                        disabled={!selectedFile || uploading}
                        className="px-6 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold text-sm"
                    >
                        {uploading ? "Uploading..." : "Upload"}
                    </button>
                </div>
            </div>

            {/* Search Section */}
            <div className="rounded-lg bg-slate-900 border border-slate-800 p-6 space-y-4">
                <h2 className="text-xl font-semibold text-purple-300">🔍 Test Search</h2>

                <div className="flex flex-col sm:flex-row gap-4">
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                        placeholder="Enter search query..."
                        className="flex-1 px-4 py-2 rounded bg-slate-800 border border-slate-700 text-white text-sm"
                    />
                    <button
                        onClick={handleSearch}
                        disabled={!searchQuery.trim() || searching}
                        className="px-6 py-2 rounded bg-purple-600 hover:bg-purple-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold text-sm"
                    >
                        {searching ? "Searching..." : "Search"}
                    </button>
                </div>

                {searchResults.length > 0 && (
                    <div className="mt-4 space-y-3">
                        <h3 className="text-sm font-semibold text-slate-300">Results:</h3>
                        {searchResults.map((result, idx) => (
                            <div key={idx} className="rounded bg-slate-800 p-4 space-y-2">
                                <div className="flex items-center justify-between">
                                    <span className="text-xs font-semibold text-purple-300">
                                        {result.metadata.filename}
                                    </span>
                                    <span className="text-xs text-slate-400">
                                        Score: {result.score.toFixed(3)}
                                    </span>
                                </div>
                                <p className="text-xs text-slate-300">{result.content.substring(0, 200)}...</p>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Documents List */}
            <div className="rounded-lg bg-slate-900 border border-slate-800 p-6 space-y-4">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold text-emerald-300">📚 Documents</h2>
                    <button
                        onClick={fetchDocuments}
                        className="text-sm text-blue-400 hover:text-blue-300"
                    >
                        🔄 Refresh
                    </button>
                </div>

                {loading ? (
                    <p className="text-sm text-slate-400">Loading documents...</p>
                ) : documents.length === 0 ? (
                    <p className="text-sm text-slate-400">No documents uploaded yet.</p>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="border-b border-slate-700">
                                <tr className="text-left">
                                    <th className="pb-3 font-semibold text-slate-300">Filename</th>
                                    <th className="pb-3 font-semibold text-slate-300">Size</th>
                                    <th className="pb-3 font-semibold text-slate-300">Status</th>
                                    <th className="pb-3 font-semibold text-slate-300">Chunks</th>
                                    <th className="pb-3 font-semibold text-slate-300">Uploaded</th>
                                    <th className="pb-3 font-semibold text-slate-300">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {documents.map((doc) => (
                                    <tr key={doc.id} className="hover:bg-slate-800/50">
                                        <td className="py-3 text-slate-200">{doc.filename}</td>
                                        <td className="py-3 text-slate-400">{formatBytes(doc.size)}</td>
                                        <td className="py-3">
                                            <span
                                                className={`px-2 py-1 rounded text-xs font-semibold ${doc.trained
                                                        ? "bg-green-900 text-green-300"
                                                        : doc.status === "training"
                                                            ? "bg-yellow-900 text-yellow-300"
                                                            : doc.status === "error"
                                                                ? "bg-red-900 text-red-300"
                                                                : "bg-slate-700 text-slate-300"
                                                    }`}
                                            >
                                                {doc.trained ? "Trained" : doc.status}
                                            </span>
                                        </td>
                                        <td className="py-3 text-slate-400">
                                            {doc.trained ? doc.chunk_count : "-"}
                                        </td>
                                        <td className="py-3 text-slate-400 text-xs">
                                            {formatDate(doc.uploaded_at)}
                                        </td>
                                        <td className="py-3 space-x-2">
                                            {!doc.trained && doc.status !== "training" && (
                                                <button
                                                    onClick={() => handleTrain(doc.id)}
                                                    className="px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold"
                                                >
                                                    Train
                                                </button>
                                            )}
                                            <button
                                                onClick={() => handleDelete(doc.id)}
                                                className="px-3 py-1 rounded bg-red-600 hover:bg-red-500 text-white text-xs font-semibold"
                                            >
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Info Section */}
            <div className="rounded-lg bg-blue-950 border border-blue-800 p-4">
                <h3 className="text-sm font-semibold text-blue-200 mb-2">ℹ️ How it works</h3>
                <ul className="text-xs text-slate-300 space-y-1">
                    <li>1. <strong>Upload</strong> company documents (policies, guides, etc.)</li>
                    <li>2. <strong>Train</strong> documents to process and add to vector database</li>
                    <li>3. <strong>RAG Agent</strong> automatically searches these documents when users ask RFI questions</li>
                    <li>4. If RAG Agent finds relevant info, it answers immediately. Otherwise, falls back to web search (RFI Agent)</li>
                </ul>
            </div>
        </main>
    );
}
