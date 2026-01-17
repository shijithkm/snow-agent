"use client";

export function AlertList({ alerts, onSilence }: { alerts: any[]; onSilence: (id: string) => Promise<void> }) {
    if (!alerts?.length) return <p className="text-sm text-slate-400">No alerts.</p>;

    return (
        <ul className="space-y-2">
            {alerts.map((a) => (
                <li
                    key={a.id}
                    className="flex items-center justify-between rounded border border-slate-800 bg-slate-900 px-3 py-2 text-sm"
                >
                    <div>
                        <span className="font-semibold">{a.id}</span>{" "}
                        <span className="text-slate-300">— {a.name}</span>{" "}
                        <span className="text-xs text-slate-400">({a.status})</span>
                    </div>
                    {a.status !== "silenced" && (
                        <button
                            onClick={() => onSilence(a.id)}
                            className="rounded bg-amber-500 px-3 py-1 text-xs font-semibold text-slate-900 hover:bg-amber-400"
                        >
                            Silence
                        </button>
                    )}
                </li>
            ))}
        </ul>
    );
}
