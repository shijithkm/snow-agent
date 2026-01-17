"use client";

import { useRouter } from "next/navigation";
import { TicketForm } from "@/components/TicketForm";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

export default function CreateTicketPage() {
    const router = useRouter();

    async function handleSubmit(description: string, alert_id?: string, ticket_type?: string, start_time?: string, end_time?: string) {
        await fetch(API_BASE + "/process_ticket", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ description, alert_id, ticket_type, start_time, end_time })
        });
        router.push("/tickets/list");
    }

    return (
        <main className="space-y-6">
            <h1 className="text-2xl font-bold">Create Ticket</h1>
            <TicketForm onSubmit={handleSubmit} />
        </main>
    );
}
