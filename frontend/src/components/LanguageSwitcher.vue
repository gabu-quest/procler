<template>
  <n-dropdown :options="options" @select="handleSelect">
    <n-button quaternary size="small" class="language-button">
      <template #icon>
        <PhGlobe :size="18" weight="regular" />
      </template>
      {{ currentLanguageLabel }}
    </n-button>
  </n-dropdown>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { NDropdown, NButton } from "naive-ui";
import { PhGlobe } from "@phosphor-icons/vue";
import { useI18n } from "vue-i18n";
import { setLocale } from "@/i18n";

const { locale } = useI18n();

const options = [
  { label: "English", key: "en" },
  { label: "日本語", key: "ja" },
];

const currentLanguageLabel = computed(() => {
  return locale.value === "ja" ? "日本語" : "English";
});

function handleSelect(key: string) {
  setLocale(key);
}
</script>

<style scoped>
.language-button {
  color: var(--n-text-color-2);
}

.language-button:hover {
  color: var(--n-primary-color);
}
</style>
