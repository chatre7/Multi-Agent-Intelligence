import { useEffect, lazy, Suspense } from "react";
import { Routes, Route, Link, useLocation, Navigate } from "react-router";
import LoginPage from "./presentation/pages/LoginPage";
import ChatPage from "./presentation/pages/ChatPage";
import AdminPage from "./presentation/pages/AdminPage";
import { BarChart3, MessageCircle, Route as RouteIcon, Hash } from "lucide-react";
import { apiClient } from "./infrastructure/api/apiClient";
import { useAuthStore } from "./infrastructure/stores/authStore";
import "./App.css";

// Lazy load heavy pages
const VisualizerPage = lazy(() => import("./presentation/pages/VisualizerPage"));
const ThreadsPage = lazy(() => import("./presentation/pages/ThreadsPage"));

function NavLink({ to, children, icon: Icon }: { to: string; children: React.ReactNode; icon: React.ElementType }) {
  const location = useLocation();
  const isActive = location.pathname === to || (to === "/" && location.pathname === "/");

  return (
    <Link
      to={to}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${isActive
        ? "bg-blue-100 text-blue-700"
        : "text-gray-600 hover:bg-gray-100"
        }`}
    >
      <Icon size={20} />
      {children}
    </Link>
  );
}

function AppLayout({ children }: { children: React.ReactNode }) {
  const { logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    apiClient.clearToken();
  };

  return (
    <div className="h-screen w-screen flex flex-col">
      {/* Navigation Bar */}
      <nav className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <NavLink to="/" icon={MessageCircle}>Chat</NavLink>
          <NavLink to="/admin" icon={BarChart3}>Admin</NavLink>
          <NavLink to="/visualizer" icon={RouteIcon}>Visualizer</NavLink>
          <NavLink to="/threads" icon={Hash}>Threads</NavLink>
        </div>

        <button
          onClick={handleLogout}
          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm font-medium"
        >
          Logout
        </button>
      </nav>

      {/* Page Content */}
      <div className="flex-1 overflow-hidden">
        {children}
      </div>
    </div>
  );
}

function App() {
  const { token, setToken } = useAuthStore();

  // Sync token to apiClient on mount
  useEffect(() => {
    if (token) {
      apiClient.setToken(token);
    }
  }, [token]);

  const handleLoginSuccess = (newToken: string) => {
    setToken(newToken);
    apiClient.setToken(newToken);
  };

  if (!token) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <Routes>
      {/* Standalone Route? No, move everything into AppLayout for consistency */}
      <Route
        path="/*"
        element={
          <AppLayout>
            <Routes>
              <Route path="/" element={<ChatPage token={token} />} />
              <Route path="/admin" element={<AdminPage />} />
              <Route
                path="/visualizer"
                element={
                  <Suspense fallback={<div className="flex items-center justify-center h-full">Loading…</div>}>
                    <VisualizerPage />
                  </Suspense>
                }
              />
              <Route path="/threads" element={<ThreadsPage />} />
              <Route path="/threads/:id" element={<ThreadsPage />} />

              {/* Redirect unknown routes to chat */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AppLayout>
        }
      />
    </Routes>
  );
}

export default App;
