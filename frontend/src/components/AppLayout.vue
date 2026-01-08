<template>
  <n-layout class="app-layout">
    <n-layout-header bordered class="app-header">
      <div class="header-content">
        <router-link to="/" class="logo">
          <PhTerminal :size="24" weight="duotone" />
          <span class="logo-text">Procler</span>
        </router-link>
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
import {
  PhTerminal,
  PhHouse,
  PhListBullets,
  PhStack,
  PhListChecks,
  PhCodeBlock,
  PhGear,
} from "@phosphor-icons/vue";

const route = useRoute();
const router = useRouter();

const activeKey = computed(() => {
  if (route.path === "/") return "dashboard";
  if (route.path.startsWith("/process")) return "processes";
  if (route.path.startsWith("/groups")) return "groups";
  if (route.path.startsWith("/recipes")) return "recipes";
  if (route.path.startsWith("/snippets")) return "snippets";
  if (route.path.startsWith("/config")) return "config";
  return "dashboard";
});

const menuOptions: MenuOption[] = [
  {
    label: "Dashboard",
    key: "dashboard",
    icon: () => h(PhHouse, { weight: "regular" }),
  },
  {
    label: "Processes",
    key: "processes",
    icon: () => h(PhListBullets, { weight: "regular" }),
  },
  {
    label: "Groups",
    key: "groups",
    icon: () => h(PhStack, { weight: "regular" }),
  },
  {
    label: "Recipes",
    key: "recipes",
    icon: () => h(PhListChecks, { weight: "regular" }),
  },
  {
    label: "Snippets",
    key: "snippets",
    icon: () => h(PhCodeBlock, { weight: "regular" }),
  },
  {
    label: "Config",
    key: "config",
    icon: () => h(PhGear, { weight: "regular" }),
  },
];

function handleMenuClick(key: string) {
  const routes: Record<string, string> = {
    dashboard: "/",
    processes: "/processes",
    groups: "/groups",
    recipes: "/recipes",
    snippets: "/snippets",
    config: "/config",
  };
  router.push(routes[key] || "/");
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
  text-decoration: none;
  transition: opacity 0.15s ease;
}

.logo:hover {
  opacity: 0.85;
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
