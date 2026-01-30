import { useEffect, lazy, Suspense } from "react";
import { Routes, Route, Navigate, Outlet, useNavigate } from "react-router";
import LoginPage from "./presentation/pages/LoginPage";
import HomePage from "./presentation/pages/HomePage";
import ChatPage from "./presentation/pages/ChatPage";
import AdminPage from "./presentation/pages/AdminPage";
import { apiClient } from "./infrastructure/api/apiClient";
import { useAuthStore } from "./infrastructure/stores/authStore";
import "./App.css";
import ChatRouteLayout from "./presentation/routes/ChatRouteLayout";
import ThreadsRouteLayout from "./presentation/routes/ThreadsRouteLayout";
import AdminRouteLayout from "./presentation/routes/AdminRouteLayout";
import HomeRouteLayout from "./presentation/routes/HomeRouteLayout";

// Lazy load heavy pages
const VisualizerPage = lazy(() => import("./presentation/pages/VisualizerPage"));
const ThreadsPage = lazy(() => import("./presentation/pages/ThreadsPage"));

function AppShellLayout() {
  return (
    <div className="h-screen w-screen flex flex-col bg-background">
      {/* Page Content */}
      <div className="flex-1 min-h-0 overflow-hidden flex">
        <Outlet />
      </div>
    </div>
  );
}

function RequireAuth() {
  const { token } = useAuthStore();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

function LoginRoute() {
  const navigate = useNavigate();
  const { token, setToken } = useAuthStore();

  // If already authenticated, bounce to home.
  useEffect(() => {
    if (token) {
      navigate("/chat", { replace: true });
    }
  }, [token, navigate]);

  const handleLoginSuccess = (newToken: string) => {
    setToken(newToken);
    apiClient.setToken(newToken);
    navigate("/chat", { replace: true });
  };

  return <LoginPage onLoginSuccess={handleLoginSuccess} />;
}

function App() {
  const { token } = useAuthStore();

  // Keep apiClient in sync with auth state.
  useEffect(() => {
    if (token) {
      apiClient.setToken(token);
    }
  }, [token]);

  return (
    <Routes>
      <Route path="/login" element={<LoginRoute />} />

      <Route element={<RequireAuth />}>
        <Route element={<AppShellLayout />}>
          <Route path="/" element={<HomeRouteLayout />}>
            <Route index element={<HomePage />} />
          </Route>

          <Route path="chat" element={<ChatRouteLayout />}>
            <Route index element={<ChatPage />} />
          </Route>

          <Route element={<AdminRouteLayout />}>
            <Route path="admin" element={<AdminPage />} />
            <Route
              path="visualizer"
              element={
                <Suspense fallback={<div className="flex items-center justify-center h-full">Loading…</div>}>
                  <VisualizerPage />
                </Suspense>
              }
            />
          </Route>

          <Route element={<ThreadsRouteLayout />}>
            <Route path="threads" element={<ThreadsPage />} />
            <Route path="threads/:id" element={<ThreadsPage />} />
          </Route>

          {/* Redirect unknown routes to chat */}
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
