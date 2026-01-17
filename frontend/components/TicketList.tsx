export function TicketList({ tickets }: { tickets: any[] }) {
    if (!tickets?.length)
        return <p className="text-sm text-slate-400">No tickets yet.</p>;

    return (
        <div className="rounded-lg bg-slate-900 border border-slate-800 p-6 space-y-3">
            <h3 className="text-lg font-semibold">Tickets</h3>

            <ul className="space-y-2">
                {tickets.map((t) => (
                    <li
                        key={t.id}
                        className="rounded-md bg-slate-950 border border-slate-800 p-3 text-sm"
                    >
                        <div className="flex justify-between items-start gap-4">
                            <div className="flex-1">
                                <div className="mb-1">
                                    <span className="font-semibold">{t.id}</span>{" "}
                                    <span className="text-slate-300">— {t.description}</span>
                                </div>
                                {t.ticket_type && (
                                    <div className="text-xs text-slate-400">Type: {t.ticket_type}</div>
                                )}
                                {t.assigned_to && (
                                    <div className="text-xs text-slate-300 flex items-center gap-2">
                                        <span>Assigned to: {t.assigned_to}</span>
                                        {t.assigned_to === "Snow Agent" ? (
                                            <span className="ml-1 text-amber-300 animate-pulse" aria-hidden>
                                                🤖
                                            </span>
                                        ) : t.assigned_to === "L1 Team" ? (
                                            <span className="ml-1 text-slate-200" aria-hidden>
                                                👤
                                            </span>
                                        ) : t.assigned_to === "RFI Agent" ? (
                                            <span className="ml-1 text-amber-300 animate-pulse" aria-hidden>
                                                🤖
                                            </span>
                                        ) : null}
                                    </div>
                                )}
                                {(t.ticket_type?.toLowerCase() === "silence_alert" || t.assigned_to === "Snow Agent") && (t.start_time || t.end_time) && (
                                    <div className="text-xs text-slate-400">
                                        {t.start_time && <>From: {new Date(t.start_time).toLocaleString()}</>}
                                        {t.start_time && t.end_time && <> — </>}
                                        {t.end_time && <>To: {new Date(t.end_time).toLocaleString()}</>}
                                    </div>
                                )}
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0">
                                {t.status === "in_progress" ? (
                                    <span className="inline-flex items-center gap-2 rounded bg-amber-700/10 px-2 py-1 text-xs font-semibold text-amber-300 uppercase">
                                        IN PROGRESS
                                    </span>
                                ) : t.status === "open" ? (
                                    <span className="inline-flex items-center gap-2 rounded bg-slate-800 px-2 py-1 text-xs uppercase tracking-wide text-slate-300">
                                        <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                                        OPEN
                                    </span>
                                ) : (
                                    <span className="rounded bg-slate-800 px-2 py-1 text-xs uppercase tracking-wide text-slate-300">
                                        CLOSED
                                    </span>
                                )}
                            </div>
                        </div>
                        {t.work_comments && t.work_comments !== "null" && t.work_comments.trim() !== "" && (
                            <div className="mt-3 rounded bg-slate-900 border border-slate-700 p-3">
                                <div className="font-semibold text-blue-300 mb-2 flex items-center gap-2">
                                    <span>🔍</span>
                                    <span>Research Results</span>
                                </div>
                                <pre className="whitespace-pre-wrap text-xs text-slate-300 leading-relaxed">{t.work_comments}</pre>
                            </div>
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
}
