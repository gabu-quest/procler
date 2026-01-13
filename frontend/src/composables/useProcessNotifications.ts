import { watch } from "vue";
import { useNotification, type NotificationType } from "naive-ui";
import { useProcessStore, type Process } from "@/stores/processes";

export function useProcessNotifications() {
  const notification = useNotification();
  const store = useProcessStore();

  // Track previous states to detect changes
  const previousStates = new Map<number, Process["status"]>();

  function showStatusNotification(
    processName: string,
    status: Process["status"],
    type: NotificationType = "info"
  ) {
    const titles: Record<Process["status"], string> = {
      running: "Process Started",
      stopped: "Process Stopped",
      failed: "Process Failed",
    };

    const descriptions: Record<Process["status"], string> = {
      running: `${processName} is now running`,
      stopped: `${processName} has stopped`,
      failed: `${processName} has failed`,
    };

    notification[type]({
      title: titles[status],
      content: descriptions[status],
      duration: 3000,
      keepAliveOnHover: true,
    });
  }

  // Watch for process status changes
  watch(
    () => store.processes,
    (processes) => {
      for (const process of processes) {
        const previousStatus = previousStates.get(process.id);

        // Only notify on status change, not initial load
        if (previousStatus !== undefined && previousStatus !== process.status) {
          const notificationType: NotificationType =
            process.status === "running"
              ? "success"
              : process.status === "failed"
                ? "error"
                : "info";

          showStatusNotification(process.name, process.status, notificationType);
        }

        previousStates.set(process.id, process.status);
      }
    },
    { deep: true }
  );

  return {
    showStatusNotification,
  };
}
