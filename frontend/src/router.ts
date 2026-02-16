import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "dashboard",
    component: () => import("@/views/DashboardView.vue"),
  },
  {
    path: "/processes",
    name: "processes",
    component: () => import("@/views/ProcessesView.vue"),
  },
  {
    path: "/process/:name",
    name: "process-detail",
    component: () => import("@/views/ProcessDetailView.vue"),
  },
  {
    path: "/groups",
    name: "groups",
    component: () => import("@/views/GroupsView.vue"),
  },
  {
    path: "/recipes",
    name: "recipes",
    component: () => import("@/views/RecipesView.vue"),
  },
  {
    path: "/snippets",
    name: "snippets",
    component: () => import("@/views/SnippetsView.vue"),
  },
  {
    path: "/config",
    name: "config",
    component: () => import("@/views/ConfigView.vue"),
  },
  {
    path: "/about",
    name: "about",
    component: () => import("@/views/AboutView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
