import { defineStore } from "pinia";
import { ref, computed } from "vue";

export interface Recipe {
  name: string;
  description?: string;
  steps_count: number;
  on_error: "stop" | "continue";
}

export interface RecipeDetail {
  name: string;
  description?: string;
  steps: Record<string, unknown>[];
  on_error: "stop" | "continue";
}

export interface RecipeStepResult {
  step: number;
  action: string;
  success: boolean;
  details?: Record<string, unknown>;
  error?: string;
  ignore_error?: boolean;
}

export interface RecipeRunResult {
  recipe: string;
  duration_ms: number;
  steps_total: number;
  steps_completed: number;
  stopped_at_step?: number | null;
  results: RecipeStepResult[];
  dry_run?: boolean;
  planned_steps?: { step: number; action: string }[];
}

const LAST_RUN_STORAGE_KEY = "procler:recipe-last-run";

function loadLastRunTimestamps(): Record<string, number> {
  try {
    const stored = localStorage.getItem(LAST_RUN_STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
}

function saveLastRunTimestamps(timestamps: Record<string, number>) {
  try {
    localStorage.setItem(LAST_RUN_STORAGE_KEY, JSON.stringify(timestamps));
  } catch {
    // localStorage might be unavailable
  }
}

export const useRecipeStore = defineStore("recipes", () => {
  const recipes = ref<Recipe[]>([]);
  const currentRecipe = ref<RecipeDetail | null>(null);
  const lastRunResult = ref<RecipeRunResult | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const runningRecipe = ref<string | null>(null); // Track which recipe is running
  const lastRunTimestamps = ref<Record<string, number>>(loadLastRunTimestamps());

  const recipeCount = computed(() => recipes.value.length);

  async function fetchRecipes() {
    loading.value = true;
    error.value = null;
    try {
      const response = await fetch("/api/recipes");
      const data = await response.json();
      if (data.success) {
        recipes.value = data.data.recipes;
      } else {
        error.value = data.error;
      }
    } catch (e) {
      error.value = String(e);
    } finally {
      loading.value = false;
    }
  }

  async function fetchRecipe(name: string) {
    loading.value = true;
    error.value = null;
    try {
      const response = await fetch(`/api/recipes/${name}`);
      const data = await response.json();
      if (data.success) {
        currentRecipe.value = data.data.recipe;
      } else {
        error.value = data.error;
      }
    } catch (e) {
      error.value = String(e);
    } finally {
      loading.value = false;
    }
  }

  async function runRecipe(name: string, dryRun: boolean = false, continueOnError?: boolean) {
    runningRecipe.value = name;
    error.value = null;
    try {
      const response = await fetch(`/api/recipes/${name}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dry_run: dryRun,
          continue_on_error: continueOnError,
        }),
      });
      const data = await response.json();
      if (data.success) {
        lastRunResult.value = data.data;
        // Track when recipe was last run (not dry-run)
        if (!dryRun) {
          lastRunTimestamps.value = {
            ...lastRunTimestamps.value,
            [name]: Date.now(),
          };
          saveLastRunTimestamps(lastRunTimestamps.value);
        }
      } else {
        error.value = data.error;
      }
      return data;
    } catch (e) {
      error.value = String(e);
      return { success: false, error: String(e) };
    } finally {
      runningRecipe.value = null;
    }
  }

  async function dryRunRecipe(name: string) {
    return runRecipe(name, true);
  }

  function clearLastResult() {
    lastRunResult.value = null;
  }

  function getLastRunTime(name: string): number | null {
    return lastRunTimestamps.value[name] ?? null;
  }

  return {
    recipes,
    currentRecipe,
    lastRunResult,
    loading,
    error,
    runningRecipe,
    recipeCount,
    lastRunTimestamps,
    fetchRecipes,
    fetchRecipe,
    runRecipe,
    dryRunRecipe,
    clearLastResult,
    getLastRunTime,
  };
});
