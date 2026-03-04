/* ─── Verdict Config (AACS Bands) ─── */
export const VERDICT_CONFIG = {
  AUTHENTIC: { label: 'Authentic', color: '#39ff14', emoji: '✅', band: '0–30' },
  UNCERTAIN: { label: 'Uncertain', color: '#ffd700', emoji: '⚠️', band: '31–60' },
  LIKELY_FAKE: { label: 'Likely Fake', color: '#ff8c00', emoji: '🔶', band: '61–85' },
  DEFINITELY_FAKE: { label: 'Definitely Fake', color: '#ff3c00', emoji: '🚨', band: '86–100' },
};

/* ─── AACS Sub-Score Keys ─── */
export const SUB_SCORES = [
  { key: 'mas', label: 'Media Authenticity (MAS)', weight: 0.30, icon: 'ScanFace', desc: 'EfficientNet-B4 + forensic artifact detection' },
  { key: 'pps', label: 'Physiological (PPS)', weight: 0.25, icon: 'HeartPulse', desc: 'rPPG heartbeat + blink analysis' },
  { key: 'irs', label: 'Information (IRS)', weight: 0.20, icon: 'FileText', desc: 'DistilBERT text + metadata analysis' },
  { key: 'aas', label: 'Audio Authenticity (AAS)', weight: 0.15, icon: 'Mic', desc: 'Librosa spectral + MFCC analysis' },
  { key: 'cvs', label: 'Context Verification (CVS)', weight: 0.10, icon: 'Globe', desc: 'Reverse image search + news cross-check' },
];

/* ─── Language Options ─── */
export const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'te', label: 'తెలుగు' },
  { code: 'bn', label: 'বাংলা' },
  { code: 'mr', label: 'मराठी' },
  { code: 'kn', label: 'ಕನ್ನಡ' },
  { code: 'ml', label: 'മലയാളം' },
];

/* ─── Sample Files For Demo ─── */
export const SAMPLE_FILES = [
  { name: 'sample_deepfake.mp4', type: 'video/mp4', label: 'Sample Deepfake Video' },
  { name: 'sample_real.jpg', type: 'image/jpeg', label: 'Sample Real Image' },
  { name: 'sample_audio.wav', type: 'audio/wav', label: 'Sample Audio' },
];

/* ─── Accepted File Types ─── */
export const ACCEPTED_FILE_TYPES = {
  'image/*': ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'],
  'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
  'audio/*': ['.wav', '.mp3', '.ogg', '.flac', '.m4a'],
};

/* ─── Analysis Steps ─── */
export const ANALYSIS_STEPS = [
  'Receiving upload',
  'Extracting frames',
  'Running face-swap detector',
  'Running lip-sync check',
  'Running forensic analysis',
  'Running physiological signals',
  'Cross-referencing context',
  'Fusing CDCF scores',
  'Generating report',
];

/* ─── Color Palette ─── */
export const COLORS = {
  bg: '#0a0a0f',
  red: '#ff3c00',
  silver: '#e0e0e0',
  yellow: '#ffd700',
  cyan: '#00f5ff',
  green: '#39ff14',
  muted: '#888888',
  card: '#111116',
  border: '#e0e0e0',
};
