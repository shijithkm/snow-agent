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
        </main>
    );
}