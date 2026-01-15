<template>
  <nav class="breadcrumbs" aria-label="Breadcrumb navigation">
    <ol class="breadcrumb-list">
      <li v-for="(crumb, index) in crumbs" :key="crumb.path" class="breadcrumb-item">
        <router-link
          v-if="index < crumbs.length - 1"
          :to="crumb.path"
          class="breadcrumb-link"
        >
          {{ crumb.label }}
        </router-link>
        <span v-else class="breadcrumb-current" aria-current="page">
          {{ crumb.label }}
        </span>
        <PhCaretRight
          v-if="index < crumbs.length - 1"
          :size="14"
          weight="bold"
          class="breadcrumb-separator"
          aria-hidden="true"
        />
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { PhCaretRight } from "@phosphor-icons/vue";

interface Breadcrumb {
  label: string;
  path: string;
}

const route = useRoute();

const routeLabels: Record<string, string> = {
  "/": "Dashboard",
  "/processes": "Processes",
  "/groups": "Groups",
  "/recipes": "Recipes",
  "/snippets": "Snippets",
  "/config": "Config",
  "/about": "About",
};

const crumbs = computed<Breadcrumb[]>(() => {
  const result: Breadcrumb[] = [{ label: "Dashboard", path: "/" }];

  if (route.path === "/") {
    return result;
  }

  // Handle process detail route
  if (route.path.startsWith("/process/")) {
    result.push({ label: "Processes", path: "/processes" });
    const processName = route.params.name as string;
    result.push({ label: processName, path: route.path });
    return result;
  }

  // Handle other routes
  const label = routeLabels[route.path];
  if (label) {
    result.push({ label, path: route.path });
  }

  return result;
});
</script>

<style scoped>
.breadcrumbs {
  margin-bottom: 1rem;
}

.breadcrumb-list {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 0.875rem;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.breadcrumb-link {
  color: var(--n-text-color-3);
  text-decoration: none;
  transition: color 0.15s ease;
}

.breadcrumb-link:hover {
  color: var(--n-primary-color);
}

.breadcrumb-current {
  color: var(--n-text-color);
  font-weight: 500;
}

.breadcrumb-separator {
  color: var(--n-text-color-3);
  flex-shrink: 0;
}
</style>
