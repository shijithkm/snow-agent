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
            const ticketList = Object.values(data);
            // Sort tickets in descending order by ticket ID
            ticketList.sort((a: any, b: any) => {
                const aNum = parseInt(a.id.replace(/\D/g, '')) || 0;
                const bNum = parseInt(b.id.replace(/\D/g, '')) || 0;
                return bNum - aNum;
            });
            console.log("Loaded tickets:", ticketList);
            setTickets(ticketList);
        } catch (err) {
            console.error("Error loading tickets:", err);
            setTickets([]);
        }
    }

    useEffect(() => {
        loadTickets();
        // Refresh tickets every 3 seconds to see updates
        const interval = setInterval(loadTickets, 3000);
        return () => clearInterval(interval);
    }, []);

    return (
        <main className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-bold">Tickets</h1>
                <button
                    onClick={loadTickets}
                    className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold hover:bg-blue-500"
                >
                    Refresh
                </button>
            </div>
            <TicketList tickets={tickets} />
        </main>
    );
}
