import { Link } from "react-router";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import AppHeader from "../components/layout/AppHeader";
import { useSidebarLayout } from "../components/layout/SidebarLayoutContext";
import myAiImage from "../../assets/myai.png";

export default function HomePage() {
  const sidebar = useSidebarLayout();
  const sidebarOpen = sidebar?.sidebarOpen ?? true;
  const setSidebarOpen = sidebar?.setSidebarOpen;

  return (
    <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
      <AppHeader>
        <div className="flex items-center gap-3">
          {setSidebarOpen && (
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 -ml-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
            >
              {sidebarOpen ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
            </button>
          )}
          <div className="text-sm font-semibold text-gray-900">Home</div>
        </div>
        <div />
      </AppHeader>

      <main className="flex-1 min-h-0 flex items-center justify-center p-6">
        <div className="max-w-md w-full text-center">
          <img
            src={myAiImage}
            alt="Multi-Agent.ai"
            className="w-full max-w-xs sm:max-w-sm mx-auto h-auto rounded-2xl"
            loading="lazy"
          />
          <h1 className="text-2xl font-semibold text-gray-900">Home</h1>
          <p className="text-gray-500 mt-2">This page is a placeholder.</p>
          <div className="mt-6">
            <Link
              to="/chat"
              className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
            >
              Go to Chat
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
