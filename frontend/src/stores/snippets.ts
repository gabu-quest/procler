import { defineStore } from "pinia";
import { ref } from "vue";

export interface Snippet {
  id: number;
  name: string;
  command: string;
  description: string | null;
  tags: string | null;
  created_at: string;
  updated_at: string;
}

export const useSnippetStore = defineStore("snippets", () => {
  const snippets = ref<Snippet[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchSnippets(tag?: string) {
    loading.value = true;
    error.value = null;
    try {
      const url = tag ? `/api/snippets?tag=${encodeURIComponent(tag)}` : "/api/snippets";
      const response = await fetch(url);
      const data = await response.json();
      if (data.success) {
        snippets.value = data.data.snippets;
      } else {
        error.value = data.error;
      }
    } catch (e) {
      error.value = String(e);
    } finally {
      loading.value = false;
    }
  }

  async function createSnippet(snippet: { name: string; command: string; description?: string; tags?: string }) {
    const response = await fetch("/api/snippets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(snippet),
    });
    const data = await response.json();
    if (data.success) {
      await fetchSnippets();
    }
    return data;
  }

  async function removeSnippet(name: string) {
    const response = await fetch(`/api/snippets/${name}`, { method: "DELETE" });
    const data = await response.json();
    if (data.success) {
      await fetchSnippets();
    }
    return data;
  }

  async function runSnippet(name: string) {
    const response = await fetch(`/api/snippets/${name}/run`, { method: "POST" });
    return await response.json();
  }

  return {
    snippets,
    loading,
    error,
    fetchSnippets,
    createSnippet,
    removeSnippet,
    runSnippet,
  };
});
