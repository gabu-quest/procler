<template>
  <div class="recipes-view">
    <div class="page-header">
      <h1>{{ $t('recipes.title') }}</h1>
      <n-button @click="store.fetchRecipes()" :loading="store.loading">
        <template #icon>
          <PhArrowsClockwise />
        </template>
        {{ $t('common.refresh') }}
      </n-button>
    </div>

    <n-spin :show="store.loading && !store.recipes.length">
      <div v-if="store.error" class="error-state">
        <n-alert type="error" :title="store.error" />
      </div>

      <div v-else-if="store.recipes.length === 0" class="empty-state">
        <n-empty :description="$t('recipes.noRecipes')">
          <template #extra>
            <p class="empty-hint">
              {{ $t('recipes.defineHint', { config: '' }) }}<code>.procler/config.yaml</code>
            </p>
          </template>
        </n-empty>
      </div>

      <n-grid v-else :cols="2" :x-gap="20" :y-gap="20" responsive="screen" :item-responsive="true">
        <n-gi v-for="recipe in store.recipes" :key="recipe.name" span="2 m:1">
          <n-card :title="recipe.name" class="recipe-card" hoverable>
            <template #header-extra>
              <n-space size="small">
                <n-button
                  size="small"
                  :loading="store.runningRecipe === recipe.name && executionMode === 'preview'"
                  :disabled="store.runningRecipe !== null"
                  @click="handleDryRun(recipe.name)"
                >
                  <template #icon>
                    <PhEye />
                  </template>
                  {{ $t('common.preview') }}
                </n-button>
                <n-button
                  size="small"
                  type="primary"
                  :loading="store.runningRecipe === recipe.name && executionMode === 'run'"
                  :disabled="store.runningRecipe !== null"
                  @click="handleRun(recipe.name)"
                >
                  <template #icon>
                    <PhPlay weight="fill" />
                  </template>
                  {{ $t('common.run') }}
                </n-button>
              </n-space>
            </template>

            <p v-if="recipe.description" class="recipe-description">{{ recipe.description }}</p>

            <div class="recipe-meta">
              <n-tag size="small" :bordered="false">
                <template #icon>
                  <PhListNumbers />
                </template>
                {{ $t('recipes.stepsCount', { count: recipe.steps_count }) }}
              </n-tag>
              <n-tag
                size="small"
                :type="recipe.on_error === 'stop' ? 'warning' : 'default'"
                :bordered="false"
              >
                <template #icon>
                  <PhWarning v-if="recipe.on_error === 'stop'" />
                  <PhArrowRight v-else />
                </template>
                {{ $t('recipes.onError', { mode: recipe.on_error }) }}
              </n-tag>
              <n-tag
                v-if="store.getLastRunTime(recipe.name)"
                size="small"
                type="info"
                :bordered="false"
                class="last-run-tag"
              >
                <template #icon>
                  <PhClockCounterClockwise />
                </template>
                {{ $t('recipes.ranAgo', { time: formatRelativeTime(store.getLastRunTime(recipe.name)) }) }}
              </n-tag>
            </div>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>

    <!-- Live Execution Modal -->
    <n-modal
      v-model:show="showExecutionModal"
      preset="card"
      :title="executionModalTitle"
      style="max-width: 640px;"
      :mask-closable="!isExecuting"
      :closable="!isExecuting"
    >
      <div class="execution-modal">
        <!-- Header with overall progress -->
        <div class="execution-header">
          <div v-if="isExecuting" class="execution-status executing">
            <n-spin size="small" />
            <span>{{ $t('recipes.execution.running') }}</span>
          </div>
          <div v-else-if="executionComplete" class="execution-status" :class="executionStatusClass">
            <PhCheckCircle v-if="executionSuccess" weight="fill" class="status-icon success" />
            <PhXCircle v-else weight="fill" class="status-icon error" />
            <span>{{ executionStatusText }}</span>
          </div>
          <div v-else-if="executionMode === 'preview'" class="execution-status preview">
            <PhEye weight="fill" class="status-icon info" />
            <span>{{ $t('recipes.execution.previewMode') }}</span>
          </div>

          <!-- Progress bar -->
          <div v-if="executionSteps.length > 0" class="progress-container">
            <n-progress
              type="line"
              :percentage="progressPercentage"
              :status="progressStatus"
              :show-indicator="false"
              :height="4"
            />
            <span class="progress-text">
              {{ $t('recipes.execution.stepsProgress', { completed: completedStepsCount, total: executionSteps.length }) }}
            </span>
          </div>

          <!-- Duration -->
          <div v-if="executionDuration" class="execution-duration">
            <PhTimer weight="regular" />
            <span>{{ executionDuration }}ms</span>
          </div>
        </div>

        <!-- Steps list -->
        <div class="execution-steps">
          <TransitionGroup name="step">
            <div
              v-for="(step, index) in executionSteps"
              :key="step.step"
              :class="['execution-step', stepStatusClass(step)]"
              :style="{ '--step-delay': `${index * 50}ms` }"
            >
              <div class="step-indicator">
                <!-- Pending -->
                <div v-if="step.status === 'pending'" class="indicator pending">
                  <span class="step-num">{{ step.step }}</span>
                </div>
                <!-- Running -->
                <div v-else-if="step.status === 'running'" class="indicator running">
                  <n-spin :size="14" />
                </div>
                <!-- Success -->
                <div v-else-if="step.status === 'success'" class="indicator success">
                  <PhCheck weight="bold" />
                </div>
                <!-- Error -->
                <div v-else-if="step.status === 'error'" class="indicator error">
                  <PhX weight="bold" />
                </div>
                <!-- Warning (ignored error) -->
                <div v-else-if="step.status === 'warning'" class="indicator warning">
                  <PhWarning weight="fill" />
                </div>
                <!-- Skipped -->
                <div v-else-if="step.status === 'skipped'" class="indicator skipped">
                  <PhMinusCircle weight="regular" />
                </div>
              </div>

              <div class="step-content">
                <span class="step-action">{{ step.action }}</span>
                <span v-if="step.error" class="step-error">{{ step.error }}</span>
              </div>

              <!-- Connector line -->
              <div v-if="index < executionSteps.length - 1" class="step-connector" />
            </div>
          </TransitionGroup>
        </div>
      </div>

      <template #footer>
        <n-space justify="end">
          <n-button
            @click="closeExecutionModal"
            :disabled="isExecuting"
          >
            {{ isExecuting ? $t('recipes.execution.running') : $t('common.close') }}
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";
import { useI18n } from "vue-i18n";
import {
  NButton,
  NCard,
  NGrid,
  NGi,
  NAlert,
  NSpin,
  NTag,
  NSpace,
  NEmpty,
  NModal,
  NProgress,
  useMessage,
} from "naive-ui";
import {
  PhPlay,
  PhEye,
  PhArrowsClockwise,
  PhListNumbers,
  PhWarning,
  PhArrowRight,
  PhCheckCircle,
  PhXCircle,
  PhCheck,
  PhX,
  PhMinusCircle,
  PhTimer,
  PhClockCounterClockwise,
} from "@phosphor-icons/vue";
import { useRecipeStore } from "@/stores/recipes";
import { useWebSocket, type RecipeStepEvent } from "@/composables/useWebSocket";

interface ExecutionStep {
  step: number;
  action: string;
  status: 'pending' | 'running' | 'success' | 'error' | 'warning' | 'skipped';
  error?: string;
  ignoreError?: boolean;
}

const { t } = useI18n();
const store = useRecipeStore();
const message = useMessage();
const { connect, subscribeRecipe, unsubscribeRecipe } = useWebSocket();

// Tick counter to force re-render of relative times
const timeTick = ref(0);
let timeTickInterval: ReturnType<typeof setInterval> | null = null;

const showExecutionModal = ref(false);
const executionMode = ref<'preview' | 'run'>('run');
const executionSteps = ref<ExecutionStep[]>([]);
const isExecuting = ref(false);
const executionComplete = ref(false);
const executionSuccess = ref(false);
const executionDuration = ref<number | null>(null);
const currentRecipeName = ref('');

const executionModalTitle = computed(() => {
  if (!currentRecipeName.value) return '';
  const prefix = executionMode.value === 'preview' ? 'Preview: ' : '';
  return prefix + currentRecipeName.value;
});

const completedStepsCount = computed(() => {
  return executionSteps.value.filter(s =>
    s.status === 'success' || s.status === 'error' || s.status === 'warning' || s.status === 'skipped'
  ).length;
});

const progressPercentage = computed(() => {
  if (executionSteps.value.length === 0) return 0;
  return Math.round((completedStepsCount.value / executionSteps.value.length) * 100);
});

const progressStatus = computed(() => {
  if (executionSteps.value.some(s => s.status === 'error')) return 'error';
  if (executionSteps.value.some(s => s.status === 'warning')) return 'warning';
  if (executionComplete.value && executionSuccess.value) return 'success';
  return 'default';
});

const executionStatusClass = computed(() => {
  if (executionSuccess.value) return 'success';
  return 'error';
});

const executionStatusText = computed(() => {
  if (executionSuccess.value) return t('recipes.execution.completed');
  return t('recipes.execution.stoppedDueToError');
});

function stepStatusClass(step: ExecutionStep) {
  return step.status;
}

function resetExecutionState() {
  executionSteps.value = [];
  isExecuting.value = false;
  executionComplete.value = false;
  executionSuccess.value = false;
  executionDuration.value = null;
}

async function handleDryRun(name: string) {
  executionMode.value = 'preview';
  currentRecipeName.value = name;
  resetExecutionState();
  showExecutionModal.value = true;

  // Get preview steps
  const result = await store.dryRunRecipe(name);

  if (result.success && result.data?.planned_steps) {
    executionSteps.value = result.data.planned_steps.map((s: { step: number; action: string }) => ({
      step: s.step,
      action: s.action,
      status: 'pending' as const,
    }));
  }
}

async function handleRun(name: string) {
  executionMode.value = 'run';
  currentRecipeName.value = name;
  resetExecutionState();
  showExecutionModal.value = true;
  isExecuting.value = true;

  // First, get the planned steps via dry-run to show what will happen
  const dryRunResult = await store.dryRunRecipe(name);

  if (dryRunResult.success && dryRunResult.data?.planned_steps) {
    executionSteps.value = dryRunResult.data.planned_steps.map((s: { step: number; action: string }) => ({
      step: s.step,
      action: s.action,
      status: 'pending' as const,
    }));

    // Small delay to show the pending state
    await nextTick();

    // Subscribe to WebSocket events for real-time updates
    connect();
    subscribeRecipe(name, handleRecipeStepEvent);

    // Run the actual recipe (events will update UI in real-time)
    const result = await store.runRecipe(name);

    // Unsubscribe from events
    unsubscribeRecipe(name);

    if (result.success && result.data) {
      executionDuration.value = result.data.duration_ms;
      executionSuccess.value = !result.data.stopped_at_step &&
        result.data.steps_completed === result.data.steps_total;
    } else {
      // Mark all as error if the whole request failed
      executionSteps.value = executionSteps.value.map(s => ({
        ...s,
        status: s.status === 'pending' ? 'error' as const : s.status,
        error: s.status === 'pending' ? (result.error || 'Unknown error') : s.error,
      }));
      message.error(t('recipes.messages.failed', { error: result.error || 'Unknown error' }));
    }
  } else {
    message.error(t('recipes.messages.loadFailed'));
  }

  isExecuting.value = false;
  executionComplete.value = true;
}

function handleRecipeStepEvent(event: RecipeStepEvent) {
  const stepIndex = event.step - 1;
  if (stepIndex >= 0 && stepIndex < executionSteps.value.length) {
    executionSteps.value[stepIndex] = {
      ...executionSteps.value[stepIndex],
      status: event.status,
      error: event.error || undefined,
    };
  }
}

function closeExecutionModal() {
  if (!isExecuting.value) {
    showExecutionModal.value = false;
  }
}

function formatRelativeTime(timestamp: number | null): string | null {
  void timeTick.value; // Dependency for reactivity
  if (!timestamp) return null;
  const seconds = Math.floor((Date.now() - timestamp) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

onMounted(() => {
  store.fetchRecipes();
  connect();
  // Update relative times every 30 seconds
  timeTickInterval = setInterval(() => {
    timeTick.value++;
  }, 30000);
});

onUnmounted(() => {
  if (timeTickInterval) {
    clearInterval(timeTickInterval);
  }
});
</script>

<style scoped>
.recipes-view {
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

.recipe-card {
  transition: transform 0.15s ease;
}

.recipe-description {
  color: var(--n-text-color-2);
  font-size: 0.875rem;
  margin: 0 0 1rem;
}

.recipe-meta {
  display: flex;
  gap: 0.5rem;
}

/* Execution Modal Styles */
.execution-modal {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.execution-header {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--n-border-color);
}

.execution-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.execution-status.executing {
  color: var(--n-primary-color);
}

.execution-status.success {
  color: var(--n-success-color);
}

.execution-status.error {
  color: var(--n-error-color);
}

.execution-status.preview {
  color: var(--n-info-color);
}

.status-icon {
  font-size: 1.25rem;
}

.status-icon.success {
  color: var(--n-success-color);
}

.status-icon.error {
  color: var(--n-error-color);
}

.status-icon.info {
  color: var(--n-info-color);
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.progress-container :deep(.n-progress) {
  flex: 1;
}

.progress-text {
  font-size: 0.8125rem;
  color: var(--n-text-color-3);
  white-space: nowrap;
}

.execution-duration {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
  color: var(--n-text-color-3);
}

/* Steps */
.execution-steps {
  display: flex;
  flex-direction: column;
  gap: 0;
  position: relative;
}

.execution-step {
  display: flex;
  align-items: flex-start;
  gap: 0.875rem;
  padding: 0.625rem 0;
  position: relative;
  animation: stepFadeIn 0.3s ease both;
  animation-delay: var(--step-delay, 0ms);
}

@keyframes stepFadeIn {
  from {
    opacity: 0;
    transform: translateX(-8px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.step-indicator {
  position: relative;
  z-index: 1;
}

.indicator {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  transition: all 0.2s ease;
}

.indicator.pending {
  background: var(--n-code-color);
  border: 2px solid var(--n-border-color);
  color: var(--n-text-color-3);
}

.indicator.running {
  background: rgba(0, 229, 255, 0.15);
  border: 2px solid var(--n-primary-color);
  color: var(--n-primary-color);
}

.indicator.success {
  background: rgba(82, 196, 26, 0.15);
  border: 2px solid var(--n-success-color);
  color: var(--n-success-color);
}

.indicator.error {
  background: rgba(255, 77, 79, 0.15);
  border: 2px solid var(--n-error-color);
  color: var(--n-error-color);
}

.indicator.warning {
  background: rgba(250, 173, 20, 0.15);
  border: 2px solid var(--n-warning-color);
  color: var(--n-warning-color);
}

.indicator.skipped {
  background: var(--n-code-color);
  border: 2px dashed var(--n-border-color);
  color: var(--n-text-color-3);
  opacity: 0.6;
}

.step-num {
  font-size: 0.75rem;
}

.step-content {
  flex: 1;
  min-width: 0;
  padding-top: 0.25rem;
}

.step-action {
  font-family: var(--n-font-family-mono);
  font-size: 0.8125rem;
  word-break: break-word;
  transition: color 0.2s ease;
}

.execution-step.pending .step-action {
  color: var(--n-text-color-3);
}

.execution-step.running .step-action {
  color: var(--n-primary-color);
}

.execution-step.success .step-action {
  color: var(--n-text-color-1);
}

.execution-step.error .step-action {
  color: var(--n-error-color);
}

.execution-step.warning .step-action {
  color: var(--n-warning-color);
}

.execution-step.skipped .step-action {
  color: var(--n-text-color-3);
  opacity: 0.6;
  text-decoration: line-through;
}

.step-error {
  display: block;
  font-size: 0.75rem;
  color: var(--n-error-color);
  margin-top: 0.25rem;
}

/* Connector line between steps */
.step-connector {
  position: absolute;
  left: 13px;
  top: 38px;
  bottom: -10px;
  width: 2px;
  background: var(--n-border-color);
  z-index: 0;
}

.execution-step.success .step-connector {
  background: var(--n-success-color);
}

.execution-step.error .step-connector,
.execution-step.warning .step-connector {
  background: var(--n-border-color);
}

/* Transition group animations */
.step-enter-active,
.step-leave-active {
  transition: all 0.3s ease;
}

.step-enter-from {
  opacity: 0;
  transform: translateX(-10px);
}

.step-leave-to {
  opacity: 0;
  transform: translateX(10px);
}
</style>
