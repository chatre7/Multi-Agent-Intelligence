import { useState, useEffect } from "react";
import type { ReactNode } from "react";
import { ThreadsSidebar } from "../threads/ThreadsSidebar";
import type { ThreadCategory } from "../threads/ThreadsSidebar";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import AppHeader from "./AppHeader";

interface ThreadsLayoutProps {
    children: ReactNode;
    activeCategory: ThreadCategory;
    onSelectCategory: (category: ThreadCategory) => void;
}

export default function ThreadsLayout({
    children,
    activeCategory,
    onSelectCategory
}: ThreadsLayoutProps) {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [isMobile, setIsMobile] = useState(false);

    // Handle window resize for responsive behavior
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth < 768) {
                setIsMobile(true);
                setSidebarOpen(false);
            } else {
                setIsMobile(false);
                setSidebarOpen(true);
            }
        };

        // Initial check
        handleResize();

        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);

    return (
        <div className="flex-1 min-h-0 w-full flex bg-gradient-to-br from-slate-50 via-white to-blue-50 overflow-hidden">
            {/* Sidebar */}
            {!isMobile ? (
                <aside
                    className={`${sidebarOpen ? "w-80" : "w-0"
                        } transition-all duration-300 ease-in-out border-r border-gray-200 bg-white/80 backdrop-blur-sm flex flex-col overflow-hidden flex-shrink-0 relative`}
                >
                    <ThreadsSidebar
                        activeCategory={activeCategory}
                        onSelectCategory={onSelectCategory}
                        isMobile={false}
                    />
                </aside>
            ) : (
                <ThreadsSidebar
                    activeCategory={activeCategory}
                    onSelectCategory={onSelectCategory}
                    isMobile={true}
                    isOpen={sidebarOpen}
                    onClose={() => setSidebarOpen(false)}
                />
            )}

            {/* Main Content */}
            <main className="flex-1 min-w-0 min-h-0 flex flex-col relative">
                {/* Mobile Header / Sidebar Toggle */}
                <AppHeader>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                            className="p-2 -ml-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
                            aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
                        >
                            {sidebarOpen ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
                        </button>
                        <div className="text-sm font-semibold text-gray-900">
                            Threads
                        </div>
                    </div>
                    <div />
                </AppHeader>

                <div className="flex-1 min-h-0 overflow-hidden relative flex flex-col">
                    {children}
                </div>
            </main>
        </div>
    );
}
