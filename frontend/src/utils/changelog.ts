export interface ParsedChangelogEntry {
  timestamp: string;
  action: string;
  entity_type: string;
  entity_name: string;
  details?: Record<string, unknown>;
}

export type ChangelogEntry = string | ParsedChangelogEntry;

const ACTION_MATCH = /\]\s+(\w+)/;

function getActionFromRaw(entry: string): string {
  const match = entry.match(ACTION_MATCH);
  return match?.[1] ?? "";
}

export function getChangelogAction(entry: ChangelogEntry): string {
  if (typeof entry === "string") {
    return getActionFromRaw(entry).toUpperCase();
  }
  return (entry.action ?? "").toUpperCase();
}

export function formatChangelogEntry(entry: ChangelogEntry): string {
  if (typeof entry === "string") {
    return entry;
  }
  const details =
    entry.details && Object.keys(entry.details).length > 0 ? JSON.stringify(entry.details) : "{}";
  return `[${entry.timestamp}] ${entry.action} ${entry.entity_type}:${entry.entity_name} ${details}`;
}

export function formatChangelogActivity(entry: ChangelogEntry): string {
  if (typeof entry === "string") {
    const match = entry.match(/\[([^\]]+)\]\s+(\w+)\s+(.+)/);
    if (match) {
      const timestamp = new Date(match[1]);
      const action = match[2].toLowerCase();
      const rest = match[3];
      const timeStr = timestamp.toLocaleTimeString();
      return `${timeStr} - ${action} ${rest.split("{")[0].trim()}`;
    }
    return entry;
  }

  const timestamp = new Date(entry.timestamp);
  const timeStr = Number.isNaN(timestamp.getTime())
    ? entry.timestamp
    : timestamp.toLocaleTimeString();
  const action = entry.action ? entry.action.toLowerCase() : "update";
  const entity = entry.entity_type && entry.entity_name ? `${entry.entity_type}:${entry.entity_name}` : "";

  return entity ? `${timeStr} - ${action} ${entity}` : `${timeStr} - ${action}`;
}
