import { onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";

export interface Shortcut {
  key: string;
  description: string;
  handler: () => void;
}

const showHelp = ref(false);

export function useKeyboardShortcuts() {
  const router = useRouter();

  const shortcuts: Shortcut[] = [
    { key: "g d", description: "Go to Dashboard", handler: () => router.push("/") },
    { key: "g p", description: "Go to Processes", handler: () => router.push("/processes") },
    { key: "g g", description: "Go to Groups", handler: () => router.push("/groups") },
    { key: "g r", description: "Go to Recipes", handler: () => router.push("/recipes") },
    { key: "g s", description: "Go to Snippets", handler: () => router.push("/snippets") },
    { key: "g c", description: "Go to Config", handler: () => router.push("/config") },
    { key: "?", description: "Show keyboard shortcuts", handler: () => { showHelp.value = true; } },
    { key: "Escape", description: "Close dialogs", handler: () => { showHelp.value = false; } },
  ];

  let keySequence = "";
  let sequenceTimeout: ReturnType<typeof setTimeout> | null = null;

  function handleKeyDown(event: KeyboardEvent) {
    // Ignore if typing in an input
    const target = event.target as HTMLElement;
    if (
      target.tagName === "INPUT" ||
      target.tagName === "TEXTAREA" ||
      target.isContentEditable
    ) {
      // Allow Escape to close help even in inputs
      if (event.key === "Escape" && showHelp.value) {
        showHelp.value = false;
        event.preventDefault();
      }
      return;
    }

    // Handle special keys
    if (event.key === "Escape") {
      showHelp.value = false;
      keySequence = "";
      return;
    }

    if (event.key === "?") {
      showHelp.value = true;
      event.preventDefault();
      return;
    }

    // Build key sequence
    if (sequenceTimeout) {
      clearTimeout(sequenceTimeout);
    }

    if (keySequence) {
      keySequence += " " + event.key;
    } else {
      keySequence = event.key;
    }

    // Check for matching shortcut
    const matchedShortcut = shortcuts.find((s) => s.key === keySequence);
    if (matchedShortcut) {
      event.preventDefault();
      matchedShortcut.handler();
      keySequence = "";
      return;
    }

    // Check if sequence could potentially match (partial match)
    const partialMatch = shortcuts.some((s) => s.key.startsWith(keySequence));
    if (!partialMatch) {
      keySequence = "";
    } else {
      // Reset after 1 second of inactivity
      sequenceTimeout = setTimeout(() => {
        keySequence = "";
      }, 1000);
    }
  }

  onMounted(() => {
    window.addEventListener("keydown", handleKeyDown);
  });

  onUnmounted(() => {
    window.removeEventListener("keydown", handleKeyDown);
    if (sequenceTimeout) {
      clearTimeout(sequenceTimeout);
    }
  });

  return {
    shortcuts,
    showHelp,
    closeHelp: () => { showHelp.value = false; },
  };
}
