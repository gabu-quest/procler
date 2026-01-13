import { defineStore } from "pinia";
import { ref, computed } from "vue";

export interface ConfigStats {
  processes: number;
  groups: number;
  recipes: number;
  snippets: number;
}

export interface ConfigInfo {
  config_dir: string;
  config_file: string;
  config_exists: boolean;
  changelog_file: string;
  changelog_exists: boolean;
  version: number;
  stats: ConfigStats;
}

export interface ConfigProcess {
  name: string;
  command: string;
  context: "local" | "docker";
  container?: string;
  cwd?: string;
  description?: string;
  tags?: string[];
}

export const useConfigStore = defineStore("config", () => {
  const info = ref<ConfigInfo | null>(null);
  const processes = ref<ConfigProcess[]>([]);
  const changelog = ref<string[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isConfigured = computed(() => info.value?.config_exists ?? false);

  async function fetchInfo() {
    loading.value = true;
    error.value = null;
    try {
      const response = await fetch("/api/config");
      const data = await response.json();
      if (data.success) {
        info.value = data.data;
      } else {
        error.value = data.error;
      }
    } catch (e) {
      error.value = String(e);
    } finally {
      loading.value = false;
    }
  }

  async function fetchProcesses() {
    loading.value = true;
    error.value = null;
    try {
      const response = await fetch("/api/config/processes");
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

  async function fetchChangelog(tail: number = 50) {
    loading.value = true;
    error.value = null;
    try {
      // Use format=raw to get string entries (frontend uses .includes() on them)
      const response = await fetch(`/api/config/changelog?tail=${tail}&format=raw`);
      const data = await response.json();
      if (data.success) {
        changelog.value = data.data.entries;
      } else {
        error.value = data.error;
      }
    } catch (e) {
      error.value = String(e);
    } finally {
      loading.value = false;
    }
  }

  async function reloadConfig() {
    loading.value = true;
    error.value = null;
    try {
      const response = await fetch("/api/config/reload", { method: "POST" });
      const data = await response.json();
      if (data.success) {
        // Refresh info after reload
        await fetchInfo();
      }
      return data;
    } catch (e) {
      error.value = String(e);
      return { success: false, error: String(e) };
    } finally {
      loading.value = false;
    }
  }

  return {
    info,
    processes,
    changelog,
    loading,
    error,
    isConfigured,
    fetchInfo,
    fetchProcesses,
    fetchChangelog,
    reloadConfig,
  };
});
