import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

export const WS_URL = BASE_URL.replace('http', 'ws');

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

function useMock() { return import.meta.env.MODE === 'development'; }

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
  return data;
}

export async function analyzeFile(file, language = 'hi') {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('language_preference', language);
    const res = await api.post('/analyze', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    return normalizeResult(res.data);
  } catch (err) {
    if (useMock()) {
      const db = getLocalDB('ds_results', {});
      const hist = getLocalDB('ds_history', MOCK_HISTORY);
      const id = 'dev-' + Date.now();
      const newRes = { ...MOCK_RESULT, id, filename: file.name, created_at: new Date().toISOString() };
      db[id] = newRes;
      hist.unshift({
        id, score: newRes.score, aacs_score: newRes.aacs_score, verdict: newRes.verdict,
        filename: newRes.filename, file_type: file.type.split('/')[0] || 'unknown',
        created_at: newRes.created_at,
      });
      setLocalDB('ds_results', db);
      setLocalDB('ds_history', hist);
      return newRes;
    }
    throw err;
  }
}

export async function analyzeUrl(url, language = 'hi') {
  try {
    const res = await api.post('/analyze/url', { url, language_preference: language });
    return normalizeResult(res.data);
  } catch (err) {
    if (useMock()) {
      const db = getLocalDB('ds_results', {});
      const hist = getLocalDB('ds_history', MOCK_HISTORY);
      const id = 'dev-url-' + Date.now();
      const filename = url.split('/').pop() || url;
      const newRes = { ...MOCK_RESULT, id, filename, created_at: new Date().toISOString() };
      db[id] = newRes;
      hist.unshift({
        id, score: newRes.score, aacs_score: newRes.aacs_score, verdict: newRes.verdict,
        filename, file_type: 'url', created_at: newRes.created_at,
      });
      setLocalDB('ds_results', db);
      setLocalDB('ds_history', hist);
      return newRes;
    }
    throw err;
  }
}

export async function getResult(id) {
  try {
    const res = await api.get(`/analyze/${id}`);
    return normalizeResult(res.data);
  } catch (err) {
    if (useMock()) {
      const db = getLocalDB('ds_results', {});
      if (db[id]) return db[id];
      if (id.startsWith('mock-')) return { ...MOCK_RESULT, id };
      throw new Error("Result not found in local mock DB");
    }
    throw err;
  }
}

export async function downloadReport(id) {
  try {
    const res = await api.get(`/report/${id}`, { responseType: 'blob' });
    return res.data;
  } catch (err) {
    if (useMock()) { console.log('Mock: PDF download for', id); return null; }
    throw err;
  }
}

export async function getHistory() {
  try {
    const res = await api.get('/history');
    const data = res.data;
    return Array.isArray(data) ? data : (data.items || []);
  } catch (err) {
    if (useMock()) return getLocalDB('ds_history', MOCK_HISTORY);
    throw err;
  }
}

export async function getCommunityAlerts() {
  try {
    const res = await api.get('/community');
    const data = res.data;
    return Array.isArray(data) ? data : (data.items || []);
  } catch (err) {
    if (useMock()) return getLocalDB('ds_community', MOCK_COMMUNITY);
    throw err;
  }
}

export async function submitCommunityReport(url, note) {
  try {
    const res = await api.post('/community', {
      title: 'User Report: ' + (url || 'Unknown'),
      content: note || '',
      tags: ['user-report'],
      submitted_by: 'anonymous',
    });
    return res.data;
  } catch (err) {
    if (useMock()) {
      const comm = getLocalDB('ds_community', MOCK_COMMUNITY);
      comm.unshift({
        id: 'user-alert-' + Date.now(), title: 'User Report: ' + (url || 'Unknown'),
        description: note || '', tags: ['user-report', 'pending'], score: 50, verdict: 'UNCERTAIN',
        reporter: 'You (Local)', created_at: new Date().toISOString(), upvotes: 1, downvotes: 0,
      });
      setLocalDB('ds_community', comm);
      return { status: 'success' };
    }
    throw err;
  }
}

export async function submitFeedback(args) {
  const id = args.alertId || args.id;
  const isCorrect = args.vote ? args.vote === 'up' : args.isCorrect;
  const comment = args.comment || '';
  try {
    return (await api.post('/feedback', { analysis_id: id, is_correct: isCorrect, comment })).data;
  } catch (err) {
    if (useMock() && args.alertId) {
      // Handle community upvote/downvote
      const comm = getLocalDB('ds_community', MOCK_COMMUNITY);
      const item = comm.find(c => c.id === args.alertId);
      if (item) {
        if (args.vote === 'up') item.upvotes = (item.upvotes || 0) + 1;
        else if (args.vote === 'down') item.downvotes = (item.downvotes || 0) + 1;
        setLocalDB('ds_community', comm);
      }
      return { success: true };
    }
    if (useMock()) return { success: true };
    throw err;
  }
}
