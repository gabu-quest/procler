<template>
  <div class="config-view">
    <div class="page-header">
      <div class="header-title">
        <img src="/procler.png" alt="Procler logo" class="config-logo" />
        <h1>Config</h1>
      </div>
      <n-button type="primary" @click="handleReload" :loading="store.loading">
        <template #icon>
          <PhArrowsClockwise />
        </template>
        Reload Config
      </n-button>
    </div>

    <n-spin :show="store.loading && !store.info">
      <div v-if="store.error" class="error-state">
        <n-alert type="error" :title="store.error" />
      </div>

      <template v-else-if="store.info">
        <n-grid :cols="2" :x-gap="20" :y-gap="20" responsive="screen" :item-responsive="true">
          <!-- Config Status Card -->
          <n-gi span="2 m:1">
            <n-card title="Configuration" class="status-card">
              <template #header-extra>
                <n-tag :type="store.info.config_exists ? 'success' : 'warning'" size="small">
                  {{ store.info.config_exists ? 'Active' : 'Not Found' }}
                </n-tag>
              </template>

              <n-descriptions :column="1" label-placement="left">
                <n-descriptions-item label="Config Directory">
                  <n-code>{{ store.info.config_dir }}</n-code>
                </n-descriptions-item>
                <n-descriptions-item label="Config File">
                  <n-code>{{ store.info.config_file }}</n-code>
                  <n-tag
                    :type="store.info.config_exists ? 'success' : 'default'"
                    size="small"
                    style="margin-left: 0.5rem"
                  >
                    {{ store.info.config_exists ? 'exists' : 'missing' }}
                  </n-tag>
                </n-descriptions-item>
                <n-descriptions-item label="Version">
                  v{{ store.info.version }}
                </n-descriptions-item>
              </n-descriptions>
            </n-card>
          </n-gi>

          <!-- Stats Card -->
          <n-gi span="2 m:1">
            <n-card title="Defined in Config" class="stats-card">
              <div class="stats-grid">
                <div class="stat-item">
                  <PhGear class="stat-icon" />
                  <div class="stat-value">{{ store.info.stats.processes }}</div>
                  <div class="stat-label">Processes</div>
                </div>
                <div class="stat-item">
                  <PhStack class="stat-icon" />
                  <div class="stat-value">{{ store.info.stats.groups }}</div>
                  <div class="stat-label">Groups</div>
                </div>
                <div class="stat-item">
                  <PhListChecks class="stat-icon" />
                  <div class="stat-value">{{ store.info.stats.recipes }}</div>
                  <div class="stat-label">Recipes</div>
                </div>
                <div class="stat-item">
                  <PhCodeBlock class="stat-icon" />
                  <div class="stat-value">{{ store.info.stats.snippets }}</div>
                  <div class="stat-label">Snippets</div>
                </div>
              </div>
            </n-card>
          </n-gi>

          <!-- Variables Card -->
          <n-gi span="2 m:1">
            <n-card title="Variables" class="vars-card">
              <template #header-extra>
                <n-tag :type="varsData.length > 0 ? 'info' : 'default'" size="small">
                  {{ varsData.length }} vars
                </n-tag>
              </template>

              <div v-if="varsData.length === 0" class="vars-empty">
                <n-empty description="No variables defined" size="small">
                  <template #extra>
                    <p class="empty-hint">
                      Add a <code>vars:</code> block in <code>.procler/config.yaml</code>
                    </p>
                  </template>
                </n-empty>
              </div>

              <div v-else>
                <p class="vars-hint">
                  Use <code>${VAR}</code> in commands, container names, and recipe exec steps.
                </p>
                <n-data-table
                  :columns="varsColumns"
                  :data="varsData"
                  :bordered="false"
                  size="small"
                />
              </div>
            </n-card>
          </n-gi>

          <!-- Changelog Card -->
          <n-gi span="2">
            <n-card title="Changelog" class="changelog-card">
              <template #header-extra>
                <n-space size="small">
                  <n-button size="small" @click="loadChangelog">
                    <template #icon>
                      <PhArrowsClockwise />
                    </template>
                    Refresh
                  </n-button>
                  <n-tag
                    :type="store.info.changelog_exists ? 'success' : 'default'"
                    size="small"
                  >
                    {{ store.info.changelog_exists ? 'tracking' : 'no changelog' }}
                  </n-tag>
                </n-space>
              </template>

              <div v-if="!store.info.changelog_exists" class="changelog-empty">
                <n-empty description="No changelog yet" size="small">
                  <template #extra>
                    <p class="empty-hint">
                      Actions will be logged to <code>changelog.log</code>
                    </p>
                  </template>
                </n-empty>
              </div>

              <div v-else-if="store.changelog.length === 0" class="changelog-empty">
                <n-empty description="Changelog is empty" size="small" />
              </div>

              <div v-else class="changelog-viewer">
                <div
                  v-for="(entry, idx) in store.changelog"
                  :key="idx"
                  :class="['changelog-entry', getEntryClass(entry)]"
                >
                  {{ formatEntry(entry) }}
                </div>
              </div>
            </n-card>
          </n-gi>

          <!-- Config Processes Preview -->
          <n-gi v-if="store.processes.length > 0" span="2">
            <n-card title="Process Definitions">
              <n-data-table
                :columns="processColumns"
                :data="store.processes"
                :bordered="false"
                size="small"
              />
            </n-card>
          </n-gi>
        </n-grid>
      </template>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { h, onMounted, computed } from "vue";
import {
  NButton,
  NCard,
  NGrid,
  NGi,
  NAlert,
  NSpin,
  NTag,
  NSpace,
  NDescriptions,
  NDescriptionsItem,
  NCode,
  NEmpty,
  NDataTable,
  type DataTableColumns,
  useMessage,
} from "naive-ui";
import {
  PhArrowsClockwise,
  PhGear,
  PhStack,
  PhListChecks,
  PhCodeBlock,
} from "@phosphor-icons/vue";
import { useConfigStore, type ConfigProcess } from "@/stores/config";
import { formatChangelogEntry, getChangelogAction, type ChangelogEntry } from "@/utils/changelog";

const store = useConfigStore();
const message = useMessage();

type ConfigVar = {
  name: string;
  value: string;
};

const varsData = computed<ConfigVar[]>(() => {
  const vars = store.info?.vars ?? {};
  return Object.entries(vars).map(([name, value]) => ({
    name,
    value,
  }));
});

const varsColumns: DataTableColumns<ConfigVar> = [
  {
    title: "Name",
    key: "name",
    width: 160,
    render: (row) => h(NTag, { size: "small", bordered: false }, { default: () => row.name }),
  },
  {
    title: "Value",
    key: "value",
    ellipsis: { tooltip: true },
    render: (row) => h(NCode, null, { default: () => row.value }),
  },
];

const processColumns: DataTableColumns<ConfigProcess> = [
  { title: "Name", key: "name", width: 150 },
  {
    title: "Context",
    key: "context",
    width: 100,
    render: (row) => h(NTag, { size: "small", bordered: false }, { default: () => row.context }),
  },
  { title: "Command", key: "command", ellipsis: { tooltip: true } },
  {
    title: "Container",
    key: "container",
    width: 120,
    render: (row) => row.container ?? "-",
  },
];

function getEntryClass(entry: ChangelogEntry): string {
  const action = getChangelogAction(entry);
  if (action === "EXECUTE") return "action-execute";
  if (action === "START") return "action-start";
  if (action === "STOP") return "action-stop";
  if (action === "CREATE") return "action-create";
  return "";
}

function formatEntry(entry: ChangelogEntry): string {
  return formatChangelogEntry(entry);
}

async function loadChangelog() {
  await store.fetchChangelog(100);
}

async function handleReload() {
  const result = await store.reloadConfig();
  if (result.success) {
    message.success("Config reloaded");
    await loadChangelog();
    await store.fetchProcesses();
  } else {
    message.error(result.error || "Failed to reload");
  }
}

onMounted(async () => {
  await store.fetchInfo();
  await store.fetchProcesses();
  await loadChangelog();
});
</script>

<style scoped>
.config-view {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.config-logo {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  opacity: 0.75;
  box-shadow: 0 0 0 1px rgba(0, 229, 255, 0.25);
}

.page-header h1 {
  margin: 0;
}

.error-state {
  padding: 2rem 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  background: var(--n-code-color);
  border-radius: var(--n-border-radius);
}

.stat-icon {
  font-size: 1.5rem;
  color: var(--n-primary-color);
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--n-text-color-1);
}

.stat-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--n-text-color-3);
}

.changelog-empty {
  padding: 1rem 0;
}

.vars-empty {
  padding: 1rem 0;
}

.vars-hint {
  color: var(--n-text-color-3);
  font-size: 0.8125rem;
  margin: 0 0 0.75rem;
}

.empty-hint {
  color: var(--n-text-color-3);
  font-size: 0.8125rem;
  margin: 0.5rem 0 0;
}

.empty-hint code {
  background: var(--n-code-color);
  padding: 0.125rem 0.375rem;
  border-radius: 3px;
}

.changelog-viewer {
  max-height: 400px;
  overflow-y: auto;
  font-family: var(--n-font-family-mono);
  font-size: 0.75rem;
  line-height: 1.6;
  background: var(--n-code-color);
  border-radius: var(--n-border-radius);
  padding: 0.75rem;
}

.changelog-entry {
  padding: 0.25rem 0.5rem;
  border-left: 3px solid transparent;
  white-space: pre-wrap;
  word-break: break-all;
}

.changelog-entry:hover {
  background: var(--n-hover-color);
}

.changelog-entry.action-execute {
  border-left-color: var(--n-primary-color);
}

.changelog-entry.action-start {
  border-left-color: var(--n-success-color);
}

.changelog-entry.action-stop {
  border-left-color: var(--n-warning-color);
}

.changelog-entry.action-create {
  border-left-color: var(--n-info-color);
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
