import { VERDICT_CONFIG } from './constants';

/* Score → 0-100 display string */
export function formatScore(score) {
  if (score == null) return '—';
  return `${Math.round(score)}%`;
}

/* Verdict key → human label */
export function formatVerdict(verdictKey) {
  return VERDICT_CONFIG[verdictKey]?.label ?? verdictKey;
}

/* Bytes → human-readable */
export function formatFileSize(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let size = bytes;
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024;
    i++;
  }
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

/* Seconds → "1m 23s" */
export function formatDuration(seconds) {
  if (!seconds) return '0s';
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

/* ISO string → localized date‑time */
export function formatDateTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/* Score → tailwindish color name */
export function getScoreColor(score) {
  if (score == null) return 'text-gray-400';
  if (score >= 70) return 'text-ds-red';
  if (score >= 40) return 'text-ds-yellow';
  return 'text-ds-green';
}

/* Score → hex color */
export function getScoreHex(score) {
  if (score == null) return '#888888';
  if (score >= 70) return '#ff3c00';
  if (score >= 40) return '#ffd700';
  return '#39ff14';
}

/* Truncate filename for display */
export function truncateFilename(name, maxLen = 24) {
  if (!name || name.length <= maxLen) return name || '';
  const ext = name.slice(name.lastIndexOf('.'));
  const base = name.slice(0, maxLen - ext.length - 3);
  return `${base}...${ext}`;
}

/* Clamp value between min and max */
export function clamp(value, min = 0, max = 100) {
  return Math.min(max, Math.max(min, value));
}
