<template>
  <div class="processes-view">
    <div class="page-header">
      <h1>{{ $t('processes.title') }}</h1>
      <n-button type="primary" @click="showCreateModal = true">
        <template #icon>
          <PhPlus />
        </template>
        {{ $t('processes.defineProcess') }}
      </n-button>
    </div>

    <n-spin :show="store.loading">
      <div v-if="store.error" class="error-state">
        <n-alert type="error" :title="store.error">
          <template #icon>
            <PhWarningCircle weight="fill" />
          </template>
        </n-alert>
        <n-button type="primary" @click="store.fetchProcesses()" style="margin-top: 1rem">
          <template #icon>
            <PhArrowsClockwise />
          </template>
          {{ $t('common.retry') }}
        </n-button>
      </div>

      <div v-else class="table-shell">
        <div class="table-toolbar">
          <div class="table-title">
            <span class="title-label">{{ $t('processes.processRegistry') }}</span>
            <span class="title-sub">{{ $t('processes.liveInventory') }}</span>
          </div>
          <div class="table-meta">
            <n-tag size="small" type="success" :bordered="false">
              <template #icon>
                <PhPlay weight="fill" />
              </template>
              {{ $t('processes.runningCount', { count: store.runningCount }) }}
            </n-tag>
            <n-tag size="small" :bordered="false">
              <template #icon>
                <PhListBullets />
              </template>
              {{ $t('processes.totalCount', { count: store.processes.length }) }}
            </n-tag>
          </div>
        </div>

        <div v-if="store.processes.length === 0" class="empty-table">
          <n-empty :description="$t('processes.noProcesses')" size="small">
            <template #extra>
              <p class="empty-hint">{{ $t('processes.defineHint', { config: '' }) }}<code>.procler/config.yaml</code></p>
            </template>
          </n-empty>
        </div>

        <n-data-table
          v-else
          class="processes-table"
          :columns="columns"
          :data="store.processes"
          :row-key="(row: Process) => row.id"
          :bordered="false"
          size="large"
          striped
        />
      </div>
    </n-spin>

    <n-modal v-model:show="showCommandModal" preset="card" :title="commandModalTitle" style="max-width: 720px;">
      <div class="command-modal">
        <pre class="command-code"><code>{{ selectedCommand }}</code></pre>
      </div>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCommandModal = false">{{ $t('common.close') }}</n-button>
          <n-button type="primary" :disabled="!selectedCommand" @click="copyCommand">{{ $t('common.copy') }}</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Create Process Modal -->
    <n-modal v-model:show="showCreateModal" preset="dialog" :title="$t('processes.modal.defineTitle')">
      <n-form ref="formRef" :model="formData" :rules="formRules">
        <n-form-item :label="$t('processes.form.name')" path="name">
          <n-input v-model:value="formData.name" :placeholder="$t('processes.form.namePlaceholder')" />
        </n-form-item>
        <n-form-item :label="$t('processes.form.command')" path="command">
          <n-input v-model:value="formData.command" :placeholder="$t('processes.form.commandPlaceholder')" />
        </n-form-item>
        <n-form-item :label="$t('processes.form.context')" path="context">
          <n-select v-model:value="formData.context" :options="contextOptions" />
        </n-form-item>
        <n-form-item v-if="formData.context === 'docker'" :label="$t('processes.form.container')" path="container">
          <n-input v-model:value="formData.container" :placeholder="$t('processes.form.containerPlaceholder')" />
        </n-form-item>
        <n-form-item :label="$t('processes.form.workingDirectory')" path="cwd">
          <n-input v-model:value="formData.cwd" :placeholder="$t('processes.form.workingDirectoryPlaceholder')" />
        </n-form-item>
        <n-form-item :label="$t('processes.form.tags')" path="tags">
          <n-input v-model:value="formData.tags" :placeholder="$t('processes.form.tagsPlaceholder')" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCreateModal = false">{{ $t('common.cancel') }}</n-button>
        <n-button type="primary" @click="handleCreate">{{ $t('common.create') }}</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, computed } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import {
  NButton,
  NDataTable,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NAlert,
  NSpin,
  NTag,
  NSpace,
  NEmpty,
  NPopconfirm,
  useMessage,
  type DataTableColumns,
} from "naive-ui";
import { PhPlus, PhPlay, PhStop, PhArrowsClockwise, PhTrash, PhEye, PhListBullets, PhCodeBlock, PhWarningCircle } from "@phosphor-icons/vue";
import { useProcessStore, type Process } from "@/stores/processes";
import { useWebSocket } from "@/composables/useWebSocket";

const router = useRouter();
const { t } = useI18n();
const store = useProcessStore();
const message = useMessage();
const { connect, subscribeStatus } = useWebSocket();

const showCreateModal = ref(false);
const showCommandModal = ref(false);
const selectedCommand = ref("");
const selectedCommandName = ref("");
const formRef = ref();
const formData = ref({
  name: "",
  command: "",
  context: "local",
  container: "",
  cwd: "",
  tags: "",
});

const formRules = computed(() => ({
  name: { required: true, message: t('processes.form.nameRequired') },
  command: { required: true, message: t('processes.form.commandRequired') },
}));

const contextOptions = computed(() => [
  { label: t('common.local'), value: "local" },
  { label: t('common.docker'), value: "docker" },
]);

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

function linuxStateType(code?: string) {
  switch (code) {
    case "D":
    case "Z":
      return "error";
    case "T":
    case "t":
      return "warning";
    case "S":
    case "I":
      return "info";
    default:
      return "default";
  }
}

function linuxStateLabel(code?: string, name?: string) {
  if (!code || !name || code === "R") return null;
  return `${code} ${name}`;
}

const commandModalTitle = computed(() =>
  selectedCommandName.value ? `${t('processes.modal.commandTitle')} — ${selectedCommandName.value}` : t('processes.modal.commandTitle')
);

async function copyCommand() {
  if (!selectedCommand.value) return;
  try {
    await navigator.clipboard.writeText(selectedCommand.value);
    message.success(t('processes.messages.commandCopied'));
  } catch {
    message.error(t('processes.messages.copyFailed'));
  }
}

function openCommand(row: Process) {
  selectedCommand.value = row.command;
  selectedCommandName.value = row.name;
  showCommandModal.value = true;
}

const columns = computed<DataTableColumns<Process>>(() => [
  {
    title: t('processes.columns.name'),
    key: "name",
    minWidth: 180,
    render: (row) =>
      h(
        "a",
        {
          class: "name-link",
          style: { color: "var(--n-primary-color)", cursor: "pointer" },
          title: row.name,
          onClick: () => router.push(`/process/${row.name}`),
        },
        row.name
      ),
  },
  {
    title: t('processes.columns.status'),
    key: "status",
    width: 170,
    render: (row) =>
      h("div", { class: "status-cell" }, [
        h(NTag, { type: statusColor(row.status), size: "small" }, { default: () => row.status }),
        linuxStateLabel(row.linux_state?.state_code, row.linux_state?.state_name)
          ? h(
            NTag,
            { type: linuxStateType(row.linux_state?.state_code), size: "small" },
            { default: () => linuxStateLabel(row.linux_state?.state_code, row.linux_state?.state_name) }
          )
          : null,
      ]),
  },
  {
    title: t('processes.columns.pid'),
    key: "pid",
    width: 100,
    render: (row) =>
      h("span", { class: "pid-cell" }, row.pid ?? "-"),
  },
  {
    title: t('processes.columns.context'),
    key: "context",
    width: 110,
    render: (row) => {
      const context = row.context ?? row.context_type ?? "local";
      const tagType = context === "docker" ? "info" : "default";
      return h(NTag, { size: "small", bordered: false, type: tagType }, { default: () => context });
    },
  },
  {
    title: t('processes.columns.command'),
    key: "command",
    width: 420,
    ellipsis: { tooltip: true },
    render: (row) =>
      h(
        NButton,
        {
          text: true,
          class: "command-button",
          title: row.command,
          onClick: () => openCommand(row),
        },
        {
          icon: () => h(PhCodeBlock, { weight: "regular" }),
          default: () => h("span", { class: "command-text" }, row.command),
        }
      ),
  },
  {
    title: t('processes.columns.actions'),
    key: "actions",
    width: 220,
    render: (row) =>
      h("div", { class: "action-buttons", role: "group", "aria-label": `Actions for ${row.name}` }, [
        h(
          NButton,
          {
            size: "small",
            quaternary: true,
            circle: true,
            title: t('processes.actions.viewDetails'),
            "aria-label": `${t('processes.actions.viewDetails')} ${row.name}`,
            onClick: () => router.push(`/process/${row.name}`),
          },
          { icon: () => h(PhEye, { weight: "regular" }) }
        ),
        h(
          NButton,
          {
            size: "small",
            quaternary: true,
            type: "success",
            circle: true,
            title: t('processes.actions.startProcess'),
            "aria-label": `${t('common.start')} ${row.name}`,
            loading: store.isActionLoading(row.name, "start"),
            disabled: row.status === "running" || store.isActionLoading(row.name, "start"),
            onClick: () => handleStart(row.name),
          },
          { icon: () => h(PhPlay, { weight: "fill" }) }
        ),
        h(
          NButton,
          {
            size: "small",
            quaternary: true,
            type: "warning",
            circle: true,
            title: t('processes.actions.stopProcess'),
            "aria-label": `${t('common.stop')} ${row.name}`,
            loading: store.isActionLoading(row.name, "stop"),
            disabled: row.status !== "running" || store.isActionLoading(row.name, "stop"),
            onClick: () => handleStop(row.name),
          },
          { icon: () => h(PhStop, { weight: "fill" }) }
        ),
        h(
          NButton,
          {
            size: "small",
            quaternary: true,
            type: "info",
            circle: true,
            title: t('processes.actions.restartProcess'),
            "aria-label": `${t('common.restart')} ${row.name}`,
            loading: store.isActionLoading(row.name, "restart"),
            disabled: store.isActionLoading(row.name, "restart"),
            onClick: () => handleRestart(row.name),
          },
          { icon: () => h(PhArrowsClockwise, { weight: "regular" }) }
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleRemove(row.name),
          },
          {
            trigger: () => h(
              NButton,
              {
                size: "small",
                quaternary: true,
                type: "error",
                circle: true,
                title: t('processes.actions.removeProcess'),
                "aria-label": `${t('common.remove')} ${row.name}`,
                loading: store.isActionLoading(row.name, "remove"),
                disabled: store.isActionLoading(row.name, "remove"),
              },
              { icon: () => h(PhTrash, { weight: "regular" }) }
            ),
            default: () => t('processes.messages.removeConfirm', { name: row.name }),
          }
        ),
      ]),
  },
]);

async function handleStart(name: string) {
  const result = await store.startProcess(name);
  if (result.success) {
    message.success(t('processes.messages.started', { name }));
  } else {
    message.error(result.error);
  }
}

async function handleStop(name: string) {
  const result = await store.stopProcess(name);
  if (result.success) {
    message.success(t('processes.messages.stopped', { name }));
  } else {
    message.error(result.error);
  }
}

async function handleRestart(name: string) {
  const result = await store.restartProcess(name);
  if (result.success) {
    message.success(t('processes.messages.restarted', { name }));
  } else {
    message.error(result.error);
  }
}

async function handleRemove(name: string) {
  const result = await store.removeProcess(name);
  if (result.success) {
    message.success(t('processes.messages.removed', { name }));
  } else {
    message.error(result.error);
  }
}

async function handleCreate() {
  const result = await store.createProcess({
    name: formData.value.name,
    command: formData.value.command,
    context: formData.value.context,
    container: formData.value.container || undefined,
    cwd: formData.value.cwd || undefined,
    tags: formData.value.tags || undefined,
  });
  if (result.success) {
    message.success(t('processes.messages.created', { name: formData.value.name }));
    showCreateModal.value = false;
    formData.value = { name: "", command: "", context: "local", container: "", cwd: "", tags: "" };
  } else {
    message.error(result.error);
  }
}

onMounted(async () => {
  await store.fetchProcesses();
  connect();
  subscribeStatus();
});
</script>

<style scoped>
.processes-view {
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

.error-state {
  padding: 1rem 0;
}

.table-shell {
  position: relative;
  padding: 0.75rem;
  border-radius: 12px;
  background:
    linear-gradient(180deg, rgba(0, 229, 255, 0.08), rgba(7, 8, 13, 0.02) 55%),
    var(--n-card-color);
  border: 1px solid var(--n-border-color);
  box-shadow: 0 22px 50px rgba(0, 0, 0, 0.35);
}

.table-shell::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 12px;
  pointer-events: none;
  border: 1px solid rgba(0, 229, 255, 0.14);
}

.table-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.25rem 0.5rem 0.75rem;
}

.table-title {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.title-label {
  font-family: var(--ds-font-heading);
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--n-text-color-3);
}

.title-sub {
  font-size: 0.95rem;
  color: var(--n-text-color-2);
}

.table-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.empty-table {
  padding: 1.25rem 0 1.5rem;
}

.empty-hint {
  color: var(--n-text-color-3);
  font-size: 0.85rem;
  margin: 0.5rem 0 0;
}

.empty-hint code {
  background: var(--n-code-color);
  padding: 0.125rem 0.375rem;
  border-radius: 3px;
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.pid-cell {
  font-family: var(--n-font-family-mono);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.processes-table :deep(.n-data-table) {
  background: transparent;
  border-radius: 10px;
}

.processes-table :deep(.n-data-table-base-table) {
  table-layout: fixed;
}

.processes-table :deep(.n-data-table-thead) {
  background: transparent;
}

.processes-table :deep(.n-data-table-th) {
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--n-text-color-3);
}

.processes-table :deep(.n-data-table-td) {
  font-size: 1rem;
  padding-top: 0.75rem;
  padding-bottom: 0.75rem;
}

.name-link {
  display: inline-flex;
  align-items: center;
  max-width: 240px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.action-buttons {
  display: flex;
  flex-wrap: nowrap;
  gap: 0.4rem;
  align-items: center;
  white-space: nowrap;
}

.command-button {
  font-family: var(--n-font-family-mono);
  font-size: 0.85rem;
  width: 100%;
  display: inline-flex;
  justify-content: flex-start;
  align-items: center;
  gap: 0.35rem;
  padding: 0.15rem 0.35rem;
  border-radius: 6px;
  background: var(--n-code-color);
  border: 1px solid var(--n-border-color);
  overflow: hidden;
}

.command-button :deep(.n-button__content) {
  max-width: 100%;
  overflow: hidden;
}

.command-text {
  display: block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.command-modal {
  padding: 0;
  background: transparent;
  border: none;
}

.command-code {
  background: var(--n-code-color);
  border-radius: var(--n-border-radius);
  border: 1px solid var(--n-border-color);
  font-family: var(--n-font-family-mono);
  font-size: 0.9rem;
  line-height: 1.6;
  margin: 0;
  padding: 0.75rem;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
