"use client";

import { useEffect, useState } from "react";
import { TicketList } from "@/components/TicketList";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

export default function TicketsListPage() {
    const [tickets, setTickets] = useState<any[]>([]);

    async function loadTickets() {
        try {
            const res = await fetch(API_BASE + "/tickets");
            const data = await res.json();
            setTickets(Object.values(data));
        } catch (err) {
            setTickets([]);
        }
    }

    useEffect(() => {
        loadTickets();
    }, []);

    return (
        <main className="space-y-6">
            <h1 className="text-2xl font-bold">Tickets</h1>
            <TicketList tickets={tickets} />
        </main>
    );
}
