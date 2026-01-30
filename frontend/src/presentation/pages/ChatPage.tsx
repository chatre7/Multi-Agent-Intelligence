import { useConversationStore } from "../../infrastructure/stores/conversationStore";
import ChatContainer from "../components/chat/ChatContainer";
import { MessageSquare } from "lucide-react";
import { useAuthStore } from "../../infrastructure/stores/authStore";

export default function ChatPage() {
  const store = useConversationStore();
  const token = useAuthStore((s) => s.token);

  if (!token) {
    return null;
  }

  return store.currentConversation ? (
    <ChatContainer conversationId={store.currentConversation.id} token={token} />
  ) : (
    <div className="h-full flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <MessageSquare className="text-blue-500" size={32} />
        </div>
        <h2 className="text-xl font-semibold text-gray-900">Welcome</h2>
        <p className="text-gray-500 mt-2">Select a Model to begin</p>
      </div>
    </div>
  );
}
