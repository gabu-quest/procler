import { ref, onUnmounted } from "vue";
import { useProcessStore } from "@/stores/processes";

type WebSocketMessage =
  | { type: "log"; process_id: number; data: { timestamp: string; stream: "stdout" | "stderr"; line: string } }
  | { type: "status"; process_id: number; data: { status: string; pid: number | null } }
  | { type: "subscribed"; action: string; process_id?: number }
  | { type: "unsubscribed"; action: string; process_id?: number }
  | { type: "pong" }
  | { type: "error"; message: string };

export function useWebSocket() {
  const ws = ref<WebSocket | null>(null);
  const connected = ref(false);
  const subscribedLogs = ref<Set<number>>(new Set());
  const subscribedStatus = ref(false);

  const processStore = useProcessStore();

  function connect() {
    if (ws.value?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/api/ws`;

    ws.value = new WebSocket(wsUrl);

    ws.value.onopen = () => {
      connected.value = true;
      console.log("[WS] Connected");
    };

    ws.value.onclose = () => {
      connected.value = false;
      subscribedLogs.value.clear();
      subscribedStatus.value = false;
      console.log("[WS] Disconnected");
      // Attempt reconnect after 2 seconds
      setTimeout(connect, 2000);
    };

    ws.value.onerror = (e) => {
      console.error("[WS] Error:", e);
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

  function handleMessage(msg: WebSocketMessage) {
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
          msg.data.pid
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

  onUnmounted(() => {
    disconnect();
  });

  return {
    connected,
    connect,
    disconnect,
    subscribeLogs,
    unsubscribeLogs,
    subscribeStatus,
    unsubscribeStatus,
  };
}
