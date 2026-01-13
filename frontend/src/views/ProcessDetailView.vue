<template>
  <div class="process-detail">
    <div class="page-header">
      <div class="header-left">
        <n-button quaternary @click="router.back()">
          <template #icon>
            <PhArrowLeft />
          </template>
        </n-button>
        <h1>{{ store.currentProcess?.name ?? "Loading..." }}</h1>
        <n-tag v-if="store.currentProcess" :type="statusColor(store.currentProcess.status)" size="medium">
          {{ store.currentProcess.status }}
        </n-tag>
      </div>
      <n-space>
        <n-button
          type="success"
          :disabled="store.currentProcess?.status === 'running'"
          @click="handleStart"
        >
          <template #icon>
            <PhPlay weight="fill" />
          </template>
          Start
        </n-button>
        <n-button
          type="warning"
          :disabled="store.currentProcess?.status !== 'running'"
          @click="handleStop"
        >
          <template #icon>
            <PhStop weight="fill" />
          </template>
          Stop
        </n-button>
        <n-button type="info" @click="handleRestart">
          <template #icon>
            <PhArrowsClockwise />
          </template>
          Restart
        </n-button>
      </n-space>
    </div>

    <n-spin :show="store.loading">
      <div v-if="store.error" class="error-state">
        <n-alert type="error" :title="store.error" />
      </div>

      <n-grid v-else-if="store.currentProcess" :cols="2" :x-gap="24" :y-gap="24">
        <n-gi>
          <n-card title="Details">
            <n-descriptions :column="1" label-placement="left" bordered>
              <n-descriptions-item label="Name">{{ store.currentProcess.name }}</n-descriptions-item>
              <n-descriptions-item label="Command">
                <n-code>{{ store.currentProcess.command }}</n-code>
              </n-descriptions-item>
              <n-descriptions-item label="Context">
                <n-tag size="small" :type="contextTagType">{{ contextLabel }}</n-tag>
              </n-descriptions-item>
              <n-descriptions-item v-if="store.currentProcess.container" label="Container">
                {{ store.currentProcess.container }}
              </n-descriptions-item>
              <n-descriptions-item v-if="store.currentProcess.cwd" label="Working Dir">
                {{ store.currentProcess.cwd }}
              </n-descriptions-item>
              <n-descriptions-item label="PID">{{ store.currentProcess.pid ?? "-" }}</n-descriptions-item>
              <n-descriptions-item v-if="store.currentProcess.linux_state" label="State">
                <n-space size="small">
                  <n-tag
                    :type="linuxStateType(store.currentProcess.linux_state.state_code)"
                    size="small"
                  >
                    {{ store.currentProcess.linux_state.state_code }} ({{ store.currentProcess.linux_state.state_name }})
                  </n-tag>
                  <span v-if="!store.currentProcess.linux_state.is_killable" class="state-warning">
                    ⚠️ Cannot be killed
                  </span>
                </n-space>
              </n-descriptions-item>
              <n-descriptions-item v-if="store.currentProcess.uptime_seconds" label="Uptime">
                {{ formatUptime(store.currentProcess.uptime_seconds) }}
              </n-descriptions-item>
              <n-descriptions-item v-if="store.currentProcess.tags" label="Tags">
                <n-space size="small">
                  <n-tag v-for="tag in store.currentProcess.tags" :key="tag" size="small">
                    {{ tag }}
                  </n-tag>
                </n-space>
              </n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card title="Logs" class="logs-card">
            <template #header-extra>
              <n-space size="small">
                <n-button size="small" @click="fetchLogs">Refresh</n-button>
                <n-tag :type="connected ? 'success' : 'default'" size="small">
                  {{ connected ? "Live" : "Disconnected" }}
                </n-tag>
              </n-space>
            </template>
            <div class="log-viewer" ref="logViewerRef">
              <div v-if="store.logs.length === 0" class="log-empty">No logs available</div>
              <div
                v-for="(log, idx) in store.logs"
                :key="idx"
                :class="['log-line', `log-${log.stream}`]"
              >
                <span class="log-timestamp">{{ formatTimestamp(log.timestamp) }}</span>
                <span class="log-content">{{ log.line }}</span>
              </div>
            </div>
          </n-card>
        </n-gi>
      </n-grid>
      <div v-else class="empty-state">
        <n-empty description="Process details unavailable" size="small">
          <template #extra>
            <n-button size="small" @click="store.fetchProcess(processName)">Retry</n-button>
          </template>
        </n-empty>
      </div>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  NButton,
  NCard,
  NGrid,
  NGi,
  NDescriptions,
  NDescriptionsItem,
  NTag,
  NSpace,
  NSpin,
  NCode,
  NAlert,
  NEmpty,
  useMessage,
} from "naive-ui";
import { PhArrowLeft, PhPlay, PhStop, PhArrowsClockwise } from "@phosphor-icons/vue";
import { useProcessStore } from "@/stores/processes";
import { useWebSocket } from "@/composables/useWebSocket";

const route = useRoute();
const router = useRouter();
const store = useProcessStore();
const message = useMessage();
const { connected, connect, subscribeLogs, unsubscribeLogs, subscribeStatus } = useWebSocket();

const logViewerRef = ref<HTMLElement | null>(null);

const processName = route.params.name as string;
const contextLabel = computed(() => {
  const process = store.currentProcess;
  return process?.context ?? process?.context_type ?? "local";
});
const contextTagType = computed(() => (contextLabel.value === "docker" ? "info" : "default"));

function statusColor(status: string) {
  switch (status) {
    case "running":
      return "success";
    case "stopped":
      return "default";
    case "failed":
      return "error";
    default:
      return "default";
  }
}

function formatTimestamp(ts: string) {
  try {
    const date = new Date(ts);
    return date.toLocaleTimeString();
  } catch {
    return ts;
  }
}

function linuxStateType(stateCode: string) {
  switch (stateCode) {
    case "R":
      return "success";
    case "S":
    case "I":
      return "info";
    case "D":
      return "error";
    case "Z":
    case "T":
    case "t":
      return "warning";
    default:
      return "default";
  }
}

function formatUptime(seconds: number) {
  if (seconds < 60) return `${Math.floor(seconds)}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`;
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${mins}m`;
}

async function fetchLogs() {
  await store.fetchLogs(processName, 200);
  scrollToBottom();
}

function scrollToBottom() {
  nextTick(() => {
    if (logViewerRef.value) {
      logViewerRef.value.scrollTop = logViewerRef.value.scrollHeight;
    }
  });
}

async function handleStart() {
  const result = await store.startProcess(processName);
  if (result.success) {
    message.success("Process started");
  } else {
    message.error(result.error);
  }
}

async function handleStop() {
  const result = await store.stopProcess(processName);
  if (result.success) {
    message.success("Process stopped");
  } else {
    message.error(result.error);
  }
}

async function handleRestart() {
  const result = await store.restartProcess(processName);
  if (result.success) {
    message.success("Process restarted");
  } else {
    message.error(result.error);
  }
}

// Auto-scroll when new logs come in
watch(() => store.logs.length, scrollToBottom);

onMounted(async () => {
  await store.fetchProcess(processName);
  await fetchLogs();
  connect();
  subscribeStatus();
  if (store.currentProcess) {
    subscribeLogs(store.currentProcess.id);
  }
});

onUnmounted(() => {
  if (store.currentProcess) {
    unsubscribeLogs(store.currentProcess.id);
  }
});
</script>

<style scoped>
.process-detail {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-left h1 {
  margin: 0;
}

.error-state,
.empty-state {
  padding: 1rem 0;
}

.logs-card :deep(.n-card__content) {
  padding: 0;
}

.log-viewer {
  height: 400px;
  overflow-y: auto;
  font-family: var(--n-font-family-mono);
  font-size: 12px;
  background: var(--n-code-color);
  padding: 0.5rem;
  border-radius: 0 0 var(--n-border-radius) var(--n-border-radius);
}

.log-empty {
  color: var(--n-text-color-3);
  padding: 1rem;
  text-align: center;
}

.log-line {
  display: flex;
  gap: 0.75rem;
  padding: 0.125rem 0.5rem;
  line-height: 1.4;
}

.log-line:hover {
  background: var(--n-hover-color);
}

.log-timestamp {
  color: var(--n-text-color-3);
  flex-shrink: 0;
}

.log-content {
  white-space: pre-wrap;
  word-break: break-all;
}

.log-stderr {
  color: var(--n-error-color);
}

.state-warning {
  color: var(--n-error-color);
  font-size: 0.75rem;
  font-weight: 500;
}
</style>
