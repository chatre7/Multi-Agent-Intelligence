# WebSocket Protocol Documentation

## Connection

### Endpoint
```
ws://[host]/ws?token=[JWT_TOKEN]
wss://[host]/ws?token=[JWT_TOKEN]  (production)
```

### Authentication
- Token passed via query parameter `?token=`
- JWT token from `/v1/auth/login` endpoint
- Invalid/missing token returns close code `1008`

---

## Message Format

All messages are JSON with a `type` field:

```typescript
interface WebSocketMessage {
  type: string;
  payload?: object;
  conversationId?: string;
  requestId?: string;
}
```

---

## Client → Server Messages

### PING
Keep-alive ping.

```json
{ "type": "PING" }
```

**Response:** `{ "type": "PONG" }`

---

### start_conversation
Start a new conversation.

```json
{
  "type": "start_conversation",
  "payload": {
    "domainId": "software_development"
  }
}
```

**Response:**
```json
{
  "type": "conversation_started",
  "payload": {
    "conversationId": "uuid",
    "domainId": "software_development",
    "activeAgent": "agent_id"
  }
}
```

---

### send_message
Send a message in a conversation.

```json
{
  "type": "send_message",
  "conversationId": "uuid",
  "payload": {
    "content": "Hello, help me with..."
  }
}
```

**Response Flow:**
1. `message_chunk` (multiple) - streaming tokens
2. `message_complete` - final message

---

### cancel_stream
Cancel an active stream.

```json
{
  "type": "cancel_stream",
  "conversationId": "uuid"
}
```

---

### approve_tool
Approve or reject a tool execution.

```json
{
  "type": "approve_tool",
  "conversationId": "uuid",
  "requestId": "uuid",
  "payload": {
    "approved": true,
    "reason": "optional rejection reason"
  }
}
```

---

## Server → Client Messages

### PONG
Response to PING.

```json
{ "type": "PONG" }
```

---

### message_chunk
Streaming token chunk.

```json
{
  "type": "message_chunk",
  "conversationId": "uuid",
  "payload": {
    "messageId": "uuid",
    "chunk": "partial text",
    "agentName": "Agent Name"
  }
}
```

---

### message_complete
Final message after streaming.

```json
{
  "type": "message_complete",
  "conversationId": "uuid",
  "payload": {
    "messageId": "uuid",
    "content": "full response text",
    "agentName": "Agent Name",
    "metadata": {
      "tokenCount": 150,
      "durationMs": 2500
    }
  }
}
```

---

### tool_approval_required
Tool requires user approval.

```json
{
  "type": "tool_approval_required",
  "conversationId": "uuid",
  "payload": {
    "requestId": "uuid",
    "toolName": "Tool Name",
    "toolArgs": {},
    "description": "Tool description",
    "agentName": "Agent Name"
  }
}
```

---

### tool_executed
Tool execution result.

```json
{
  "type": "tool_executed",
  "conversationId": "uuid",
  "payload": {
    "requestId": "uuid",
    "toolName": "Tool Name",
    "result": {},
    "success": true,
    "errorMessage": null
  }
}
```

---

### error
Error message.

```json
{
  "type": "error",
  "conversationId": "uuid",
  "error": "Error message",
  "payload": {
    "code": "error_code",
    "message": "Error message"
  }
}
```

**Error Codes:**
| Code | Description |
|------|-------------|
| `bad_request` | Missing required fields |
| `forbidden` | Permission denied |
| `not_found` | Resource not found |
| `not_configured` | Feature not configured |
| `stream_error` | Streaming error |
| `cancelled` | Stream cancelled |
| `tool_request_failed` | Tool request failed |
| `tool_execute_failed` | Tool execution failed |

---

## Close Codes

| Code | Meaning |
|------|---------|
| 1000 | Normal closure |
| 1006 | Abnormal closure (network/proxy issue) |
| 1008 | Policy violation (auth failed) |

---

## Reconnection Strategy

The client implements automatic reconnection:

```typescript
// Default configuration
{
  reconnectAttempts: 5,    // Max attempts
  reconnectDelay: 3000     // 3 seconds between attempts
}
```

### Reconnection Flow:

1. On disconnect (non-manual):
   - Wait `reconnectDelay` ms
   - Attempt reconnection
   - Increment attempt counter

2. If successful:
   - Reset attempt counter to 0
   - Resume normal operation

3. If max attempts reached:
   - Log error
   - Stop reconnection attempts
   - User intervention required

### Best Practices:

1. **Exponential Backoff** (recommended enhancement):
   ```typescript
   delay = baseDelay * Math.pow(2, attemptNumber)
   ```

2. **Check connectivity before reconnect**:
   ```typescript
   navigator.onLine // Browser API
   ```

3. **Notify user** when connection lost/restored

4. **Resume conversations** after reconnect by re-subscribing
