<template>
  <n-modal v-model:show="showHelp" preset="card" :title="$t('shortcuts.title')" style="max-width: 400px">
    <div class="shortcuts-list">
      <div class="shortcuts-section">
        <h4>{{ $t('shortcuts.navigation') }}</h4>
        <div v-for="shortcut in navigationShortcuts" :key="shortcut.key" class="shortcut-row">
          <kbd class="shortcut-key">{{ shortcut.key }}</kbd>
          <span class="shortcut-desc">{{ shortcut.description }}</span>
        </div>
      </div>
      <div class="shortcuts-section">
        <h4>{{ $t('shortcuts.general') }}</h4>
        <div v-for="shortcut in generalShortcuts" :key="shortcut.key" class="shortcut-row">
          <kbd class="shortcut-key">{{ shortcut.key }}</kbd>
          <span class="shortcut-desc">{{ shortcut.description }}</span>
        </div>
      </div>
    </div>
    <template #footer>
      <n-button @click="closeHelp">{{ $t('common.close') }}</n-button>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { NModal, NButton } from "naive-ui";
import { useKeyboardShortcuts } from "@/composables/useKeyboardShortcuts";

const { t } = useI18n();
const { showHelp, closeHelp } = useKeyboardShortcuts();

const shortcuts = computed(() => [
  { key: "g d", description: t('shortcuts.goToDashboard') },
  { key: "g p", description: t('shortcuts.goToProcesses') },
  { key: "g g", description: t('shortcuts.goToGroups') },
  { key: "g r", description: t('shortcuts.goToRecipes') },
  { key: "g s", description: t('shortcuts.goToSnippets') },
  { key: "g c", description: t('shortcuts.goToConfig') },
  { key: "g a", description: t('shortcuts.goToAbout') },
  { key: "?", description: t('shortcuts.showShortcuts') },
  { key: "Escape", description: t('shortcuts.closeDialogs') },
]);

const navigationShortcuts = computed(() =>
  shortcuts.value.filter((s) => s.key.startsWith("g "))
);

const generalShortcuts = computed(() =>
  shortcuts.value.filter((s) => !s.key.startsWith("g "))
);
</script>

<style scoped>
.shortcuts-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.shortcuts-section h4 {
  margin: 0 0 0.75rem;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--n-text-color-3);
}

.shortcut-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.375rem 0;
}

.shortcut-key {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 60px;
  padding: 0.25rem 0.5rem;
  font-family: var(--n-font-family-mono);
  font-size: 0.85rem;
  background: var(--n-code-color);
  border: 1px solid var(--n-border-color);
  border-radius: 4px;
  color: var(--n-text-color);
}

.shortcut-desc {
  color: var(--n-text-color-2);
  font-size: 0.9rem;
}
</style>
