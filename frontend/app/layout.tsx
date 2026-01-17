import "../style/global.css";
import type { ReactNode } from "react";
import { Header } from "@/components/Header";

export default function RootLayout({ children }: { children: ReactNode }) {
    return (
        <html lang="en">
            <body className="min-h-screen bg-slate-950 text-slate-100" suppressHydrationWarning>
                <div className="mx-auto max-w-5xl px-4 sm:px-6 py-4 sm:py-8">
                    <Header />
                    {children}
                </div>
            </body>
        </html>
    );
}