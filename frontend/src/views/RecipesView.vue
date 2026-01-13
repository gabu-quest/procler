<template>
  <div class="recipes-view">
    <div class="page-header">
      <h1>Recipes</h1>
      <n-button @click="store.fetchRecipes()" :loading="store.loading">
        <template #icon>
          <PhArrowsClockwise />
        </template>
        Refresh
      </n-button>
    </div>

    <n-spin :show="store.loading && !store.recipes.length">
      <div v-if="store.error" class="error-state">
        <n-alert type="error" :title="store.error" />
      </div>

      <div v-else-if="store.recipes.length === 0" class="empty-state">
        <n-empty description="No recipes defined">
          <template #extra>
            <p class="empty-hint">
              Define recipes in your <code>.procler/config.yaml</code> file
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
                  :loading="store.runningRecipe === recipe.name && isDryRun"
                  :disabled="store.runningRecipe !== null"
                  @click="handleDryRun(recipe.name)"
                >
                  <template #icon>
                    <PhEye />
                  </template>
                  Preview
                </n-button>
                <n-button
                  size="small"
                  type="primary"
                  :loading="store.runningRecipe === recipe.name && !isDryRun"
                  :disabled="store.runningRecipe !== null"
                  @click="handleRun(recipe.name)"
                >
                  <template #icon>
                    <PhPlay weight="fill" />
                  </template>
                  Run
                </n-button>
              </n-space>
            </template>

            <p v-if="recipe.description" class="recipe-description">{{ recipe.description }}</p>

            <div class="recipe-meta">
              <n-tag size="small" :bordered="false">
                <template #icon>
                  <PhListNumbers />
                </template>
                {{ recipe.steps_count }} steps
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
                on_error: {{ recipe.on_error }}
              </n-tag>
            </div>

            <!-- Steps -->
            <div v-if="recipeDetails[recipe.name]" class="steps-panel">
              <n-button
                text
                type="primary"
                size="small"
                @click="toggleSteps(recipe.name)"
                class="load-steps-btn"
              >
                <template #icon>
                  <PhCaretDown :class="['caret-icon', { open: expandedSteps[recipe.name] }]" />
                </template>
                {{ expandedSteps[recipe.name] ? "Hide steps" : "Show steps" }}
              </n-button>

              <div v-show="expandedSteps[recipe.name]" class="step-list">
                <div
                  v-for="(step, idx) in recipeDetails[recipe.name].steps"
                  :key="idx"
                  class="step-item"
                >
                  <span class="step-number">{{ idx + 1 }}</span>
                  <span class="step-action">{{ formatStep(step) }}</span>
                </div>
              </div>
            </div>

            <n-button
              v-else
              text
              type="primary"
              size="small"
              @click="loadRecipeDetails(recipe.name)"
              class="load-steps-btn"
            >
              <template #icon>
                <PhCaretDown />
              </template>
              Show steps
            </n-button>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>

    <!-- Execution Result Modal -->
    <n-modal v-model:show="showResultModal" preset="card" :title="resultModalTitle" style="max-width: 600px;">
      <template v-if="store.lastRunResult">
        <!-- Dry Run Preview -->
        <template v-if="store.lastRunResult.dry_run">
          <n-alert type="info" title="Preview Mode" style="margin-bottom: 1rem;">
            This shows what would happen. No actions were taken.
          </n-alert>
          <div class="result-steps">
            <div
              v-for="step in store.lastRunResult.planned_steps"
              :key="step.step"
              class="result-step preview"
            >
              <span class="step-number">{{ step.step }}</span>
              <span class="step-action">{{ step.action }}</span>
            </div>
          </div>
        </template>

        <!-- Actual Run Result -->
        <template v-else>
          <div class="result-summary">
            <n-alert
              :type="store.lastRunResult.stopped_at_step ? 'error' : (store.lastRunResult.steps_completed === store.lastRunResult.steps_total ? 'success' : 'warning')"
              :title="getResultTitle()"
              style="margin-bottom: 1rem;"
            >
              <p>Duration: {{ store.lastRunResult.duration_ms }}ms</p>
              <p>Steps: {{ store.lastRunResult.steps_completed }} / {{ store.lastRunResult.steps_total }}</p>
              <p v-if="store.lastRunResult.stopped_at_step">
                Stopped at step {{ store.lastRunResult.stopped_at_step }}
              </p>
            </n-alert>
          </div>

          <div class="result-steps">
            <div
              v-for="result in store.lastRunResult.results"
              :key="result.step"
              :class="['result-step', { success: result.success, error: !result.success && !result.ignore_error, ignored: !result.success && result.ignore_error }]"
            >
              <PhCheckCircle v-if="result.success" weight="fill" class="step-icon success" />
              <PhWarning v-else-if="result.ignore_error" weight="fill" class="step-icon warning" />
              <PhXCircle v-else weight="fill" class="step-icon error" />
              <span class="step-number">{{ result.step }}</span>
              <span class="step-action">{{ result.action }}</span>
              <span v-if="result.error" class="step-error">{{ result.error }}</span>
            </div>
          </div>
        </template>
      </template>
      <template #footer>
        <n-button @click="showResultModal = false">Close</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
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
  useMessage,
} from "naive-ui";
import {
  PhPlay,
  PhEye,
  PhArrowsClockwise,
  PhListNumbers,
  PhWarning,
  PhArrowRight,
  PhCaretDown,
  PhCheckCircle,
  PhXCircle,
} from "@phosphor-icons/vue";
import { useRecipeStore, type RecipeDetail } from "@/stores/recipes";

const store = useRecipeStore();
const message = useMessage();

const isDryRun = ref(false);
const showResultModal = ref(false);
const recipeDetails = reactive<Record<string, RecipeDetail>>({});
const expandedSteps = reactive<Record<string, boolean>>({});

const resultModalTitle = computed(() => {
  if (!store.lastRunResult) return "";
  const prefix = store.lastRunResult.dry_run ? "Preview: " : "Result: ";
  return prefix + store.lastRunResult.recipe;
});

function formatStep(step: Record<string, unknown>): string {
  // Format step for display
  const keys = Object.keys(step);
  if (keys.includes("start")) return `start ${step.start}`;
  if (keys.includes("stop")) return `stop ${step.stop}${step.ignore_error ? " (ignore errors)" : ""}`;
  if (keys.includes("restart")) return `restart ${step.restart}`;
  if (keys.includes("group_start")) return `start group ${step.group_start}`;
  if (keys.includes("group_stop")) return `stop group ${step.group_stop}`;
  if (keys.includes("wait")) return `wait ${step.wait}`;
  if (keys.includes("exec")) {
    let s = `exec "${step.exec}"`;
    if (step.container) s += ` (docker:${step.container})`;
    if (step.ignore_error) s += " (ignore errors)";
    return s;
  }
  return JSON.stringify(step);
}

async function loadRecipeDetails(name: string) {
  try {
    const response = await fetch(`/api/recipes/${name}`);
    const data = await response.json();
    if (data.success) {
      recipeDetails[name] = data.data.recipe;
      expandedSteps[name] = true;
    }
  } catch (e) {
    console.error("Failed to load recipe details:", e);
  }
}

function toggleSteps(name: string) {
  expandedSteps[name] = !expandedSteps[name];
}

async function handleDryRun(name: string) {
  isDryRun.value = true;
  message.info(`Previewing recipe: ${name}`);
  await store.dryRunRecipe(name);
  showResultModal.value = true;
}

async function handleRun(name: string) {
  isDryRun.value = false;
  message.info(`Running recipe: ${name}`);
  const result = await store.runRecipe(name);
  if (result.success) {
    message.success(`Recipe completed: ${name}`);
  } else {
    message.error(`Recipe failed: ${result.error || "Unknown error"}`);
  }
  showResultModal.value = true;
}

function getResultTitle(): string {
  if (!store.lastRunResult) return "";
  if (store.lastRunResult.stopped_at_step) return "Recipe stopped due to error";
  if (store.lastRunResult.steps_completed === store.lastRunResult.steps_total) {
    return "Recipe completed successfully";
  }
  return "Recipe completed with issues";
}

onMounted(() => {
  store.fetchRecipes();
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
  margin-bottom: 1rem;
}

.steps-panel {
  margin-top: 0.5rem;
}

.caret-icon {
  transition: transform 0.2s ease;
}

.caret-icon.open {
  transform: rotate(180deg);
}

.step-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.step-item,
.result-step {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.375rem 0.5rem;
  background: var(--n-code-color);
  border-radius: var(--n-border-radius-small);
}

.step-number {
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
  flex-shrink: 0;
}

.step-action {
  font-family: var(--n-font-family-mono);
  font-size: 0.8125rem;
  flex: 1;
}

.load-steps-btn {
  margin-top: 0.5rem;
  color: var(--n-primary-color);
}

/* Result modal styles */
.result-summary {
  margin-bottom: 1rem;
}

.result-summary p {
  margin: 0.25rem 0;
  font-size: 0.875rem;
}

.result-steps {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.result-step {
  border-left: 3px solid var(--n-border-color);
}

.result-step.success {
  border-left-color: var(--n-success-color);
}

.result-step.error {
  border-left-color: var(--n-error-color);
  background: rgba(255, 59, 59, 0.08);
}

.result-step.ignored {
  border-left-color: var(--n-warning-color);
  background: rgba(255, 204, 0, 0.08);
}

.result-step.preview {
  border-left-color: var(--n-info-color);
}

.step-icon {
  font-size: 1.125rem;
  flex-shrink: 0;
}

.step-icon.success {
  color: var(--n-success-color);
}

.step-icon.error {
  color: var(--n-error-color);
}

.step-icon.warning {
  color: var(--n-warning-color);
}

.step-error {
  color: var(--n-error-color);
  font-size: 0.75rem;
  margin-left: auto;
}
</style>
