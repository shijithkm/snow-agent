"use client";

import { useEffect, useState } from "react";

interface WorkflowStep {
    id: string;
    label: string;
    description: string;
    icon: string;
    color: string;
}

const workflowSteps: WorkflowStep[] = [
    {
        id: "start",
        label: "Ticket Created",
        description: "User submits a ticket via chat or form",
        icon: "📝",
        color: "bg-blue-500",
    },
    {
        id: "classify",
        label: "Intent Classification",
        description: "LLM classifies: Alert, RFI, or L1 Support",
        icon: "🧠",
        color: "bg-purple-500",
    },
    {
        id: "route",
        label: "Smart Routing",
        description: "Routes to Grafana, RAG, or L1 agent",
        icon: "🔀",
        color: "bg-amber-500",
    },
    {
        id: "rag",
        label: "RAG Search",
        description: "Searches company docs with vector DB",
        icon: "🔍",
        color: "bg-violet-500",
    },
    {
        id: "process",
        label: "Agent Processing",
        description: "Grafana/RFI/L1 agent handles request",
        icon: "⚙️",
        color: "bg-emerald-500",
    },
    {
        id: "complete",
        label: "Ticket Resolved",
        description: "Results saved and ticket updated",
        icon: "✅",
        color: "bg-green-500",
    },
];

export function WorkflowAnimation() {
    const [activeStep, setActiveStep] = useState(0);
    const [isPaused, setIsPaused] = useState(false);

    useEffect(() => {
        if (isPaused) return;

        const interval = setInterval(() => {
            setActiveStep((prev) => (prev + 1) % workflowSteps.length);
        }, 2500);

        return () => clearInterval(interval);
    }, [isPaused]);

    const handleStepClick = (index: number) => {
        setActiveStep(index);
        setIsPaused(true);
        setTimeout(() => setIsPaused(false), 5000);
    };

    return (
        <div className="rounded-lg bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-slate-700 p-6 sm:p-8 space-y-6">
            <div className="text-center space-y-2">
                <h2 className="text-xl sm:text-2xl font-bold text-white">
                    🔄 SNOW Agentic AI Workflow
                </h2>
                <p className="text-sm text-slate-300">
                    Watch how tickets flow through our AI-powered system
                </p>
            </div>

            {/* Workflow Steps */}
            <div className="relative">
                {/* Connection Lines */}
                <div className="absolute top-12 left-0 right-0 h-1 bg-slate-700 hidden sm:block">
                    <div
                        className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-green-500 transition-all duration-500 ease-in-out"
                        style={{
                            width: `${(activeStep / (workflowSteps.length - 1)) * 100}%`,
                        }}
                    />
                </div>

                {/* Steps */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 sm:gap-2 relative z-10">
                    {workflowSteps.map((step, index) => (
                        <div
                            key={step.id}
                            className={`flex flex-col items-center cursor-pointer transition-all duration-300 ${index === activeStep ? "scale-110" : "scale-100 opacity-60"
                                }`}
                            onClick={() => handleStepClick(index)}
                        >
                            {/* Icon Circle */}
                            <div
                                className={`w-20 h-20 sm:w-24 sm:h-24 rounded-full flex items-center justify-center text-3xl sm:text-4xl transition-all duration-300 ${index === activeStep
                                    ? `${step.color} shadow-lg shadow-${step.color}/50 animate-pulse`
                                    : "bg-slate-800"
                                    }`}
                            >
                                {step.icon}
                            </div>

                            {/* Label */}
                            <div className="mt-3 text-center">
                                <h3
                                    className={`text-xs sm:text-sm font-semibold transition-colors duration-300 ${index === activeStep ? "text-white" : "text-slate-400"
                                        }`}
                                >
                                    {step.label}
                                </h3>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Active Step Description */}
            <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700 min-h-[80px] transition-all duration-300">
                <div className="flex items-start gap-3">
                    <span className="text-2xl">{workflowSteps[activeStep].icon}</span>
                    <div className="flex-1">
                        <h4 className="text-sm font-semibold text-white mb-1">
                            {workflowSteps[activeStep].label}
                        </h4>
                        <p className="text-xs text-slate-300">
                            {workflowSteps[activeStep].description}
                        </p>
                    </div>
                </div>
            </div>

            {/* Agent Routing Visualization */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <div
                    className={`rounded-lg p-3 border transition-all duration-300 ${activeStep === 3 || activeStep === 4
                        ? "bg-blue-900/30 border-blue-500 scale-105"
                        : "bg-slate-800/30 border-slate-700"
                        }`}
                >
                    <div className="flex items-center gap-2 text-xs">
                        <span className="text-lg">🔔</span>
                        <span className="font-semibold text-blue-300">Grafana Agent</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Alert Suppression</p>
                </div>

                <div
                    className={`rounded-lg p-3 border transition-all duration-300 ${activeStep === 3
                        ? "bg-violet-900/30 border-violet-500 scale-105"
                        : "bg-slate-800/30 border-slate-700"
                        }`}
                >
                    <div className="flex items-center gap-2 text-xs">
                        <span className="text-lg">📚</span>
                        <span className="font-semibold text-violet-300">RAG Agent</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Company Docs Search</p>
                </div>

                <div
                    className={`rounded-lg p-3 border transition-all duration-300 ${activeStep === 4
                        ? "bg-purple-900/30 border-purple-500 scale-105"
                        : "bg-slate-800/30 border-slate-700"
                        }`}
                >
                    <div className="flex items-center gap-2 text-xs">
                        <span className="text-lg">🌐</span>
                        <span className="font-semibold text-purple-300">RFI Agent</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Web Search Fallback</p>
                </div>

                <div
                    className={`rounded-lg p-3 border transition-all duration-300 ${activeStep === 4
                        ? "bg-emerald-900/30 border-emerald-500 scale-105"
                        : "bg-slate-800/30 border-slate-700"
                        }`}
                >
                    <div className="flex items-center gap-2 text-xs">
                        <span className="text-lg">👤</span>
                        <span className="font-semibold text-slate-200">L1 Team</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Technical Support</p>
                </div>
            </div>

            {/* Controls */}
            <div className="flex items-center justify-center gap-4 pt-2">
                <button
                    onClick={() => setIsPaused(!isPaused)}
                    className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-xs font-medium transition-colors"
                >
                    {isPaused ? "▶️ Resume" : "⏸️ Pause"}
                </button>
                <button
                    onClick={() => setActiveStep((prev) => (prev + 1) % workflowSteps.length)}
                    className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-xs font-medium transition-colors"
                >
                    ⏭️ Next Step
                </button>
            </div>

            {/* Tech Info */}
            <div className="flex items-center justify-center gap-2 text-xs text-slate-400 pt-2 border-t border-slate-700">
                <span>Powered by</span>
                <span className="font-semibold text-emerald-400">LangGraph</span>
                <span>+</span>
                <span className="font-semibold text-purple-400">Groq LLM</span>
                <span>+</span>
                <span className="font-semibold text-violet-400">FAISS Vector DB</span>
                <span>+</span>
                <span className="font-semibold text-blue-400">FastAPI</span>
            </div>
        </div>
    );
}
