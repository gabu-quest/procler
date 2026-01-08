import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "processes",
    component: () => import("@/views/ProcessesView.vue"),
  },
  {
    path: "/process/:name",
    name: "process-detail",
    component: () => import("@/views/ProcessDetailView.vue"),
  },
  {
    path: "/snippets",
    name: "snippets",
    component: () => import("@/views/SnippetsView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
