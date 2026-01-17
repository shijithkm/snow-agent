"use client";

import Link from "next/link";
import { useState } from "react";

export function Header() {
    const [menuOpen, setMenuOpen] = useState(false);

    return (
        <header className="mb-6 sm:mb-8">
            <div className="flex items-center justify-between">
                <h1 className="text-lg sm:text-xl font-bold">Snow AI Agent</h1>

                {/* Mobile Menu Button */}
                <button
                    className="md:hidden p-2 rounded-lg bg-slate-800 hover:bg-slate-700"
                    onClick={() => setMenuOpen(!menuOpen)}
                    aria-label="Toggle menu"
                >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                </button>

                {/* Desktop Navigation */}
                <nav className="hidden md:flex space-x-4">
                    <Link href="/" className="text-sm text-slate-300 hover:text-white transition-colors">Home</Link>
                    <Link href="/chat" className="text-sm text-slate-300 hover:text-white transition-colors">Chat</Link>
                    <Link href="/tickets/list" className="text-sm text-slate-300 hover:text-white transition-colors">Ticket List</Link>
                    <Link href="/tickets/create" className="text-sm text-slate-300 hover:text-white transition-colors">Create Ticket</Link>
                    <Link href="/grafana" className="text-sm text-slate-300 hover:text-white transition-colors">Grafana</Link>
                </nav>
            </div>

            {/* Mobile Navigation */}
            {menuOpen && (
                <nav className="md:hidden mt-4 flex flex-col space-y-2 bg-slate-900 rounded-lg p-4 border border-slate-800">
                    <Link
                        href="/"
                        className="text-sm text-slate-300 hover:text-white hover:bg-slate-800 px-3 py-2 rounded transition-colors"
                        onClick={() => setMenuOpen(false)}
                    >
                        Home
                    </Link>
                    <Link
                        href="/chat"
                        className="text-sm text-slate-300 hover:text-white hover:bg-slate-800 px-3 py-2 rounded transition-colors"
                        onClick={() => setMenuOpen(false)}
                    >
                        Chat
                    </Link>
                    <Link
                        href="/tickets/list"
                        className="text-sm text-slate-300 hover:text-white hover:bg-slate-800 px-3 py-2 rounded transition-colors"
                        onClick={() => setMenuOpen(false)}
                    >
                        Ticket List
                    </Link>
                    <Link
                        href="/tickets/create"
                        className="text-sm text-slate-300 hover:text-white hover:bg-slate-800 px-3 py-2 rounded transition-colors"
                        onClick={() => setMenuOpen(false)}
                    >
                        Create Ticket
                    </Link>
                    <Link
                        href="/grafana"
                        className="text-sm text-slate-300 hover:text-white hover:bg-slate-800 px-3 py-2 rounded transition-colors"
                        onClick={() => setMenuOpen(false)}
                    >
                        Grafana
                    </Link>
                </nav>
            )}
        </header>
    );
}
