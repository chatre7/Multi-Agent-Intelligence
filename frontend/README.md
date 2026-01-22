# Multi-Agent Intelligence Frontend

React + Vite + TailwindCSS frontend for the multi-agent system.

## Features

- 🔐 JWT Authentication
- 💬 Real-time Chat with WebSocket streaming
- 🔀 Domain & Agent selection
- ⚡ Streaming responses from LLMs
- 🎯 Tool approval workflows
- 📊 Metrics dashboard (coming soon)
- 🛠️ Admin panel (coming soon)

## Tech Stack

- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite 5
- **Styling**: TailwindCSS 4 + shadcn/ui components
- **State Management**: Zustand
- **API Client**: Axios
- **WebSocket**: Native WebSocket + custom client
- **Icons**: Lucide React

## Setup

### Prerequisites

- Node.js 18+
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Setup TailwindCSS (already configured)
# No additional setup needed!
```

### Development

```bash
# Start Vite dev server
npm run dev

# Open http://localhost:5173 in browser
```

### Build

```bash
# Build for production
npm run build

# Preview build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── domain/
│   │   └── entities/
│   │       └── types.ts              # Domain entities (Agent, Conversation, etc)
│   │
│   ├── infrastructure/
│   │   ├── api/
│   │   │   └── apiClient.ts          # Axios HTTP client
│   │   ├── stores/
│   │   │   └── conversationStore.ts  # Zustand conversation state
│   │   └── websocket/
│   │       └── WebSocketClient.ts    # WebSocket client for streaming
│   │
│   ├── presentation/
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatContainer.tsx # Main chat component
│   │   │   │   ├── ChatMessage.tsx   # Individual message
│   │   │   │   └── ChatInput.tsx     # Input with send button
│   │   │   └── selectors/
│   │   │       └── DomainSelector.tsx # Domain/Agent picker
│   │   └── pages/
│   │       ├── LoginPage.tsx          # Authentication
│   │       └── ChatPage.tsx           # Main chat page
│   │
│   ├── lib/
│   │   └── utils.ts                  # Utility functions (cn helper)
│   │
│   ├── App.tsx                       # Main app component
│   ├── App.css                       # Global styles
│   ├── index.css                     # TailwindCSS directives
│   └── main.tsx                      # Entry point
│
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
└── package.json
```

## Usage

### Login

1. Start the backend: `python -m uvicorn src.presentation.api.app:create_app --reload`
2. Open frontend: `npm run dev`
3. Login with demo credentials:
   - Admin: `admin:admin`
   - Developer: `dev:dev`
   - User: `user:user`

### Start a Conversation

1. Select a Domain from the dropdown
2. Select an Agent from the second dropdown
3. Click "Start Conversation"
4. Type a message and press Enter or click Send
5. Watch responses stream in real-time!

## Features in Detail

### Real-time Streaming

WebSocket connection automatically handles:
- Message streaming with delta chunks
- Message completion events
- Tool approval requests
- Error handling with auto-reconnection

### State Management

Zustand store manages:
- Current conversation and messages
- Streaming state
- Loading and error states
- Domain/Agent selections

### Authentication

- JWT token stored in localStorage
- Automatic token injection in API requests
- Login/logout functionality
- Token persistence across sessions

## API Integration

The frontend communicates with backend on:

- **REST API**: `http://localhost:8000/api/v1`
- **WebSocket**: `ws://localhost:8000/ws/chat/{conversation_id}`

### Available Endpoints (via apiClient)

```typescript
// Auth
apiClient.login(username, password)
apiClient.getMe()

// Domains
apiClient.listDomains()
apiClient.getDomain(id)

// Agents
apiClient.listAgents(domainId?)
apiClient.getAgent(id)

// Conversations
apiClient.startConversation(domainId, agentId)
apiClient.getConversation(id)
apiClient.listConversations()

// Tool Runs
apiClient.listToolRuns()
apiClient.getToolRun(id)
apiClient.approveToolRun(id)
apiClient.rejectToolRun(id, reason)

// Metrics
apiClient.getMetrics()
apiClient.getHealth()
```

## Next Steps

- [ ] Admin panel for domain/agent management
- [ ] Metrics dashboard with real-time charts
- [ ] Tool approval modal UI
- [ ] Conversation history sidebar
- [ ] Export chat as markdown/PDF
- [ ] Dark mode support
- [ ] Mobile responsive design
- [ ] E2E tests with Playwright

## Troubleshooting

### WebSocket Connection Fails

- Ensure backend is running on `localhost:8000`
- Check CORS configuration in backend
- Verify token is valid

### API Calls Return 401

- Token may have expired
- Try logging out and back in
- Check localStorage for valid token

### Styles Not Applying

- Rebuild TailwindCSS: `npm run build`
- Clear browser cache
- Check tailwind.config.js content patterns

## Development

### Add New Components

1. Create component in `src/presentation/components/`
2. Use Tailwind classes for styling
3. Import and use in pages

### Add New API Endpoints

1. Add method to `apiClient` in `src/infrastructure/api/apiClient.ts`
2. Use in components via `apiClient.methodName()`
3. Update TypeScript types

### Add New Store Slices

1. Add to Zustand store in `src/infrastructure/stores/conversationStore.ts`
2. Use `useConversationStore()` hook in components

## License

MIT
