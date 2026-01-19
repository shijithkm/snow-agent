"use client";

import { TicketForm } from "@/components/TicketForm";
import { TicketList } from "@/components/TicketList";
import { WorkflowAnimation } from "@/components/WorkflowAnimation";
import { useEffect, useState } from "react";


const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

async function fetchTickets() {
    const res = await fetch(API_BASE + "/tickets");
    const data = await res.json();
    return Object.values(data);
}

async function processTicket(description: string, alert_id?: string) {
    const res = await fetch(API_BASE + "/process_ticket", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description, alert_id })
    });
    return res.json();
}

export default function SnowPage() {
    return (
        <main className="space-y-6 sm:space-y-8">
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 pt-2 sm:pt-4">
                <a href="/chat" className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 text-center">
                    💬 Chat with AI
                </a>
                <a href="/tickets/create" className="rounded bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-900 text-center">Create Ticket</a>
                <a href="/tickets/list" className="rounded bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-100 text-center">View Tickets</a>
                <a href="/admin/rag" className="rounded bg-purple-600 px-4 py-2 text-sm font-semibold text-white hover:bg-purple-500 text-center">
                    🔧 Admin: RAG Docs
                </a>
            </div>

            {/* Workflow Animation */}
            <div className="mt-8 sm:mt-12">
                <WorkflowAnimation />
            </div>

            {/* Available Agents Section */}
            <div className="mt-8 sm:mt-12 space-y-4 sm:space-y-6">
                <h2 className="text-xl sm:text-2xl font-bold">Available AI Agents</h2>
                <p className="text-xs sm:text-sm text-slate-300">Our intelligent automation platform provides specialized agents to handle different types of requests:</p>

                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    {/* Ops Agent */}
                    <div className="rounded-lg bg-amber-900 border border-amber-700 p-4 sm:p-6 space-y-3">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl sm:text-3xl">🤖</span>
                            <h3 className="text-base sm:text-lg font-semibold text-amber-300">Ops Agent</h3>
                        </div>
                        <p className="text-xs sm:text-sm text-slate-300">
                            Orchestrates the entire ticket workflow. Routes requests to appropriate agents, coordinates between Info, RAG, and Grafana agents, and ensures smooth ticket resolution.
                        </p>
                        <div className="text-xs text-slate-400">
                            <strong>Handles:</strong> Workflow orchestration, intelligent routing
                        </div>
                    </div>

                    {/* Info Agent */}
                    <div className="rounded-lg bg-cyan-900 border border-cyan-700 p-4 sm:p-6 space-y-3">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl sm:text-3xl">📚</span>
                            <h3 className="text-base sm:text-lg font-semibold text-cyan-300">Info Agent</h3>
                        </div>
                        <p className="text-xs sm:text-sm text-slate-300">
                            Searches Confluence documentation via MCP server. Provides instant answers from official company wikis, policies, and technical documentation.
                        </p>
                        <div className="text-xs text-slate-400">
                            <strong>Handles:</strong> Confluence search, documentation lookup
                        </div>
                    </div>

                    {/* RAG Agent */}
                    <div className="rounded-lg bg-violet-900 border border-violet-700 p-4 sm:p-6 space-y-3">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl sm:text-3xl">🔍</span>
                            <h3 className="text-base sm:text-lg font-semibold text-violet-300">RAG Agent</h3>
                        </div>
                        <p className="text-xs sm:text-sm text-slate-300">
                            Fallback knowledge base search using vector embeddings. Searches trained internal documents when Info Agent doesn't find answers in Confluence.
                        </p>
                        <div className="text-xs text-slate-400">
                            <strong>Handles:</strong> Vector DB search, company knowledge base
                        </div>
                    </div>

                    {/* Grafana Agent */}
                    <div className="rounded-lg bg-blue-900 border border-blue-700 p-4 sm:p-6 space-y-3">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl sm:text-3xl">🔔</span>
                            <h3 className="text-base sm:text-lg font-semibold text-blue-300">Grafana Agent</h3>
                        </div>
                        <p className="text-xs sm:text-sm text-slate-300">
                            Handles alert suppression for RITM tickets. Automatically silences Grafana alerts for specified time windows and manages monitoring alert lifecycle.
                        </p>
                        <div className="text-xs text-slate-400">
                            <strong>Handles:</strong> Alert suppression, monitoring alerts
                        </div>
                    </div>
                </div>

                <div className="rounded-lg bg-blue-950 border border-blue-800 p-3 sm:p-4">
                    <div className="flex items-start gap-2 sm:gap-3">
                        <span className="text-xl sm:text-2xl">💡</span>
                        <div className="space-y-1">
                            <h4 className="text-xs sm:text-sm font-semibold text-blue-200">Smart Routing</h4>
                            <p className="text-xs text-slate-300">
                                Our system automatically routes your ticket to the appropriate agent based on your description and ticket type. For best results, clearly describe your issue or question.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}