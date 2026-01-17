import "../style/global.css";
import type { ReactNode } from "react";
import Link from "next/link";

export default function RootLayout({ children }: { children: ReactNode }) {
    return (
        <html lang="en">
            <body className="min-h-screen bg-slate-950 text-slate-100">
                <div className="mx-auto max-w-5xl px-6 py-8">
                    <header className="mb-8 flex items-center justify-between">
                        <h1 className="text-xl font-bold">Snow AI Agent</h1>
                        <nav className="space-x-4">
                            <Link href="/" className="text-sm text-slate-300 hover:text-white">Home</Link>
                            <Link href="/tickets/list" className="text-sm text-slate-300 hover:text-white">Ticket List</Link>
                            <Link href="/tickets/create" className="text-sm text-slate-300 hover:text-white">Create Ticket</Link>
                            <Link href="/grafana" className="text-sm text-slate-300 hover:text-white">Grafana</Link>
                        </nav>
                    </header>

                    {children}
                </div>
            </body>
        </html>
    );
}