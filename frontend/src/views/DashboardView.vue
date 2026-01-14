<template>
  <div class="dashboard-view">
    <div class="page-header">
      <div class="header-title">
        <img src="/procler.png" alt="Procler logo" class="dashboard-logo" />
        <h1>Dashboard</h1>
      </div>
      <n-button @click="refreshAll" :loading="loading">
        <template #icon>
          <PhArrowsClockwise />
        </template>
        Refresh
      </n-button>
    </div>

    <!-- Stats Overview -->
    <div class="stats-row">
      <n-card class="stat-card" :class="{ 'has-running': processStore.runningCount > 0 }">
        <div class="stat-content">
          <div class="stat-icon-wrapper running">
            <PhPlay weight="fill" class="stat-icon" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ processStore.runningCount }}</div>
            <div class="stat-label">Running</div>
          </div>
        </div>
      </n-card>

      <n-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon-wrapper processes">
            <PhListBullets class="stat-icon" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ processStore.processes.length }}</div>
            <div class="stat-label">Processes</div>
          </div>
        </div>
      </n-card>

      <n-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon-wrapper groups">
            <PhStack class="stat-icon" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ groupStore.groups.length }}</div>
            <div class="stat-label">Groups</div>
          </div>
        </div>
      </n-card>

      <n-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon-wrapper recipes">
            <PhListChecks class="stat-icon" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ recipeStore.recipes.length }}</div>
            <div class="stat-label">Recipes</div>
          </div>
        </div>
      </n-card>
    </div>

    <n-grid :cols="2" :x-gap="20" :y-gap="20" responsive="screen" :item-responsive="true">
      <!-- Process Status -->
      <n-gi span="2 m:1">
        <n-card title="Process Status">
          <template #header-extra>
            <router-link to="/processes" class="view-all-link">View all</router-link>
          </template>

          <div v-if="processStore.processes.length === 0" class="empty-placeholder">
            <n-empty description="No processes defined" size="small" />
          </div>

          <div v-else class="process-list">
            <div
              v-for="proc in processStore.processes.slice(0, 8)"
              :key="proc.id"
              class="process-item"
              @click="$router.push(`/process/${proc.name}`)"
            >
              <div :class="['status-dot', proc.status]" />
              <span class="process-name">{{ proc.name }}</span>
              <n-tag :type="statusType(proc.status)" size="small">
                {{ proc.status }}
              </n-tag>
            </div>
            <div v-if="processStore.processes.length > 8" class="more-indicator">
              +{{ processStore.processes.length - 8 }} more
            </div>
          </div>
        </n-card>
      </n-gi>

      <!-- Quick Actions -->
      <n-gi span="2 m:1">
        <n-card title="Quick Actions">
          <div v-if="groupStore.groups.length === 0 && recipeStore.recipes.length === 0" class="empty-placeholder">
            <n-empty description="No groups or recipes defined" size="small">
              <template #extra>
                <p class="empty-hint">
                  Define them in <code>.procler/config.yaml</code>
                </p>
              </template>
            </n-empty>
          </div>

          <div v-else class="quick-actions">
            <!-- Groups -->
            <div v-if="groupStore.groups.length > 0" class="action-section">
              <div class="section-label">Groups</div>
              <div class="action-buttons">
                <n-button
                  v-for="group in groupStore.groups.slice(0, 4)"
                  :key="group.name"
                  size="small"
                  @click="$router.push('/groups')"
                >
                  <template #icon>
                    <PhStack />
                  </template>
                  {{ group.name }}
                </n-button>
              </div>
            </div>

            <!-- Recipes -->
            <div v-if="recipeStore.recipes.length > 0" class="action-section">
              <div class="section-label">Recipes</div>
              <div class="action-buttons">
                <n-button
                  v-for="recipe in recipeStore.recipes.slice(0, 4)"
                  :key="recipe.name"
                  size="small"
                  type="primary"
                  secondary
                  @click="$router.push('/recipes')"
                >
                  <template #icon>
                    <PhPlay weight="fill" />
                  </template>
                  {{ recipe.name }}
                </n-button>
              </div>
            </div>
          </div>
        </n-card>
      </n-gi>

      <!-- Recent Activity -->
      <n-gi span="2">
        <n-card title="Recent Activity">
          <template #header-extra>
            <router-link to="/config" class="view-all-link">View changelog</router-link>
          </template>

          <div v-if="configStore.changelog.length === 0" class="empty-placeholder">
            <n-empty description="No recent activity" size="small" />
          </div>

          <div v-else class="activity-list">
            <div
              v-for="(entry, idx) in configStore.changelog.slice(-10).reverse()"
              :key="idx"
              :class="['activity-item', getActivityClass(entry)]"
            >
              <PhCheckCircle v-if="isAction(entry, 'EXECUTE')" weight="fill" class="activity-icon" />
              <PhPlay v-else-if="isAction(entry, 'START')" weight="fill" class="activity-icon" />
              <PhStop v-else-if="isAction(entry, 'STOP')" weight="fill" class="activity-icon" />
              <PhPlus v-else weight="fill" class="activity-icon" />
              <span class="activity-text">{{ formatActivity(entry) }}</span>
            </div>
          </div>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import {
  NButton,
  NCard,
  NGrid,
  NGi,
  NTag,
  NEmpty,
} from "naive-ui";
import {
  PhArrowsClockwise,
  PhPlay,
  PhStop,
  PhListBullets,
  PhStack,
  PhListChecks,
  PhCheckCircle,
  PhPlus,
} from "@phosphor-icons/vue";
import { useProcessStore } from "@/stores/processes";
import { useGroupStore } from "@/stores/groups";
import { useRecipeStore } from "@/stores/recipes";
import { useConfigStore } from "@/stores/config";
import { formatChangelogActivity, getChangelogAction, type ChangelogEntry } from "@/utils/changelog";

const processStore = useProcessStore();
const groupStore = useGroupStore();
const recipeStore = useRecipeStore();
const configStore = useConfigStore();

const loading = ref(false);

function statusType(status: string) {
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

function getActivityClass(entry: ChangelogEntry): string {
  const action = getChangelogAction(entry);
  if (action === "EXECUTE") return "execute";
  if (action === "START") return "start";
  if (action === "STOP") return "stop";
  return "create";
}

function isAction(entry: ChangelogEntry, action: string): boolean {
  return getChangelogAction(entry) === action;
}

function formatActivity(entry: ChangelogEntry): string {
  return formatChangelogActivity(entry);
}

async function refreshAll() {
  loading.value = true;
  try {
    await Promise.all([
      processStore.fetchProcesses(),
      groupStore.fetchGroups(),
      recipeStore.fetchRecipes(),
      configStore.fetchChangelog(20),
    ]);
  } finally {
    loading.value = false;
  }
}

onMounted(refreshAll);
</script>

<style scoped>
.dashboard-view {
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
  gap: 0.75rem;
}

.dashboard-logo {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  box-shadow: 0 0 0 1px rgba(0, 229, 255, 0.25), 0 10px 24px rgba(0, 0, 0, 0.35);
}

.page-header h1 {
  margin: 0;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

.stat-card {
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-card.has-running {
  border-color: var(--n-success-color);
  box-shadow: 0 0 20px rgba(168, 255, 96, 0.15);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon-wrapper {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--n-code-color);
}

.stat-icon-wrapper.running {
  background: rgba(168, 255, 96, 0.15);
  color: var(--n-success-color);
}

.stat-icon-wrapper.processes {
  background: rgba(0, 229, 255, 0.15);
  color: var(--n-primary-color);
}

.stat-icon-wrapper.groups {
  background: rgba(255, 43, 214, 0.15);
  color: var(--n-info-color);
}

.stat-icon-wrapper.recipes {
  background: rgba(255, 204, 0, 0.15);
  color: var(--n-warning-color);
}

.stat-icon {
  font-size: 1.5rem;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 600;
  line-height: 1;
}

.stat-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--n-text-color-3);
  margin-top: 0.25rem;
}

.view-all-link {
  font-size: 0.8125rem;
  color: var(--n-primary-color);
  text-decoration: none;
}

.view-all-link:hover {
  text-decoration: underline;
}

.empty-placeholder {
  padding: 1.5rem 0;
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

.process-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.process-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  border-radius: var(--n-border-radius);
  cursor: pointer;
  transition: background 0.15s ease;
}

.process-item:hover {
  background: var(--n-hover-color);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.running {
  background: var(--n-success-color);
  box-shadow: 0 0 8px var(--n-success-color);
}

.status-dot.stopped {
  background: var(--n-text-color-3);
}

.status-dot.failed {
  background: var(--n-error-color);
}

.process-name {
  flex: 1;
  font-family: var(--n-font-family-mono);
  font-size: 0.875rem;
}

.more-indicator {
  text-align: center;
  font-size: 0.8125rem;
  color: var(--n-text-color-3);
  padding: 0.5rem;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.action-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.section-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--n-text-color-3);
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.5rem;
  font-size: 0.8125rem;
  font-family: var(--n-font-family-mono);
  border-left: 3px solid transparent;
  border-radius: 0 var(--n-border-radius-small) var(--n-border-radius-small) 0;
}

.activity-item:hover {
  background: var(--n-hover-color);
}

.activity-item.execute {
  border-left-color: var(--n-primary-color);
}

.activity-item.start {
  border-left-color: var(--n-success-color);
}

.activity-item.stop {
  border-left-color: var(--n-warning-color);
}

.activity-item.create {
  border-left-color: var(--n-info-color);
}

.activity-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.activity-item.execute .activity-icon {
  color: var(--n-primary-color);
}

.activity-item.start .activity-icon {
  color: var(--n-success-color);
}

.activity-item.stop .activity-icon {
  color: var(--n-warning-color);
}

.activity-item.create .activity-icon {
  color: var(--n-info-color);
}

.activity-text {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
