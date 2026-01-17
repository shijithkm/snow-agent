"use client";

import { TicketForm } from "@/components/TicketForm";
import { TicketList } from "@/components/TicketList";
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
        <main className="space-y-8">
            <h1 className="text-3xl font-bold">ServiceNow – Ticketing</h1>

            <p className="text-sm text-slate-300">Tickets have been split into separate pages:</p>
            <div className="flex gap-4 pt-4">
                <a href="/tickets/create" className="rounded bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-900">Create Ticket</a>
                <a href="/tickets/list" className="rounded bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-100">View Tickets</a>
            </div>

            {/* Available Agents Section */}
            <div className="mt-12 space-y-6">
                <h2 className="text-2xl font-bold">Available AI Agents</h2>
                <p className="text-sm text-slate-300">Our intelligent automation platform provides specialized agents to handle different types of requests:</p>

                <div className="grid gap-4 md:grid-cols-3">
                    {/* Snow Agent */}
                    <div className="rounded-lg bg-slate-900 border border-slate-800 p-6 space-y-3">
                        <div className="flex items-center gap-3">
                            <span className="text-3xl">🤖</span>
                            <h3 className="text-lg font-semibold text-amber-300">Snow Agent</h3>
                        </div>
                        <p className="text-sm text-slate-300">
                            Automatically handles alert suppression requests. Silences Grafana alerts for specified time windows and manages alert lifecycle. Tickets are auto-closed after suppression is complete.
                        </p>
                        <div className="text-xs text-slate-400">
                            <strong>Handles:</strong> Alert silencing, suppression windows
                        </div>
                    </div>

                    {/* RFI Agent */}
                    <div className="rounded-lg bg-slate-900 border border-slate-800 p-6 space-y-3">
                        <div className="flex items-center gap-3">
                            <span className="text-3xl">🤖</span>
                            <h3 className="text-lg font-semibold text-amber-300">RFI Agent</h3>
                        </div>
                        <p className="text-sm text-slate-300">
                            Performs intelligent web research to answer your questions. Uses advanced search capabilities to find relevant information and provides concise, policy-aligned summaries with source references.
                        </p>
                        <div className="text-xs text-slate-400">
                            <strong>Handles:</strong> Information requests, documentation searches, how-to queries
                        </div>
                    </div>

                    {/* L1 Team */}
                    <div className="rounded-lg bg-slate-900 border border-slate-800 p-6 space-y-3">
                        <div className="flex items-center gap-3">
                            <span className="text-3xl">👤</span>
                            <h3 className="text-lg font-semibold text-slate-200">L1 Support Team</h3>
                        </div>
                        <p className="text-sm text-slate-300">
                            Human support team handles general incidents, technical issues, and requests that require manual intervention. Available for complex problems that need personal attention.
                        </p>
                        <div className="text-xs text-slate-400">
                            <strong>Handles:</strong> General support, incidents, technical issues
                        </div>
                    </div>
                </div>

                <div className="rounded-lg bg-blue-950 border border-blue-800 p-4">
                    <div className="flex items-start gap-3">
                        <span className="text-2xl">💡</span>
                        <div className="space-y-1">
                            <h4 className="text-sm font-semibold text-blue-200">Smart Routing</h4>
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