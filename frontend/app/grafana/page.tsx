"use client";

import { AlertList } from "@/components/AlertList";
import { useEffect, useState } from "react";


const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

async function fetchAlerts() {
    const res = await fetch(API_BASE + "/alerts");
    return res.json();
}

async function processTicket(description: string, alert_id: string) {
    const res = await fetch(API_BASE + "/process_ticket", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description, alert_id })
    });
    return res.json();
}

export default function GrafanaPage() {
    const [alerts, setAlerts] = useState<any[]>([]);

    async function loadAlerts() {
        const a = await fetchAlerts();
        setAlerts(a);
    }

    async function handleSilence(alertId: string) {
        const description = `Please silence alert ${alertId}`;
        await processTicket(description, alertId);
        await loadAlerts();
    }

    useEffect(() => {
        loadAlerts();
    }, []);

    return (
        <main className="space-y-8">
            <h1 className="text-3xl font-bold">Grafana – Alerts Dashboard</h1>

            <AlertList alerts={alerts} onSilence={handleSilence} />
        </main>
    );
}