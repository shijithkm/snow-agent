"use client";

import { TicketForm } from "@/components/TicketForm";
import { TicketList } from "@/components/TicketList";
import { useEffect, useState } from "react";


async function fetchTickets() {
    const res = await fetch("/api/tickets");
    const data = await res.json();
    return Object.values(data);
}

async function processTicket(description: string, alert_id?: string) {
    const res = await fetch("/api/process_ticket", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description, alert_id })
    });
    return res.json();
}

export default function SnowPage() {
    const [tickets, setTickets] = useState<any[]>([]);

    async function loadTickets() {
        const t = await fetchTickets();
        setTickets(t as any[]);
    }

    async function handleSubmit(description: string, alert_id?: string) {
        const result = await processTicket(description, alert_id);
        console.log("Result:", result);
        await loadTickets();
    }

    useEffect(() => {
        loadTickets();
    }, []);

    return (
        <main className="space-y-6">
            <h1 className="text-2xl font-bold">ServiceNow – Tickets</h1>
            <p className="text-sm text-slate-300">Ticket UI has moved. Use the links below:</p>
            <div className="flex gap-4 pt-4">
                <a href="/tickets/create" className="rounded bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-900">Create Ticket</a>
                <a href="/tickets/list" className="rounded bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-100">View Tickets</a>
            </div>
        </main>
    );
}