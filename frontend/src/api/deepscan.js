import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL + '/api/v1',
  timeout: 60000, // default 60s for normal calls
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ds_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) localStorage.removeItem('ds_token');
    return Promise.reject(err);
  }
);

export const WS_URL = BASE_URL.replace('http', 'ws');

/**
 * Normalize a backend result into the shape the frontend components expect.
 */
function normalizeResult(data) {
  if (!data) return data;
  // Map backend `fusion` key → `cdcf` for CdcfPanel component
  if (data.fusion && !data.cdcf) {
    const contradictions = data.fusion.contradictions || [];
    data.cdcf = {
      multiplier: data.fusion.multiplier,
      contradictions,
      confidence_note: data.fusion.confidence_note,
      consensus: Math.max(0, 100 - contradictions.length * 10),
      dissent: Math.min(100, contradictions.length * 10),
      confidence: Math.round(100 - Math.abs(1 - (data.fusion.multiplier || 1)) * 100),
      fusion_method: 'CDCF + XGBoost',
    };
  }
  // Normalize heartbeat signal data to use `value` key
  if (data.heartbeat?.signal) {
    data.heartbeat.signal = data.heartbeat.signal.map((p) => ({
      time: p.time ?? p.t ?? 0,
      value: p.value ?? p.amplitude ?? p.v ?? 0,
    }));
  }
  return data;
}

// ─── Cache fresh scan results in localStorage so /result/:id can find them ───
function cacheResult(id, data) {
  try {
    const store = JSON.parse(localStorage.getItem('ds_results') || '{}');
    store[id] = data;
    // Trim to last 50 results to avoid overflowing storage
    const keys = Object.keys(store);
    if (keys.length > 50) delete store[keys[0]];
    localStorage.setItem('ds_results', JSON.stringify(store));
  } catch (e) { /* storage full — ignore */ }
}

function getCachedResult(id) {
  try {
    const store = JSON.parse(localStorage.getItem('ds_results') || '{}');
    return store[id] ?? null;
  } catch { return null; }
}

// ─── Cache scan history locally ───
function cacheHistoryItem(item) {
  try {
    const hist = JSON.parse(localStorage.getItem('ds_history') || '[]');
    // Don't duplicate
    if (!hist.find(h => h.id === item.id)) {
      hist.unshift(item);
      if (hist.length > 100) hist.pop();
      localStorage.setItem('ds_history', JSON.stringify(hist));
    }
  } catch { /* ignore */ }
}

function getLocalHistory() {
  try {
    return JSON.parse(localStorage.getItem('ds_history') || '[]');
  } catch { return []; }
}

export async function analyzeFile(file, onUploadProgress) {
  const formData = new FormData();
  formData.append('file', file);
  // Large videos need a much longer timeout — 30 minutes
  const res = await api.post('/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30 * 60 * 1000,  // 30 minutes
    onUploadProgress,
  });
  const result = normalizeResult(res.data);
  cacheResult(result.id, result);
  cacheHistoryItem({
    id: result.id,
    score: result.score ?? result.aacs_score ?? 0,
    aacs_score: result.aacs_score ?? result.score ?? 0,
    verdict: result.verdict,
    filename: result.original_filename || file.name,
    file_type: file.type.split('/')[0] || 'unknown',
    created_at: result.created_at,
  });
  return result;
}

export async function analyzeUrl(url) {
  const res = await api.post('/analyze/url', { url });
  const result = normalizeResult(res.data);
  cacheResult(result.id, result);
  cacheHistoryItem({
    id: result.id,
    score: result.score ?? result.aacs_score ?? 0,
    aacs_score: result.aacs_score ?? result.score ?? 0,
    verdict: result.verdict,
    filename: url,
    file_type: 'url',
    created_at: result.created_at,
  });
  return result;
}

export async function getResult(id) {
  // 1. Try the real API first
  try {
    const res = await api.get(`/analyze/${id}`);
    return normalizeResult(res.data);
  } catch (err) {
    // 2. Fall back to our local cache (survives server restarts)
    const cached = getCachedResult(id);
    if (cached) return cached;
    throw err;
  }
}

export async function downloadReport(id) {
  const res = await api.get(`/report/${id}`, { responseType: 'blob' });
  return res.data;
}

export async function getHistory() {
  try {
    const res = await api.get('/history');
    const data = res.data;
    return Array.isArray(data) ? data : (data.items || []);
  } catch {
    // Fall back to locally cached history (works without a DB)
    return getLocalHistory();
  }
}

export async function getCommunityAlerts() {
  try {
    const res = await api.get('/community');
    const data = res.data;
    return Array.isArray(data) ? data : (data.items || []);
  } catch {
    return [];
  }
}

export async function submitCommunityReport(url, note) {
  const res = await api.post('/community', {
    title: 'User Report: ' + (url || 'Unknown'),
    content: note || '',
    tags: ['user-report'],
    submitted_by: 'anonymous',
  });
  return res.data;
}

export async function submitFeedback(args) {
  const id = args.alertId || args.id;
  const isCorrect = args.vote ? args.vote === 'up' : args.isCorrect;
  const comment = args.comment || '';
  try {
    return (await api.post('/feedback', { analysis_id: id, is_correct: isCorrect, comment })).data;
  } catch {
    return { success: true };
  }
}
