import { useState, useEffect, useRef } from "react";
import { apiClient } from "../../../infrastructure/api/apiClient";
import type { DomainConfig, Agent } from "../../../domain/entities/types";
import { ChevronDown, PanelLeftClose, PanelLeftOpen, Check } from "lucide-react";
import AppHeader from "../layout/AppHeader";

interface ChatHeaderProps {
    sidebarOpen: boolean;
    setSidebarOpen: (open: boolean) => void;
    selectedDomainId: string;
    selectedAgentId: string;
    onDomainSelect: (id: string) => void;
    onAgentSelect: (id: string) => void;
}

export default function ChatHeader({
    sidebarOpen,
    setSidebarOpen,
    selectedDomainId,
    selectedAgentId,
    onDomainSelect,
    onAgentSelect,
}: ChatHeaderProps) {
    const [domains, setDomains] = useState<DomainConfig[]>([]);
    const [agents, setAgents] = useState<Agent[]>([]);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Load domains on mount
    useEffect(() => {
        const loadDomains = async () => {
            try {
                const data = await apiClient.listDomains();
                setDomains(data);
                // Default to first domain if none selected
                if (!selectedDomainId && data.length > 0) {
                    onDomainSelect(data[0].id);
                }
            } catch (err) {
                console.error("Failed to load domains:", err);
            }
        };
        loadDomains();
    }, []);

    // Load agents when domain changes
    useEffect(() => {
        if (!selectedDomainId) {
            setAgents([]);
            return;
        }
        const loadAgents = async () => {
            try {
                const data = await apiClient.listAgents(selectedDomainId);
                setAgents(data);
                // Default to first agent if none selected or if current selection not in new list
                // (But strictly only if we don't have a valid selection for this domain)
                if (data.length > 0 && (!selectedAgentId || !data.find(a => a.id === selectedAgentId))) {
                    onAgentSelect(data[0].id);
                }
            } catch (err) {
                console.error("Failed to load agents:", err);
            }
        };
        loadAgents();
    }, [selectedDomainId]);

    // Close dropdown on click outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsDropdownOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const currentDomain = domains.find(d => d.id === selectedDomainId);
    const currentAgent = agents.find(a => a.id === selectedAgentId);

    return (
        <AppHeader>
            <div className="flex items-center gap-3">
                {/* Mobile / Sidebar Toggle */}
                <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="p-2 -ml-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
                    aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
                >
                    {sidebarOpen ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
                </button>

                {/* Model Selector */}
                <div className="relative" ref={dropdownRef}>
                    <button
                        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors text-sm font-medium text-gray-700 group"
                    >
                        <span className="text-gray-500 font-normal">{currentDomain?.name || "Select Domain"}</span>
                        <span className="text-gray-300">/</span>
                        <span className="text-gray-900">{currentAgent?.name || "Select Agent"}</span>
                        <ChevronDown size={14} className={`text-gray-400 transition-transform duration-200 ${isDropdownOpen ? "rotate-180" : ""}`} />
                    </button>

                    {/* Dropdown Menu */}
                    {isDropdownOpen && (
                        <div className="absolute top-full left-0 mt-2 w-72 bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden py-1 animate-in fade-in slide-in-from-top-2 duration-200">
                            {domains.length === 0 ? (
                                <div className="px-4 py-3 text-sm text-gray-500">Loading domains...</div>
                            ) : (
                                <div className="max-h-[80vh] overflow-y-auto">
                                    {domains.map(domain => (
                                        <div key={domain.id}>
                                            <div
                                                className="px-4 py-2 text-xs font-semibold text-gray-500 bg-gray-50 uppercase tracking-wider sticky top-0 border-y border-gray-100 first:border-t-0"
                                            >
                                                {domain.name}
                                            </div>
                                            <div>
                                                {/* We need to fetch agents for this domain if not selected. 
                                       But for simplicity in this synchronous-ish UI, we might only show agents for SELECTED domain 
                                       OR we need to preload all. 
                                       
                                       Strategy: For now, just show the domains as clickable headers to switch domain, 
                                       and then list agents for the CURRENT domain. 
                                       
                                       Better UX: Click domain -> Selects domain -> Async loads agents -> Selects first agent.
                                   */}
                                                <button
                                                    onClick={() => {
                                                        onDomainSelect(domain.id);
                                                        // Keep dropdown open to let them select agent? Or auto-select first?
                                                        // Let's keep it simple: Select domain updates state, generic "loading" shows if needed.
                                                    }}
                                                    className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center justify-between ${selectedDomainId === domain.id ? "text-blue-600 font-medium" : "text-gray-700"}`}
                                                >
                                                    {domain.name}
                                                    {selectedDomainId === domain.id && <Check size={14} />}
                                                </button>

                                                {/* Show agents ONLY for selected domain to avoid massive pre-fetching complexity for now */}
                                                {selectedDomainId === domain.id && (
                                                    <div className="pl-4 pr-2 py-1 space-y-0.5">
                                                        {agents.map(agent => (
                                                            <button
                                                                key={agent.id}
                                                                onClick={() => {
                                                                    onAgentSelect(agent.id);
                                                                    setIsDropdownOpen(false);
                                                                }}
                                                                className={`w-full text-left px-3 py-1.5 rounded-md text-sm flex items-center justify-between transition-colors ${selectedAgentId === agent.id
                                                                    ? "bg-blue-50 text-blue-700 font-medium"
                                                                    : "text-gray-600 hover:bg-gray-100"}`}
                                                            >
                                                                <span>{agent.name}</span>
                                                                {selectedAgentId === agent.id && <Check size={12} />}
                                                            </button>
                                                        ))}
                                                        {agents.length === 0 && <div className="px-3 py-2 text-xs text-gray-400 italic">No agents found</div>}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Right Side Actions (e.g. empty for now, maybe User menu later) */}
            <div></div>
        </AppHeader>
    );
}
