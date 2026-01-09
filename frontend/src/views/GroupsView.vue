<template>
  <div class="groups-view">
    <div class="page-header">
      <h1>Groups</h1>
      <n-button @click="refreshAll" :loading="store.loading">
        <template #icon>
          <PhArrowsClockwise />
        </template>
        Refresh
      </n-button>
    </div>

    <n-spin :show="store.loading && !store.groups.length">
      <div v-if="store.error" class="error-state">
        <n-alert type="error" :title="store.error" />
      </div>

      <div v-else-if="store.groups.length === 0" class="empty-state">
        <n-empty description="No groups defined">
          <template #extra>
            <p class="empty-hint">
              Define groups in your <code>.procler/config.yaml</code> file
            </p>
          </template>
        </n-empty>
      </div>

      <n-grid v-else :cols="2" :x-gap="20" :y-gap="20" responsive="screen" :item-responsive="true">
        <n-gi v-for="group in store.groups" :key="group.name" span="2 m:1">
          <n-card :title="group.name" class="group-card" hoverable>
            <template #header-extra>
              <n-space size="small">
                <n-button
                  size="small"
                  type="success"
                  :loading="store.operationInProgress === group.name && isStarting"
                  :disabled="store.operationInProgress !== null"
                  @click="handleStartGroup(group.name)"
                >
                  <template #icon>
                    <PhPlay weight="fill" />
                  </template>
                  Start All
                </n-button>
                <n-button
                  size="small"
                  type="warning"
                  :loading="store.operationInProgress === group.name && !isStarting"
                  :disabled="store.operationInProgress !== null"
                  @click="handleStopGroup(group.name)"
                >
                  <template #icon>
                    <PhStop weight="fill" />
                  </template>
                  Stop All
                </n-button>
              </n-space>
            </template>

            <p v-if="group.description" class="group-description">{{ group.description }}</p>

            <div class="process-list">
              <div class="list-header">
                <span class="header-label">Start Order</span>
                <n-tag size="small" :bordered="false">{{ group.processes.length }} processes</n-tag>
              </div>

              <div class="process-items">
                <div
                  v-for="(proc, idx) in group.processes"
                  :key="proc"
                  class="process-item"
                >
                  <span class="process-index">{{ idx + 1 }}</span>
                  <span class="process-name">{{ proc }}</span>
                  <n-tag
                    v-if="groupStatuses[group.name]?.[proc]"
                    :type="statusType(groupStatuses[group.name][proc].status)"
                    size="small"
                  >
                    {{ groupStatuses[group.name][proc].status }}
                  </n-tag>
                  <!-- Linux state warning -->
                  <n-tooltip v-if="groupStatuses[group.name]?.[proc]?.linux_state?.state_code === 'D'">
                    <template #trigger>
                      <n-tag type="error" size="small">D (unkillable)</n-tag>
                    </template>
                    {{ groupStatuses[group.name]?.[proc]?.linux_state?.state_description }}
                  </n-tooltip>
                  <n-tooltip v-else-if="groupStatuses[group.name]?.[proc]?.linux_state?.state_code === 'Z'">
                    <template #trigger>
                      <n-tag type="warning" size="small">Z (zombie)</n-tag>
                    </template>
                    {{ groupStatuses[group.name]?.[proc]?.linux_state?.state_description }}
                  </n-tooltip>
                  <!-- Health status -->
                  <n-tag
                    v-if="groupStatuses[group.name]?.[proc]?.health"
                    :type="healthType(groupStatuses[group.name]?.[proc]?.health?.status ?? 'unknown')"
                    size="small"
                  >
                    {{ groupStatuses[group.name]?.[proc]?.health?.status }}
                  </n-tag>
                  <!-- Dependencies -->
                  <n-tooltip v-if="groupStatuses[group.name]?.[proc]?.depends_on?.length">
                    <template #trigger>
                      <PhArrowBendDownRight class="dep-icon" />
                    </template>
                    Depends on: {{ formatDependencies(groupStatuses[group.name]?.[proc]?.depends_on) }}
                  </n-tooltip>
                </div>
              </div>

              <div v-if="group.stop_order.join(',') !== [...group.processes].reverse().join(',')" class="stop-order">
                <n-divider />
                <span class="order-label">Stop Order:</span>
                <span class="order-processes">{{ group.stop_order.join(' → ') }}</span>
              </div>
            </div>

            <!-- Operation Result -->
            <template v-if="lastResults[group.name]">
              <n-divider />
              <div class="operation-result">
                <n-alert
                  :type="lastResults[group.name].success ? 'success' : 'error'"
                  :title="lastResults[group.name].success ? 'Operation completed' : 'Operation had errors'"
                  closable
                  @close="clearResult(group.name)"
                >
                  <div class="result-list">
                    <div
                      v-for="result in lastResults[group.name].results"
                      :key="result.process"
                      class="result-item"
                    >
                      <PhCheckCircle v-if="result.success" weight="fill" class="icon-success" />
                      <PhXCircle v-else weight="fill" class="icon-error" />
                      <span>{{ result.process }}</span>
                      <span v-if="result.error" class="result-error">{{ result.error }}</span>
                    </div>
                  </div>
                </n-alert>
              </div>
            </template>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import {
  NButton,
  NCard,
  NGrid,
  NGi,
  NAlert,
  NSpin,
  NTag,
  NSpace,
  NDivider,
  NEmpty,
  NTooltip,
  useMessage,
} from "naive-ui";
import { PhPlay, PhStop, PhArrowsClockwise, PhCheckCircle, PhXCircle, PhArrowBendDownRight } from "@phosphor-icons/vue";
import { useGroupStore } from "@/stores/groups";

const store = useGroupStore();
const message = useMessage();

const isStarting = ref(true);
interface ProcessStatus {
  status: string;
  linux_state?: { state_code: string; state_description: string };
  health?: { status: string };
  depends_on?: { name: string; condition: string }[];
}
const groupStatuses = reactive<Record<string, Record<string, ProcessStatus>>>({});
const lastResults = reactive<Record<string, { success: boolean; results: { process: string; success: boolean; error?: string }[] }>>({});

function statusType(status: string) {
  switch (status) {
    case "running":
      return "success";
    case "stopped":
      return "default";
    case "failed":
      return "error";
    case "not_defined":
      return "warning";
    default:
      return "default";
  }
}

function healthType(status: string) {
  switch (status) {
    case "healthy":
      return "success";
    case "unhealthy":
      return "error";
    case "starting":
      return "info";
    default:
      return "default";
  }
}

function formatDependencies(deps: { name: string; condition: string }[] | undefined): string {
  if (!deps) return "";
  return deps.map(d => `${d.name} (${d.condition})`).join(", ");
}

async function refreshAll() {
  await store.fetchGroups();
  // Fetch status for each group
  for (const group of store.groups) {
    await fetchGroupStatus(group.name);
  }
}

async function fetchGroupStatus(name: string) {
  try {
    const response = await fetch(`/api/groups/${name}/status`);
    const data = await response.json();
    if (data.success) {
      const statusMap: Record<string, { status: string }> = {};
      for (const s of data.data.statuses) {
        statusMap[s.process] = { status: s.status };
      }
      groupStatuses[name] = statusMap;
    }
  } catch (e) {
    console.error("Failed to fetch group status:", e);
  }
}

async function handleStartGroup(name: string) {
  isStarting.value = true;
  message.info(`Starting group: ${name}`);
  const result = await store.startGroup(name);
  if (result.success) {
    message.success(`Started group: ${name}`);
  } else {
    message.error(`Failed to start group: ${result.error}`);
  }
  lastResults[name] = { success: result.success, results: result.data?.results ?? [] };
  await fetchGroupStatus(name);
}

async function handleStopGroup(name: string) {
  isStarting.value = false;
  message.info(`Stopping group: ${name}`);
  const result = await store.stopGroup(name);
  if (result.success) {
    message.success(`Stopped group: ${name}`);
  } else {
    message.error(`Failed to stop group: ${result.error}`);
  }
  lastResults[name] = { success: result.success, results: result.data?.results ?? [] };
  await fetchGroupStatus(name);
}

function clearResult(name: string) {
  delete lastResults[name];
}

onMounted(refreshAll);
</script>

<style scoped>
.groups-view {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.page-header h1 {
  margin: 0;
}

.error-state,
.empty-state {
  padding: 2rem 0;
}

.empty-hint {
  color: var(--n-text-color-3);
  font-size: 0.875rem;
  margin: 0.5rem 0 0;
}

.empty-hint code {
  background: var(--n-code-color);
  padding: 0.125rem 0.375rem;
  border-radius: 3px;
}

.group-card {
  transition: transform 0.15s ease;
}

.group-description {
  color: var(--n-text-color-2);
  font-size: 0.875rem;
  margin: 0 0 1rem;
}

.process-list {
  background: var(--n-code-color);
  border-radius: var(--n-border-radius);
  padding: 0.75rem;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--n-divider-color);
}

.header-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--n-text-color-3);
}

.process-items {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.process-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.25rem 0;
}

.process-index {
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--n-primary-color);
  color: var(--n-base-color);
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 50%;
}

.process-name {
  flex: 1;
  font-family: var(--n-font-family-mono);
  font-size: 0.875rem;
}

.stop-order {
  margin-top: 0.5rem;
  font-size: 0.8125rem;
}

.order-label {
  color: var(--n-text-color-3);
  margin-right: 0.5rem;
}

.order-processes {
  font-family: var(--n-font-family-mono);
  color: var(--n-warning-color);
}

.operation-result {
  margin-top: 0.5rem;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.icon-success {
  color: var(--n-success-color);
}

.icon-error {
  color: var(--n-error-color);
}

.result-error {
  color: var(--n-error-color);
  font-size: 0.75rem;
}

.dep-icon {
  color: var(--n-text-color-3);
  font-size: 0.875rem;
  cursor: help;
}
</style>
