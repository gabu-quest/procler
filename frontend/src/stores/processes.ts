import { defineStore } from "pinia";
import { ref, computed } from "vue";

export interface LinuxState {
  state_code: string;
  state_name: string;
  state_description: string;
  is_killable: boolean;
}

export interface Process {
  id: number;
  name: string;
  command: string;
  context: "local" | "docker";
  container: string | null;
  cwd: string | null;
  tags: string | null;
  status: "stopped" | "running" | "failed";
  pid: number | null;
  started_at: string | null;
  created_at: string;
  updated_at: string;
  uptime_seconds?: number;
  linux_state?: LinuxState;
  warning?: string;
}

export interface LogEntry {
  timestamp: string;
  stream: "stdout" | "stderr";
  line: string;
}

export const useProcessStore = defineStore("processes", () => {
  const processes = ref<Process[]>([]);
  const currentProcess = ref<Process | null>(null);
  const logs = ref<LogEntry[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const runningCount = computed(() => processes.value.filter((p) => p.status === "running").length);

  async function fetchProcesses() {
    loading.value = true;
    error.value = null;
    try {
      const response = await fetch("/api/processes");
      const data = await response.json();
      if (data.success) {
        processes.value = data.data.processes;
      } else {
        error.value = data.error;
      }
    } catch (e) {
      error.value = String(e);
    } finally {
      loading.value = false;
    }
  }

  async function fetchProcess(name: string) {
    loading.value = true;
    error.value = null;
    try {
      const response = await fetch(`/api/processes/${name}`);
      const data = await response.json();
      if (data.success) {
        currentProcess.value = data.data;
      } else {
        error.value = data.error;
      }
    } catch (e) {
      error.value = String(e);
    } finally {
      loading.value = false;
    }
  }

  async function startProcess(name: string) {
    const response = await fetch(`/api/processes/${name}/start`, { method: "POST" });
    const data = await response.json();
    if (data.success) {
      await fetchProcesses();
      if (currentProcess.value?.name === name) {
        await fetchProcess(name);
      }
    }
    return data;
  }

  async function stopProcess(name: string) {
    const response = await fetch(`/api/processes/${name}/stop`, { method: "POST" });
    const data = await response.json();
    if (data.success) {
      await fetchProcesses();
      if (currentProcess.value?.name === name) {
        await fetchProcess(name);
      }
    }
    return data;
  }

  async function restartProcess(name: string) {
    const response = await fetch(`/api/processes/${name}/restart`, { method: "POST" });
    const data = await response.json();
    if (data.success) {
      await fetchProcesses();
      if (currentProcess.value?.name === name) {
        await fetchProcess(name);
      }
    }
    return data;
  }

  async function removeProcess(name: string) {
    const response = await fetch(`/api/processes/${name}`, { method: "DELETE" });
    const data = await response.json();
    if (data.success) {
      await fetchProcesses();
    }
    return data;
  }

  async function createProcess(process: { name: string; command: string; context?: string; container?: string; cwd?: string; tags?: string }) {
    const response = await fetch("/api/processes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(process),
    });
    const data = await response.json();
    if (data.success) {
      await fetchProcesses();
    }
    return data;
  }

  async function fetchLogs(name: string, tail = 100) {
    try {
      const response = await fetch(`/api/logs/${name}?tail=${tail}`);
      const data = await response.json();
      if (data.success) {
        logs.value = data.data.logs;
      }
    } catch (e) {
      console.error("Failed to fetch logs:", e);
    }
  }

  function appendLog(entry: LogEntry) {
    logs.value.push(entry);
    // Keep max 1000 lines in memory
    if (logs.value.length > 1000) {
      logs.value = logs.value.slice(-1000);
    }
  }

  function updateProcessStatus(processId: number, status: Process["status"], pid: number | null) {
    const process = processes.value.find((p) => p.id === processId);
    if (process) {
      process.status = status;
      process.pid = pid;
    }
    if (currentProcess.value?.id === processId) {
      currentProcess.value.status = status;
      currentProcess.value.pid = pid;
    }
  }

  return {
    processes,
    currentProcess,
    logs,
    loading,
    error,
    runningCount,
    fetchProcesses,
    fetchProcess,
    startProcess,
    stopProcess,
    restartProcess,
    removeProcess,
    createProcess,
    fetchLogs,
    appendLog,
    updateProcessStatus,
  };
});
