<template>
  <div class="snippets-view">
    <div class="page-header">
      <h1>{{ $t('snippets.title') }}</h1>
      <n-button type="primary" @click="showCreateModal = true">
        <template #icon>
          <PhPlus />
        </template>
        {{ $t('snippets.saveSnippet') }}
      </n-button>
    </div>

    <n-spin :show="store.loading">
      <div v-if="store.error" class="error-state">
        <n-alert type="error" :title="store.error" />
      </div>

      <div v-else-if="store.snippets.length === 0" class="empty-state">
        <n-empty :description="$t('snippets.noSnippets')">
          <template #extra>
            <n-button type="primary" @click="showCreateModal = true">{{ $t('snippets.createFirst') }}</n-button>
          </template>
        </n-empty>
      </div>

      <n-grid v-else :cols="3" :x-gap="16" :y-gap="16" responsive="screen" :item-responsive="true">
        <n-gi v-for="snippet in store.snippets" :key="snippet.id" span="3 m:1 l:1">
          <n-card :title="snippet.name" hoverable>
            <template #header-extra>
              <n-space size="small">
                <n-button
                  size="small"
                  type="primary"
                  :aria-label="$t('common.run') + ' ' + snippet.name"
                  @click="handleRun(snippet.name)"
                >
                  <template #icon>
                    <PhPlay weight="fill" />
                  </template>
                  {{ $t('common.run') }}
                </n-button>
                <n-popconfirm @positive-click="handleRemove(snippet.name)">
                  <template #trigger>
                    <n-button
                      size="small"
                      quaternary
                      type="error"
                      :aria-label="$t('common.delete') + ' ' + snippet.name"
                      :title="$t('common.delete')"
                    >
                      <template #icon>
                        <PhTrash />
                      </template>
                    </n-button>
                  </template>
                  {{ $t('snippets.deleteConfirm', { name: snippet.name }) }}
                </n-popconfirm>
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
    <n-modal v-model:show="showCreateModal" preset="dialog" :title="$t('snippets.modal.saveTitle')">
      <n-form ref="formRef" :model="formData" :rules="formRules">
        <n-form-item :label="$t('snippets.form.name')" path="name">
          <n-input v-model:value="formData.name" :placeholder="$t('snippets.form.namePlaceholder')" />
        </n-form-item>
        <n-form-item :label="$t('snippets.form.command')" path="command">
          <n-input
            v-model:value="formData.command"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 6 }"
            :placeholder="$t('snippets.form.commandPlaceholder')"
          />
        </n-form-item>
        <n-form-item :label="$t('snippets.form.description')" path="description">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 3 }"
            :placeholder="$t('snippets.form.descriptionPlaceholder')"
          />
        </n-form-item>
        <n-form-item :label="$t('snippets.form.tags')" path="tags">
          <n-input v-model:value="formData.tags" :placeholder="$t('snippets.form.tagsPlaceholder')" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCreateModal = false">{{ $t('common.cancel') }}</n-button>
        <n-button type="primary" @click="handleCreate">{{ $t('common.save') }}</n-button>
      </template>
    </n-modal>

    <!-- Run Result Modal -->
    <n-modal v-model:show="showResultModal" preset="dialog" :title="$t('snippets.modal.resultTitle', { name: runResult?.snippet ?? '' })">
      <template v-if="runResult">
        <n-alert v-if="runResult.success" type="success" :title="$t('snippets.result.completedSuccessfully')">
          {{ $t('snippets.result.exitCode', { code: runResult.exit_code }) }}
        </n-alert>
        <n-alert v-else type="error" :title="runResult.error ?? $t('snippets.result.executionFailed')">
          {{ $t('snippets.result.exitCode', { code: runResult.exit_code }) }}
        </n-alert>
        <n-divider>{{ $t('snippets.result.output') }}</n-divider>
        <n-code :code="runResult.stdout || $t('snippets.result.noOutput')" language="bash" word-wrap />
        <template v-if="runResult.stderr">
          <n-divider>{{ $t('snippets.result.stderr') }}</n-divider>
          <n-code :code="runResult.stderr" language="bash" word-wrap />
        </template>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";
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
  NPopconfirm,
  useMessage,
} from "naive-ui";
import { PhPlus, PhPlay, PhTrash } from "@phosphor-icons/vue";
import { useSnippetStore } from "@/stores/snippets";

const { t } = useI18n();
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

const formRules = computed(() => ({
  name: { required: true, message: t('snippets.form.nameRequired') },
  command: { required: true, message: t('snippets.form.commandRequired') },
}));

async function handleCreate() {
  const result = await store.createSnippet({
    name: formData.value.name,
    command: formData.value.command,
    description: formData.value.description || undefined,
    tags: formData.value.tags || undefined,
  });
  if (result.success) {
    message.success(t('snippets.messages.saved', { name: formData.value.name }));
    showCreateModal.value = false;
    formData.value = { name: "", command: "", description: "", tags: "" };
  } else {
    message.error(result.error);
  }
}

async function handleRemove(name: string) {
  const result = await store.removeSnippet(name);
  if (result.success) {
    message.success(t('snippets.messages.removed', { name }));
  } else {
    message.error(result.error);
  }
}

async function handleRun(name: string) {
  message.info(t('snippets.messages.running', { name }));
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
