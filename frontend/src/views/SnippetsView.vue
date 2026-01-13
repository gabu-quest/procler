<template>
  <div class="snippets-view">
    <div class="page-header">
      <h1>Snippets</h1>
      <n-button type="primary" @click="showCreateModal = true">
        <template #icon>
          <PhPlus />
        </template>
        Save Snippet
      </n-button>
    </div>

    <n-spin :show="store.loading">
      <div v-if="store.error" class="error-state">
        <n-alert type="error" :title="store.error" />
      </div>

      <div v-else-if="store.snippets.length === 0" class="empty-state">
        <n-empty description="No snippets yet">
          <template #extra>
            <n-button type="primary" @click="showCreateModal = true">Create your first snippet</n-button>
          </template>
        </n-empty>
      </div>

      <n-grid v-else :cols="3" :x-gap="16" :y-gap="16" responsive="screen" :item-responsive="true">
        <n-gi v-for="snippet in store.snippets" :key="snippet.id" span="3 m:1 l:1">
          <n-card :title="snippet.name" hoverable>
            <template #header-extra>
              <n-space size="small">
                <n-button size="small" type="primary" @click="handleRun(snippet.name)">
                  <template #icon>
                    <PhPlay weight="fill" />
                  </template>
                  Run
                </n-button>
                <n-button size="small" quaternary type="error" @click="handleRemove(snippet.name)">
                  <template #icon>
                    <PhTrash />
                  </template>
                </n-button>
              </n-space>
            </template>

            <n-code :code="snippet.command" language="bash" word-wrap />

            <template v-if="snippet.description">
              <n-divider />
              <p class="snippet-description">{{ snippet.description }}</p>
            </template>

            <template v-if="snippet.tags" #footer>
              <n-space size="small">
                <n-tag v-for="tag in snippet.tags" :key="tag" size="small">
                  {{ tag }}
                </n-tag>
              </n-space>
            </template>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>

    <!-- Create Snippet Modal -->
    <n-modal v-model:show="showCreateModal" preset="dialog" title="Save Snippet">
      <n-form ref="formRef" :model="formData" :rules="formRules">
        <n-form-item label="Name" path="name">
          <n-input v-model:value="formData.name" placeholder="rebuild-api" />
        </n-form-item>
        <n-form-item label="Command" path="command">
          <n-input
            v-model:value="formData.command"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 6 }"
            placeholder="docker compose build api"
          />
        </n-form-item>
        <n-form-item label="Description" path="description">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 3 }"
            placeholder="What this snippet does (optional)"
          />
        </n-form-item>
        <n-form-item label="Tags" path="tags">
          <n-input v-model:value="formData.tags" placeholder="docker,build (optional)" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCreateModal = false">Cancel</n-button>
        <n-button type="primary" @click="handleCreate">Save</n-button>
      </template>
    </n-modal>

    <!-- Run Result Modal -->
    <n-modal v-model:show="showResultModal" preset="dialog" :title="`Result: ${runResult?.snippet ?? ''}`">
      <template v-if="runResult">
        <n-alert v-if="runResult.success" type="success" title="Completed successfully">
          Exit code: {{ runResult.exit_code }}
        </n-alert>
        <n-alert v-else type="error" :title="runResult.error ?? 'Execution failed'">
          Exit code: {{ runResult.exit_code }}
        </n-alert>
        <n-divider>Output</n-divider>
        <n-code :code="runResult.stdout || '(no output)'" language="bash" word-wrap />
        <template v-if="runResult.stderr">
          <n-divider>Stderr</n-divider>
          <n-code :code="runResult.stderr" language="bash" word-wrap />
        </template>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import {
  NButton,
  NCard,
  NGrid,
  NGi,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NAlert,
  NSpin,
  NCode,
  NTag,
  NSpace,
  NDivider,
  NEmpty,
  useMessage,
} from "naive-ui";
import { PhPlus, PhPlay, PhTrash } from "@phosphor-icons/vue";
import { useSnippetStore } from "@/stores/snippets";

const store = useSnippetStore();
const message = useMessage();

const showCreateModal = ref(false);
const showResultModal = ref(false);
const runResult = ref<{
  success: boolean;
  snippet?: string;
  exit_code?: number;
  stdout?: string;
  stderr?: string;
  error?: string;
} | null>(null);

const formRef = ref();
const formData = ref({
  name: "",
  command: "",
  description: "",
  tags: "",
});

const formRules = {
  name: { required: true, message: "Name is required" },
  command: { required: true, message: "Command is required" },
};

async function handleCreate() {
  const result = await store.createSnippet({
    name: formData.value.name,
    command: formData.value.command,
    description: formData.value.description || undefined,
    tags: formData.value.tags || undefined,
  });
  if (result.success) {
    message.success(`Saved snippet: ${formData.value.name}`);
    showCreateModal.value = false;
    formData.value = { name: "", command: "", description: "", tags: "" };
  } else {
    message.error(result.error);
  }
}

async function handleRemove(name: string) {
  const result = await store.removeSnippet(name);
  if (result.success) {
    message.success(`Removed snippet: ${name}`);
  } else {
    message.error(result.error);
  }
}

async function handleRun(name: string) {
  message.info(`Running snippet: ${name}`);
  const result = await store.runSnippet(name);
  runResult.value = { ...result.data, snippet: name, success: result.success, error: result.error };
  showResultModal.value = true;
}

onMounted(() => {
  store.fetchSnippets();
});
</script>

<style scoped>
.snippets-view {
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

.snippet-description {
  color: var(--n-text-color-2);
  font-size: 0.875rem;
  margin: 0;
}
</style>
