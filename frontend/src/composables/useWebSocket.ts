import { ref, computed } from "vue";
import { useProcessStore } from "@/stores/processes";

type WebSocketMessage =
  | { type: "log"; process_id: number; data: { timestamp: string; stream: "stdout" | "stderr"; line: string } }
  | {
    type: "status";
    process_id: number;
    data: { status: string; pid: number | null; linux_state?: Process["linux_state"]; warning?: string | null };
  }
  | { type: "subscribed"; action: string; process_id?: number }
  | { type: "unsubscribed"; action: string; process_id?: number }
  | { type: "pong" }
  | { type: "error"; message: string };

export type ConnectionStatus = "connected" | "connecting" | "disconnected" | "error";

// Shared state across all components using this composable
const ws = ref<WebSocket | null>(null);
const connected = ref(false);
const connecting = ref(false);
const lastError = ref<string | null>(null);
const reconnectAttempts = ref(0);
const subscribedLogs = ref<Set<number>>(new Set());
const subscribedStatus = ref(false);

const connectionStatus = computed<ConnectionStatus>(() => {
  if (connected.value) return "connected";
  if (connecting.value) return "connecting";
  if (lastError.value) return "error";
  return "disconnected";
});

let processStore: ReturnType<typeof useProcessStore> | null = null;

function handleMessage(msg: WebSocketMessage) {
  if (!processStore) return;

  switch (msg.type) {
    case "log":
      processStore.appendLog({
        timestamp: msg.data.timestamp,
        stream: msg.data.stream,
        line: msg.data.line,
      });
      break;

    case "status":
      processStore.updateProcessStatus(
        msg.process_id,
        msg.data.status as "stopped" | "running" | "failed",
        msg.data.pid,
        msg.data.linux_state ?? undefined,
        msg.data.warning ?? undefined
      );
      break;

    case "subscribed":
      if (msg.action === "subscribe_logs" && msg.process_id) {
        subscribedLogs.value.add(msg.process_id);
      } else if (msg.action === "subscribe_status") {
        subscribedStatus.value = true;
      }
      break;

    case "unsubscribed":
      if (msg.action === "unsubscribe_logs" && msg.process_id) {
        subscribedLogs.value.delete(msg.process_id);
      } else if (msg.action === "unsubscribe_status") {
        subscribedStatus.value = false;
      }
      break;

    case "pong":
      // Heartbeat response
      break;

    case "error":
      console.error("[WS] Server error:", msg.message);
      break;
  }
}

function connect() {
  // Initialize process store on first connect (must be called within Vue setup context)
  if (!processStore) {
    processStore = useProcessStore();
  }

  if (ws.value?.readyState === WebSocket.OPEN || ws.value?.readyState === WebSocket.CONNECTING) {
    return;
  }

  connecting.value = true;
  lastError.value = null;

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/api/ws`;

  ws.value = new WebSocket(wsUrl);

  ws.value.onopen = () => {
    connected.value = true;
    connecting.value = false;
    reconnectAttempts.value = 0;
    lastError.value = null;
    console.log("[WS] Connected");
  };

  ws.value.onclose = () => {
    connected.value = false;
    connecting.value = false;
    subscribedLogs.value.clear();
    subscribedStatus.value = false;
    reconnectAttempts.value++;
    console.log(`[WS] Disconnected (reconnect attempt ${reconnectAttempts.value})`);
    // Attempt reconnect with exponential backoff (max 30s)
    const delay = Math.min(2000 * Math.pow(1.5, reconnectAttempts.value - 1), 30000);
    setTimeout(connect, delay);
  };

  ws.value.onerror = (e) => {
    console.error("[WS] Error:", e);
    lastError.value = "Connection error";
    connecting.value = false;
  };

  ws.value.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data) as WebSocketMessage;
      handleMessage(msg);
    } catch (e) {
      console.error("[WS] Failed to parse message:", e);
    }
  };
}

function send(data: object) {
  if (ws.value?.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify(data));
  }
}

function subscribeLogs(processId: number) {
  send({ action: "subscribe_logs", process_id: processId });
}

function unsubscribeLogs(processId: number) {
  send({ action: "unsubscribe_logs", process_id: processId });
}

function subscribeStatus() {
  send({ action: "subscribe_status" });
}

function unsubscribeStatus() {
  send({ action: "unsubscribe_status" });
}

function disconnect() {
  if (ws.value) {
    ws.value.close();
    ws.value = null;
  }
}

export function useWebSocket() {
  return {
    connected,
    connecting,
    connectionStatus,
    lastError,
    reconnectAttempts,
    subscribedLogs,
    subscribedStatus,
    connect,
    disconnect,
    subscribeLogs,
    unsubscribeLogs,
    subscribeStatus,
    unsubscribeStatus,
  };
}
