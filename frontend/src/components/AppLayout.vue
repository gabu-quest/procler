<template>
  <n-layout class="app-layout">
    <n-layout-header bordered class="app-header">
      <div class="header-content">
        <div class="logo">
          <PhTerminal :size="24" weight="duotone" />
          <span class="logo-text">Procgler</span>
        </div>
        <n-menu mode="horizontal" :options="menuOptions" :value="activeKey" @update:value="handleMenuClick" />
      </div>
    </n-layout-header>
    <n-layout-content class="app-content">
      <slot />
    </n-layout-content>
  </n-layout>
</template>

<script setup lang="ts">
import { computed, h } from "vue";
import { useRoute, useRouter } from "vue-router";
import { NLayout, NLayoutHeader, NLayoutContent, NMenu, type MenuOption } from "naive-ui";
import { PhTerminal, PhListBullets, PhCodeBlock } from "@phosphor-icons/vue";

const route = useRoute();
const router = useRouter();

const activeKey = computed(() => {
  if (route.path.startsWith("/snippets")) return "snippets";
  return "processes";
});

const menuOptions: MenuOption[] = [
  {
    label: "Processes",
    key: "processes",
    icon: () => h(PhListBullets, { weight: "regular" }),
  },
  {
    label: "Snippets",
    key: "snippets",
    icon: () => h(PhCodeBlock, { weight: "regular" }),
  },
];

function handleMenuClick(key: string) {
  if (key === "processes") {
    router.push("/");
  } else if (key === "snippets") {
    router.push("/snippets");
  }
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
}

.app-header {
  padding: 0 1.5rem;
  background: var(--n-card-color);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 2rem;
  height: 56px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--n-primary-color);
}

.logo-text {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.app-content {
  padding: 1.5rem;
}
</style>
