import { defineStore } from "pinia";
import { ref, computed } from "vue";

export interface GroupProcess {
  process: string;
  status?: string;
  pid?: number | null;
  uptime_seconds?: number;
  success?: boolean;
  error?: string;
}

export interface Group {
  name: string;
  description?: string;
  processes: string[];
  stop_order: string[];
}

export interface GroupStatus {
  group: string;
  description?: string;
  statuses: GroupProcess[];
}

export const useGroupStore = defineStore("groups", () => {
  const groups = ref<Group[]>([]);
  const currentGroupStatus = ref<GroupStatus | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const operationInProgress = ref<string | null>(null); // Track which group is being operated on

  const groupCount = computed(() => groups.value.length);

  async function fetchGroups() {
    loading.value = true;
    error.value = null;
    try {
      const response = await fetch("/api/groups");
      const data = await response.json();
      if (data.success) {
        groups.value = data.data.groups;
      } else {
        error.value = data.error;
      }
    } catch (e) {
      error.value = String(e);
    } finally {
      loading.value = false;
    }
  }

  async function fetchGroupStatus(name: string) {
    loading.value = true;
    error.value = null;
    try {
      const response = await fetch(`/api/groups/${name}/status`);
      const data = await response.json();
      if (data.success) {
        currentGroupStatus.value = data.data;
      } else {
        error.value = data.error;
      }
    } catch (e) {
      error.value = String(e);
    } finally {
      loading.value = false;
    }
  }

  async function startGroup(name: string) {
    operationInProgress.value = name;
    try {
      const response = await fetch(`/api/groups/${name}/start`, { method: "POST" });
      const data = await response.json();
      return data;
    } finally {
      operationInProgress.value = null;
    }
  }

  async function stopGroup(name: string) {
    operationInProgress.value = name;
    try {
      const response = await fetch(`/api/groups/${name}/stop`, { method: "POST" });
      const data = await response.json();
      return data;
    } finally {
      operationInProgress.value = null;
    }
  }

  return {
    groups,
    currentGroupStatus,
    loading,
    error,
    operationInProgress,
    groupCount,
    fetchGroups,
    fetchGroupStatus,
    startGroup,
    stopGroup,
  };
});
