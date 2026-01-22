import { useState } from "react";
import LoginPage from "./presentation/pages/LoginPage";
import ChatPage from "./presentation/pages/ChatPage";
import AdminPage from "./presentation/pages/AdminPage";
import { BarChart3, MessageCircle } from "lucide-react";
import "./App.css";

function App() {
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem("auth_token");
  });
  const [currentPage, setCurrentPage] = useState<"chat" | "admin">("chat");

  const handleLoginSuccess = (newToken: string) => {
    setToken(newToken);
    localStorage.setItem("auth_token", newToken);
  };

  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem("auth_token");
    setCurrentPage("chat");
  };

  if (!token) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="h-screen w-screen flex flex-col">
      {/* Navigation Bar */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setCurrentPage("chat")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              currentPage === "chat"
                ? "bg-blue-100 text-blue-700"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            <MessageCircle size={20} />
            Chat
          </button>
          <button
            onClick={() => setCurrentPage("admin")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              currentPage === "admin"
                ? "bg-blue-100 text-blue-700"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            <BarChart3 size={20} />
            Admin
          </button>
        </div>

        <button
          onClick={handleLogout}
          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm font-medium"
        >
          Logout
        </button>
      </div>

      {/* Page Content */}
      <div className="flex-1 overflow-hidden">
        {currentPage === "chat" ? <ChatPage token={token} /> : <AdminPage />}
      </div>
    </div>
  );
}

export default App;
