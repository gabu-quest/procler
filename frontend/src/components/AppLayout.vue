<template>
  <n-layout class="app-layout">
    <n-layout-header bordered class="app-header">
      <div class="header-content">
        <router-link to="/" class="logo">
          <PhTerminal :size="24" weight="duotone" />
          <span class="logo-text">Procler</span>
        </router-link>
        <n-menu mode="horizontal" :options="menuOptions" :value="activeKey" @update:value="handleMenuClick" />
        <div class="header-spacer" />
        <n-tooltip trigger="hover">
          <template #trigger>
            <div
              class="connection-indicator"
              :class="connectionStatus"
              role="status"
              :aria-label="`WebSocket ${connectionStatus}${lastError ? ': ' + lastError : ''}`"
            >
              <PhPlugsConnected v-if="connectionStatus === 'connected'" :size="18" weight="fill" />
              <PhCircleNotch v-else-if="connectionStatus === 'connecting'" :size="18" weight="bold" class="spin" />
              <PhPlugs v-else :size="18" weight="regular" />
            </div>
          </template>
          <span v-if="connectionStatus === 'connected'">Connected</span>
          <span v-else-if="connectionStatus === 'connecting'">Connecting{{ reconnectAttempts > 0 ? ` (attempt ${reconnectAttempts})` : '' }}...</span>
          <span v-else-if="connectionStatus === 'error'">{{ lastError || 'Connection error' }}</span>
          <span v-else>Disconnected</span>
        </n-tooltip>
      </div>
    </n-layout-header>
    <n-layout-content class="app-content">
      <slot />
    </n-layout-content>
    <KeyboardShortcutsHelp />
  </n-layout>
</template>

<script setup lang="ts">
import { computed, h, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { NLayout, NLayoutHeader, NLayoutContent, NMenu, NTooltip, type MenuOption } from "naive-ui";
import {
  PhTerminal,
  PhHouse,
  PhListBullets,
  PhStack,
  PhListChecks,
  PhCodeBlock,
  PhGear,
  PhInfo,
  PhPlugsConnected,
  PhPlugs,
  PhCircleNotch,
} from "@phosphor-icons/vue";
import { useWebSocket } from "@/composables/useWebSocket";
import { useProcessNotifications } from "@/composables/useProcessNotifications";
import KeyboardShortcutsHelp from "@/components/KeyboardShortcutsHelp.vue";

const route = useRoute();
const router = useRouter();
const { connectionStatus, lastError, reconnectAttempts, connect, subscribeStatus } = useWebSocket();

// Initialize process notifications (watches for status changes)
useProcessNotifications();

onMounted(() => {
  connect();
  // Subscribe to status updates for all processes
  subscribeStatus();
});

const activeKey = computed(() => {
  if (route.path === "/") return "dashboard";
  if (route.path.startsWith("/process")) return "processes";
  if (route.path.startsWith("/groups")) return "groups";
  if (route.path.startsWith("/recipes")) return "recipes";
  if (route.path.startsWith("/snippets")) return "snippets";
  if (route.path.startsWith("/config")) return "config";
  if (route.path.startsWith("/about")) return "about";
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
  {
    label: "About",
    key: "about",
    icon: () => h(PhInfo, { weight: "regular" }),
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
    about: "/about",
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

.header-spacer {
  flex: 1;
}

.connection-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: default;
  transition: all 0.2s ease;
}

.connection-indicator.connected {
  color: var(--n-success-color);
}

.connection-indicator.connecting {
  color: var(--n-warning-color);
}

.connection-indicator.disconnected,
.connection-indicator.error {
  color: var(--n-text-color-3);
}

.connection-indicator.error {
  color: var(--n-error-color);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
