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
                    <div className="flex items-center">
                        {a.status === "silenced" ? (
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                className="h-5 w-5 text-slate-400"
                                aria-hidden="true"
                                role="img"
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M15 12a3 3 0 00-3-3v6a3 3 0 003-3zM5 9v6h4l5 4V5L9 9H5z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 4L4 20" />
                            </svg>
                        ) : (
                            <button
                                onClick={() => onSilence(a.id)}
                                className="rounded bg-amber-500 px-3 py-1 text-xs font-semibold text-slate-900 hover:bg-amber-400"
                            >
                                Silence
                            </button>
                        )}
                    </div>
                </li>
            ))}
        </ul>
    );
}
