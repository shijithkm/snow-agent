"use client";

import { useState, useEffect } from "react";

export function TicketForm({ onSubmit }: { onSubmit: (d: string, a?: string, t?: string, start?: string, end?: string, serviceType?: string, application?: string) => Promise<void> }) {
    const [description, setDescription] = useState("");
    const [alertId, setAlertId] = useState("");
    const [alerts, setAlerts] = useState<any[] | null>(null);
    const [alertsError, setAlertsError] = useState<string | null>(null);

    const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

    useEffect(() => {
        let mounted = true;
        async function load() {
            try {
                const res = await fetch(API_BASE + "/alerts");
                if (!res.ok) throw new Error(String(res.status));
                const data = await res.json();
                if (mounted) setAlerts(data || []);
            } catch (err: any) {
                if (mounted) setAlertsError(err?.message ?? String(err));
            }
        }
        load();
        return () => { mounted = false };
    }, [API_BASE]);

    const ticketTypes = [
        { label: "RFI (Request for Information)", value: "rfi" },
        { label: "RITM (Requested Item)", value: "ritm" },
        { label: "INCIDENT (Service Disruption)", value: "incident" }
    ];

    const serviceTypes = [
        { label: "Suppress Alerts", value: "suppress_alerts" },
        { label: "Access Request", value: "access_request" },
        { label: "Update Firewall", value: "update_firewall" }
    ];

    const applications = [
        { label: "Website 1", value: "website1" },
        { label: "Website 2", value: "website2" }
    ];

    const [ticketType, setTicketType] = useState("rfi");
    const [serviceType, setServiceType] = useState("");
    const [application, setApplication] = useState("");

    // Prefill start/end with tomorrow's local datetime (end = +1 hour)
    const defaultTimes = (() => {
        const now = new Date();
        const tom = new Date(now);
        tom.setDate(tom.getDate() + 1);
        function toLocalInput(d: Date) {
            const pad = (n: number) => String(n).padStart(2, "0");
            const yyyy = d.getFullYear();
            const mm = pad(d.getMonth() + 1);
            const dd = pad(d.getDate());
            const hh = pad(d.getHours());
            const min = pad(d.getMinutes());
            return `${yyyy}-${mm}-${dd}T${hh}:${min}`;
        }
        const start = toLocalInput(tom);
        const endDate = new Date(tom);
        endDate.setHours(endDate.getHours() + 1);
        const end = toLocalInput(endDate);
        return { start, end };
    })();

    const [startTime, setStartTime] = useState(defaultTimes.start);
    const [endTime, setEndTime] = useState(defaultTimes.end);

    async function handleSubmit() {
        const startIso = startTime ? new Date(startTime).toISOString() : undefined;
        const endIso = endTime ? new Date(endTime).toISOString() : undefined;
        await onSubmit(
            description,
            alertId || undefined,
            ticketType || undefined,
            startIso,
            endIso,
            serviceType || undefined,
            application || undefined
        );
        setDescription("");
        setAlertId("");
        setTicketType("rfi");
        setServiceType("");
        setApplication("");
        setStartTime("");
        setEndTime("");
    }

    return (
        <div className="rounded-lg bg-slate-900 border border-slate-800 p-6 space-y-4">
            <h3 className="text-lg font-semibold">Create Ticket</h3>

            <div className="space-y-1">
                <label className="text-sm text-slate-300">Ticket Type *</label>
                <select
                    className="w-full rounded-md bg-slate-950 border border-slate-800 p-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    value={ticketType}
                    onChange={(e) => {
                        setTicketType(e.target.value);
                        setServiceType(""); // Reset service type when ticket type changes
                        setAlertId("");
                        setApplication("");
                    }}
                >
                    {ticketTypes.map((type) => (
                        <option key={type.value} value={type.value}>
                            {type.label}
                        </option>
                    ))}
                </select>
            </div>

            {ticketType === "ritm" && (
                <div className="space-y-1">
                    <label className="text-sm text-slate-300">Service Type *</label>
                    <select
                        className="w-full rounded-md bg-slate-950 border border-slate-800 p-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
                        value={serviceType}
                        onChange={(e) => {
                            setServiceType(e.target.value);
                            setAlertId("");
                            setApplication("");
                        }}
                    >
                        <option value="">Select a service</option>
                        {serviceTypes.map((type) => (
                            <option key={type.value} value={type.value}>
                                {type.label}
                            </option>
                        ))}
                    </select>
                </div>
            )}

            {serviceType === "suppress_alerts" && (
                <>
                    <div className="space-y-1">
                        <label className="text-sm text-slate-300">Alert *</label>
                        {alertsError ? (
                            <div className="text-xs text-rose-400">Failed to load alerts</div>
                        ) : alerts === null ? (
                            <div className="text-xs text-slate-400">Loading alerts…</div>
                        ) : (
                            <select
                                className="w-full rounded-md bg-slate-950 border border-slate-800 p-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
                                value={alertId}
                                onChange={(e) => setAlertId(e.target.value)}
                            >
                                <option value="">Select an alert</option>
                                {alerts.map((a: any) => (
                                    <option key={a.id} value={a.id}>
                                        {a.name ? `${a.name} (${a.id})` : a.id}
                                    </option>
                                ))}
                            </select>
                        )}
                    </div>

                    <div className="space-y-1">
                        <label className="text-sm text-slate-300">Application *</label>
                        <select
                            className="w-full rounded-md bg-slate-950 border border-slate-800 p-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
                            value={application}
                            onChange={(e) => setApplication(e.target.value)}
                        >
                            <option value="">Select an application</option>
                            {applications.map((app) => (
                                <option key={app.value} value={app.value}>
                                    {app.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                            <label className="text-sm text-slate-300">Start Time (local) *</label>
                            <input
                                type="datetime-local"
                                className="w-full rounded-md bg-slate-950 border border-slate-800 p-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
                                value={startTime}
                                onChange={(e) => setStartTime(e.target.value)}
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-sm text-slate-300">End Time (local) *</label>
                            <input
                                type="datetime-local"
                                className="w-full rounded-md bg-slate-950 border border-slate-800 p-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
                                value={endTime}
                                onChange={(e) => setEndTime(e.target.value)}
                            />
                        </div>
                    </div>
                </>
            )}

            <div className="space-y-1">
                <label className="text-sm text-slate-300">Description *</label>
                <textarea
                    rows={3}
                    className="w-full rounded-md bg-slate-950 border border-slate-800 p-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Describe your request..."
                />
            </div>

            <button
                onClick={handleSubmit}
                disabled={!description || (ticketType === "ritm" && !serviceType) || (serviceType === "suppress_alerts" && (!alertId || !application))}
                className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed"
            >
                Submit Ticket
            </button>
        </div>
    );
}
