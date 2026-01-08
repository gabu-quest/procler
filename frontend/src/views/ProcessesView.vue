<template>
  <div class="processes-view">
    <div class="page-header">
      <h1>Processes</h1>
      <n-button type="primary" @click="showCreateModal = true">
        <template #icon>
          <PhPlus />
        </template>
        Define Process
      </n-button>
    </div>

    <n-spin :show="store.loading">
      <div v-if="store.error" class="error-state">
        <n-alert type="error" :title="store.error" />
      </div>

      <n-data-table
        v-else
        :columns="columns"
        :data="store.processes"
        :row-key="(row: Process) => row.id"
        :bordered="false"
        striped
      />
    </n-spin>

    <!-- Create Process Modal -->
    <n-modal v-model:show="showCreateModal" preset="dialog" title="Define Process">
      <n-form ref="formRef" :model="formData" :rules="formRules">
        <n-form-item label="Name" path="name">
          <n-input v-model:value="formData.name" placeholder="my-api" />
        </n-form-item>
        <n-form-item label="Command" path="command">
          <n-input v-model:value="formData.command" placeholder="uvicorn main:app --port 8000" />
        </n-form-item>
        <n-form-item label="Context" path="context">
          <n-select v-model:value="formData.context" :options="contextOptions" />
        </n-form-item>
        <n-form-item v-if="formData.context === 'docker'" label="Container" path="container">
          <n-input v-model:value="formData.container" placeholder="container-name" />
        </n-form-item>
        <n-form-item label="Working Directory" path="cwd">
          <n-input v-model:value="formData.cwd" placeholder="/path/to/project (optional)" />
        </n-form-item>
        <n-form-item label="Tags" path="tags">
          <n-input v-model:value="formData.tags" placeholder="api,backend (optional)" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCreateModal = false">Cancel</n-button>
        <n-button type="primary" @click="handleCreate">Create</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from "vue";
import { useRouter } from "vue-router";
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
  useMessage,
  type DataTableColumns,
} from "naive-ui";
import { PhPlus, PhPlay, PhStop, PhArrowsClockwise, PhTrash, PhEye } from "@phosphor-icons/vue";
import { useProcessStore, type Process } from "@/stores/processes";
import { useWebSocket } from "@/composables/useWebSocket";

const router = useRouter();
const store = useProcessStore();
const message = useMessage();
const { connect, subscribeStatus } = useWebSocket();

const showCreateModal = ref(false);
const formRef = ref();
const formData = ref({
  name: "",
  command: "",
  context: "local",
  container: "",
  cwd: "",
  tags: "",
});

const formRules = {
  name: { required: true, message: "Name is required" },
  command: { required: true, message: "Command is required" },
};

const contextOptions = [
  { label: "Local", value: "local" },
  { label: "Docker", value: "docker" },
];

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

const columns: DataTableColumns<Process> = [
  {
    title: "Name",
    key: "name",
    render: (row) =>
      h(
        "a",
        {
          style: { color: "var(--n-primary-color)", cursor: "pointer" },
          onClick: () => router.push(`/process/${row.name}`),
        },
        row.name
      ),
  },
  {
    title: "Status",
    key: "status",
    width: 100,
    render: (row) =>
      h(
        NTag,
        { type: statusColor(row.status), size: "small" },
        { default: () => row.status }
      ),
  },
  {
    title: "PID",
    key: "pid",
    width: 80,
    render: (row) => row.pid ?? "-",
  },
  {
    title: "Context",
    key: "context",
    width: 100,
    render: (row) =>
      h(
        NTag,
        { size: "small", bordered: false },
        { default: () => row.context }
      ),
  },
  {
    title: "Command",
    key: "command",
    ellipsis: { tooltip: true },
  },
  {
    title: "Actions",
    key: "actions",
    width: 200,
    render: (row) =>
      h(NSpace, { size: "small" }, () => [
        h(
          NButton,
          {
            size: "small",
            quaternary: true,
            title: "View",
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
            title: "Start",
            disabled: row.status === "running",
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
            title: "Stop",
            disabled: row.status !== "running",
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
            title: "Restart",
            onClick: () => handleRestart(row.name),
          },
          { icon: () => h(PhArrowsClockwise, { weight: "regular" }) }
        ),
        h(
          NButton,
          {
            size: "small",
            quaternary: true,
            type: "error",
            title: "Remove",
            onClick: () => handleRemove(row.name),
          },
          { icon: () => h(PhTrash, { weight: "regular" }) }
        ),
      ]),
  },
];

async function handleStart(name: string) {
  const result = await store.startProcess(name);
  if (result.success) {
    message.success(`Started ${name}`);
  } else {
    message.error(result.error);
  }
}

async function handleStop(name: string) {
  const result = await store.stopProcess(name);
  if (result.success) {
    message.success(`Stopped ${name}`);
  } else {
    message.error(result.error);
  }
}

async function handleRestart(name: string) {
  const result = await store.restartProcess(name);
  if (result.success) {
    message.success(`Restarted ${name}`);
  } else {
    message.error(result.error);
  }
}

async function handleRemove(name: string) {
  const result = await store.removeProcess(name);
  if (result.success) {
    message.success(`Removed ${name}`);
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
    message.success(`Created ${formData.value.name}`);
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
</style>
