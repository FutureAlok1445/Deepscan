import axios from 'axios';

// ─── Base URL: empty in dev (uses Vite proxy), full URL in prod ───
const isDev = import.meta.env.DEV;
const BASE_URL = isDev ? '' : (import.meta.env.VITE_API_URL || '');

const api = axios.create({
  baseURL: BASE_URL + '/api/v1',
  timeout: 60000,
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

// WebSocket URL: in dev goes through Vite proxy, in prod uses configured URL
export const WS_URL = isDev
  ? `ws://${typeof window !== 'undefined' ? window.location.host : 'localhost:3000'}`
  : (import.meta.env.VITE_WS_URL || BASE_URL.replace(/^http/, 'ws'));

// ─── Session ID ───
export function getSessionId() {
  let sid = sessionStorage.getItem('ds_session');
  if (!sid) {
    sid = 'sess_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);
    sessionStorage.setItem('ds_session', sid);
  }
  return sid;
}

// ─── Health Check ───
export async function checkHealth() {
  try {
    const res = await axios.get(BASE_URL + '/health', { timeout: 5000 });
    return { ok: true, data: res.data };
  } catch {
    return { ok: false, data: null };
  }
}

// ─── Mock Data ───
const MOCK_RESULT = {
  id: 'mock-001',
  aacs_score: 89,
  score: 89,
  verdict: 'DEFINITELY_FAKE',
  filename: 'CEO_Video_Suspicious.mp4',
  file_type: 'video',
  file_size: 4823040,
  status: 'complete',
  sub_scores: { mas: 87, pps: 92, irs: 84, aas: 91, cvs: 76 },
  cdcf: {
    multiplier: 1.03,
    contradictions: ['AAS↔CVS'],
    confidence_note: 'Minor contradiction between audio authenticity and context verification.',
    consensus: 82,
    dissent: 18,
    confidence: 88,
    fusion_method: 'CDCF + XGBoost',
    module_votes: [
      { module: 'EfficientNet-B4 (MAS)', verdict: 'fake' },
      { module: 'rPPG Heartbeat (PPS)', verdict: 'fake' },
      { module: 'DistilBERT (IRS)', verdict: 'fake' },
      { module: 'Audio MFCC (AAS)', verdict: 'fake' },
      { module: 'Reverse Search (CVS)', verdict: 'real' },
    ],
  },
  findings: [
    { severity: 'high', title: 'Lip-sync offset detected', detail: '4 frames behind audio track', engine: 'VIDEO', confidence: 91 },
    { severity: 'high', title: 'Synthetic voice markers', detail: '92% probability of TTS origin', engine: 'AUDIO', confidence: 92 },
    { severity: 'high', title: 'ELA anomaly: cheek region', detail: 'High error energy in right cheek ROI', engine: 'IMAGE', confidence: 78 },
    { severity: 'medium', title: 'EXIF metadata inconsistent', detail: 'Timestamp mismatch detected', engine: 'META', confidence: 65 },
    { severity: 'medium', title: 'Frequency domain anomaly', detail: 'FFT shows unnatural patterns at 4.2kHz', engine: 'AUDIO', confidence: 70 },
    { severity: 'low', title: 'Compression artifacts', detail: 'Double JPEG compression detected', engine: 'IMAGE', confidence: 55 },
    { severity: 'normal', title: 'File size: normal range', detail: 'No unusual compression', engine: 'FILE' },
    { severity: 'normal', title: 'Resolution: standard 1080p', detail: 'Frame dimensions consistent', engine: 'VIDEO' },
  ],
  heartbeat: {
    is_deepfake: true,
    bpm: 0,
    confidence: 0.96,
    signal: Array.from({ length: 120 }, (_, i) => ({
      time: +(i * 0.033).toFixed(3),
      value: Math.random() * 0.05 - 0.025,
    })),
    real_reference: Array.from({ length: 120 }, (_, i) => ({
      time: +(i * 0.033).toFixed(3),
      value: Math.sin(i * 0.15) * 0.4 + (Math.random() * 0.05),
    })),
  },
  processing_time_ms: 1847,
  created_at: new Date().toISOString(),
  narrative: {
    summary: 'This video exhibits strong indicators of AI manipulation across multiple detection engines.',
    eli5: "This video was probably made by a computer. The person's heartbeat couldn't be found, and the voice doesn't match the lips.",
    detailed: 'EfficientNet-B4 classified the face region with 87% deepfake probability. The rPPG module detected no viable heartbeat signal (flat-line). Audio analysis revealed 92% TTS probability with unnatural harmonic patterns at 4.2kHz.',
    technical: 'MAS=87 (EfficientNet-B4 logit: 2.31, ELA energy: 78.4), PPS=92 (rPPG: flat), IRS=84 (DistilBERT confidence: 0.84), AAS=91 (MFCC anomaly: σ=3.2), CVS=76. CDCF multiplier: 1.03x. Final AACS: 89.',
  },
  forensics: {
    ela: { score: 78, image_url: null, description: 'High error energy detected in facial region, particularly right cheek area.' },
    fft: { score: 65, image_url: null, description: 'Periodic artifacts at spatial frequency consistent with GAN generation.' },
    noise: { score: 72, description: 'Inconsistent noise patterns between face region and background.' },
    metadata: {
      Software: 'Unknown', creation_date: null, camera: null, gps: null,
      modified: true, description: 'No EXIF camera data found. File re-encoded.',
    },
  },
  gradcam: {
    original_url: null,
    heatmap_url: null,
    regions: [
      { x: 35, y: 20, w: 25, h: 30, label: 'Right cheek', confidence: 0.91, severity: 'high' },
      { x: 55, y: 40, w: 15, h: 20, label: 'Jaw line', confidence: 0.78, severity: 'medium' },
      { x: 20, y: 15, w: 20, h: 25, label: 'Forehead', confidence: 0.65, severity: 'low' },
    ],
  },
  audio: {
    spectrum: Array.from({ length: 50 }, (_, i) => ({
      freq: `${(i * 0.4).toFixed(1)}kHz`,
      amplitude: Math.random() * 80 + 20,
      baseline: 50 + Math.sin(i * 0.3) * 20,
    })),
    clone_probability: 92,
    splicing_detected: true,
    anomalies: [
      { label: 'Harmonic anomaly at 4.2kHz', freq_start: 4000, freq_end: 4400 },
      { label: 'Spectral discontinuity at 8.1kHz', freq_start: 8000, freq_end: 8200 },
    ],
  },
};

const MOCK_HISTORY = [
  {
    id: 'mock-001', score: 89, aacs_score: 89, verdict: 'DEFINITELY_FAKE',
    filename: 'CEO_Video_Suspicious.mp4', file_type: 'video',
    created_at: new Date().toISOString(),
  },
  {
    id: 'mock-002', score: 23, aacs_score: 23, verdict: 'AUTHENTIC',
    filename: 'Family_Photo.jpg', file_type: 'image',
    created_at: '2025-11-13T14:20:00Z',
  },
  {
    id: 'mock-003', score: 54, aacs_score: 54, verdict: 'UNCERTAIN',
    filename: 'Voice_Clip_Suspect.wav', file_type: 'audio',
    created_at: '2025-11-12T09:15:00Z',
  },
];

const MOCK_COMMUNITY = [
  {
    id: 'alert-001', title: 'Deepfake election ad circulating on WhatsApp',
    description: 'AI-generated video of political leader making false promises.',
    tags: ['politics', 'video', 'whatsapp'], score: 94, verdict: 'DEFINITELY_FAKE',
    reporter: 'community', created_at: '2025-11-14T06:30:00Z', upvotes: 23, downvotes: 2,
  },
  {
    id: 'alert-002', title: 'Synthetic voice claiming to be bank officer',
    description: 'AI-cloned voices impersonating SBI officer for account details.',
    tags: ['audio', 'scam', 'voice-clone'], score: 71, verdict: 'LIKELY_FAKE',
    reporter: 'anonymous', created_at: '2025-11-14T08:45:00Z', upvotes: 15, downvotes: 1,
  },
  {
    id: 'alert-003', title: 'Manipulated Aadhaar card image',
    description: 'GAN-generated Aadhaar photos used for fraudulent KYC.',
    tags: ['image', 'aadhaar', 'fraud'], score: 88, verdict: 'DEFINITELY_FAKE',
    reporter: 'community', created_at: '2025-11-13T22:10:00Z', upvotes: 45, downvotes: 3,
  },
];

function useMock() { return false; }

// ─── LocalStorage DB Helpers for Dynamic Fallback ───
function getLocalDB(key, defaultData) {
  const data = localStorage.getItem(key);
  if (data) return JSON.parse(data);
  localStorage.setItem(key, JSON.stringify(defaultData));
  return defaultData;
}
function setLocalDB(key, data) {
  localStorage.setItem(key, JSON.stringify(data));
}

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
  // Map elapsed_seconds → processing_time_ms if missing
  if (!data.processing_time_ms && data.elapsed_seconds) {
    data.processing_time_ms = Math.round(data.elapsed_seconds * 1000);
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

export async function analyzeFile(file, onUploadProgress, language = 'en') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('language', language);
  formData.append('session_id', getSessionId());
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

export async function analyzeUrl(url, language = 'en') {
  const res = await api.post('/analyze/url', { url, language, session_id: getSessionId() });
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
    const items = Array.isArray(data) ? data : (data.items || []);
    // Normalize backend field names → frontend AlertCard expected fields
    return items.map(item => ({
      ...item,
      score: item.score ?? item.trust_score ?? 0,
      description: item.description ?? item.content ?? '',
      reporter: item.reporter ?? item.submitted_by ?? 'anonymous',
      upvotes: item.upvotes ?? 0,
      downvotes: item.downvotes ?? 0,
    }));
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
