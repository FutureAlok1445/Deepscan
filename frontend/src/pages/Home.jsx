import React, { useEffect, useRef, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion';
import {
  Shield, Upload, Brain, Eye, BarChart3, Users, ChevronDown,
  Zap, Lock, Layers, Globe, ArrowRight, Play, HeartPulse,
  Mic, ScanFace, FileText, Radio, AlertTriangle, Search,
  Fingerprint, Cpu, Activity, Waves, Scan, MonitorCheck,
} from 'lucide-react';
import * as THREE from 'three';
import BrutalButton from '../components/ui/BrutalButton';
import BrutalCard from '../components/ui/BrutalCard';
import PaperTear from '../components/ui/PaperTear';
import TerminalText from '../components/ui/TerminalText';
import { ContainerScroll } from '../components/ui/ContainerScrollAnimation';

gsap.registerPlugin(ScrollTrigger);

/* ═══ Constants ═══ */
const STATS = [
  { value: '8+', label: 'Detection Engines', icon: Brain, color: '#ff3c00' },
  { value: '99.2%', label: 'Accuracy Rate', icon: Shield, color: '#39ff14' },
  { value: '<3s', label: 'Avg Scan Time', icon: Zap, color: '#00f5ff' },
  { value: '8', label: 'Indian Languages', icon: Globe, color: '#ffd700' },
];

const PIPELINE_STEPS = [
  { icon: Upload, title: 'Upload Media', desc: 'Drop any image, video, or audio file. We accept 15+ formats including WhatsApp forwards.', color: '#ff3c00' },
  { icon: ScanFace, title: 'AI Detection', desc: 'EfficientNet-B4, DistilBERT, librosa, and 5 more engines analyze every pixel and frequency.', color: '#00f5ff' },
  { icon: HeartPulse, title: 'rPPG Analysis', desc: 'Our secret weapon: extract heartbeat signals from video. Real faces pulse — deepfakes flatline.', color: '#39ff14' },
  { icon: Layers, title: 'CDCF Fusion', desc: 'Cross-Domain Consistency Fusion weighs all detector votes. Contradictions are flagged.', color: '#ffd700' },
  { icon: Eye, title: 'Explainable Report', desc: 'Grad-CAM heatmaps, heartbeat charts, Hindi narration — see exactly WHY the AI decided.', color: '#ff3c00' },
];

const FEATURES = [
  { icon: Zap, title: 'Multi-Modal', desc: 'Image, video, audio, and text analysis in one platform — no competitor covers all 4.', color: '#ff3c00' },
  { icon: Lock, title: 'Privacy First', desc: 'Files are processed in-memory and deleted instantly. Nothing stored permanently.', color: '#00f5ff' },
  { icon: Globe, title: '8 Languages', desc: 'Results narrated in Hindi, Tamil, Telugu, Bengali, Marathi, and more.', color: '#39ff14' },
  { icon: BarChart3, title: 'Forensic Reports', desc: 'PDF reports with ELA, FFT, noise analysis, and EXIF metadata for police complaints.', color: '#ffd700' },
  { icon: Users, title: 'Community Alerts', desc: 'Crowdsourced database of known deepfakes circulating in India.', color: '#ff3c00' },
  { icon: Radio, title: 'Telegram Bot', desc: 'Forward any media to @DeepScanBot for instant 30-second verification.', color: '#00f5ff' },
];

const AACS_FORMULA = [
  { label: 'MAS', weight: '0.30', color: '#ff3c00', desc: 'Media Authenticity', icon: ScanFace },
  { label: 'PPS', weight: '0.25', color: '#39ff14', desc: 'Physiological', icon: HeartPulse },
  { label: 'IRS', weight: '0.20', color: '#00f5ff', desc: 'Information', icon: FileText },
  { label: 'AAS', weight: '0.15', color: '#ffd700', desc: 'Audio Authenticity', icon: Mic },
  { label: 'CVS', weight: '0.10', color: '#e0e0e0', desc: 'Context Verification', icon: Search },
];

const THREAT_CASES = [
  { icon: AlertTriangle, title: 'CEO Voice Clone', desc: 'Fake CFO call — Rs 8 Cr transferred, Mumbai 2024', color: '#ff3c00', defense: 'AAS Score detects synthetic voice markers' },
  { icon: Fingerprint, title: 'Aadhaar Face Swap', desc: 'AI-generated Aadhaar used for Rs 50L loan fraud', color: '#ffd700', defense: 'EfficientNet-B4 + ELA catches face artifacts' },
  { icon: Waves, title: 'WhatsApp Scam Video', desc: 'PM Modi fake video — 2M shares in 6 hours', color: '#00f5ff', defense: 'Multi-modal scan + Telegram Bot verdicts' },
  { icon: MonitorCheck, title: 'Evidence Tampering', desc: 'Edited CCTV footage submitted as legal evidence', color: '#39ff14', defense: 'PDF forensic report + EXIF metadata analysis' },
];

/* ═══ SCANNING ANIMATION STEPS ═══ */
const SCAN_STEPS = [
  { label: 'Initializing 8 AI engines...', progress: 8 },
  { label: 'EfficientNet-B4 spatial analysis', progress: 18 },
  { label: 'Extracting face ROI regions', progress: 28 },
  { label: 'Running ELA & FFT forensics', progress: 38 },
  { label: 'Detecting rPPG heartbeat signal', progress: 50 },
  { label: 'Audio MFCC spectrum analysis', progress: 60 },
  { label: 'EXIF metadata cross-check', progress: 70 },
  { label: 'Computing CDCF fusion scores', progress: 80 },
  { label: 'AACS = 89.3 — DEFINITELY FAKE', progress: 92 },
  { label: 'Generating forensic report...', progress: 100 },
];

export default function Home() {
  const containerRef = useRef(null);

  // NOTE: GSAP ScrollTriggers removed per user request for fixing visibility bugs

  return (
    <div ref={containerRef} className="min-h-screen bg-ds-bg text-ds-silver overflow-hidden">

      {/* ═══ SPIDER-VERSE HERO ═══ */}
      <SpiderVerseHero />

      {/* ═══ CONTAINER SCROLL — TABLET SCANNING DEMO ═══ */}
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-b from-ds-bg via-transparent to-ds-bg pointer-events-none z-10" />
        <ContainerScroll
          titleComponent={
            <div className="mb-8">
              <p className="text-xs font-mono text-ds-cyan uppercase tracking-[0.3em] mb-3">
                // LIVE ANALYSIS PREVIEW
              </p>
              <h2 className="text-3xl md:text-5xl font-grotesk font-black leading-tight text-ds-silver">
                See <span className="text-ds-cyan neon-cyan">DeepScan</span> in Action
              </h2>
              <p className="mt-4 max-w-2xl mx-auto text-ds-silver font-mono text-sm">
                Watch 8 AI engines analyze a deepfake video in real-time — powered by our AACS formula.
              </p>
            </div>
          }
        >
          <TabletScanAnimation />
        </ContainerScroll>
      </div>

      <PaperTear />

      {/* ═══ THE PROBLEM ═══ */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-xs font-mono text-ds-red uppercase tracking-[0.3em] mb-3">// THE THREAT</p>
          <h2 className="text-3xl md:text-5xl font-grotesk font-black leading-tight">
            India Faces a <span className="text-ds-red neon-red">Deepfake Crisis</span>
          </h2>
          <p className="mt-4 max-w-2xl mx-auto text-ds-silver font-mono text-sm leading-relaxed">
            Rs 7,061 Cr lost to cyber fraud in 2023. Over 40% involved AI-manipulated media.
            The deepfake market is growing at 37.45% CAGR — our defense must accelerate.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { stat: '96%', desc: "of Indians can not detect deepfakes", color: '#ff3c00' },
            { stat: 'Rs 7,061Cr', desc: 'lost to cyber fraud in 2023', color: '#ffd700' },
            { stat: '500%', desc: 'increase in deepfake content', color: '#ff3c00' },
          ].map((item, i) => (
            <div key={i} className="gs-stat">
              <div className="text-center py-10 px-6 border-3 border-ds-silver/20 bg-ds-card relative overflow-hidden brutal-shadow card-hover-lift">
                <div className="absolute inset-0 bg-gradient-to-br from-transparent via-transparent to-ds-red/5" />
                <div className="absolute top-0 left-0 w-full h-1" style={{ background: item.color }} />
                <p className="text-3xl sm:text-5xl font-grotesk font-black relative z-10" style={{ color: item.color }}>{item.stat}</p>
                <p className="mt-2 sm:mt-3 text-xs sm:text-sm font-mono text-ds-silver relative z-10 font-bold">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <PaperTear flip />

      {/* ═══ DETECTION PIPELINE ═══ */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-xs font-mono text-ds-cyan uppercase tracking-[0.3em] mb-3">// DETECTION PIPELINE</p>
          <h2 className="text-3xl md:text-5xl font-grotesk font-black leading-tight">
            Five Steps to <span className="text-ds-cyan neon-cyan">Truth</span>
          </h2>
        </div>
        <div className="gs-pipeline-container space-y-4">
          {PIPELINE_STEPS.map((step, i) => (
            <div key={i} className="">
              <div
                className="flex items-start gap-3 sm:gap-6 p-3 sm:p-6 border-3 border-ds-silver/40 bg-ds-card hover:border-ds-silver/70 transition-all group relative overflow-hidden card-hover-lift"
                style={{ borderLeftColor: step.color, borderLeftWidth: 4 }}
              >
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                  style={{ background: `linear-gradient(90deg, ${step.color}10, transparent)` }} />
                <div className="flex-shrink-0 relative z-10 flex items-center justify-center w-10 h-10 sm:w-14 sm:h-14 border-3 border-ds-silver/30" style={{ color: step.color }}>
                  <step.icon className="w-5 h-5 sm:w-7 sm:h-7" />
                </div>
                <div className="relative z-10 flex-1">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs" style={{ color: step.color }}>STEP {String(i + 1).padStart(2, '0')}</span>
                    <h3 className="font-grotesk font-bold text-lg">{step.title}</h3>
                  </div>
                  <p className="text-sm font-mono text-ds-silver leading-relaxed mt-1">{step.desc}</p>
                </div>
                <div className="hidden md:flex items-center">
                  {i < PIPELINE_STEPS.length - 1 && (
                    <ArrowRight className="w-5 h-5 text-ds-silver" />
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <PaperTear flip />

      {/* ═══ AACS FORMULA ═══ */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <p className="text-xs font-mono text-ds-green uppercase tracking-[0.3em] mb-3">// SCORING ENGINE</p>
          <h2 className="text-3xl md:text-5xl font-grotesk font-black leading-tight">
            AACS <span className="text-ds-green neon-green">Formula</span>
          </h2>
          <p className="mt-4 text-sm font-mono text-ds-silver max-w-xl mx-auto">
            AI Authenticity Confidence Score — a weighted fusion of 5 sub-scores, multiplied by the CDCF contradiction penalty.
          </p>
        </div>
        <div className="gs-formula-container">
          <div className="text-center mb-10 p-3 sm:p-6 border-3 border-ds-green/30 bg-ds-card relative overflow-hidden">
            <div className="absolute inset-0 cyber-grid opacity-30" />
            <p className="font-mono text-xs sm:text-lg md:text-xl text-ds-silver relative z-10 leading-relaxed">
              AACS = (<span className="text-ds-red font-bold">0.30</span>×MAS + <span className="text-ds-green font-bold">0.25</span>×PPS + <span className="text-ds-cyan font-bold">0.20</span>×IRS + <span className="text-ds-yellow font-bold">0.15</span>×AAS + <span className="text-ds-silver font-bold">0.10</span>×CVS) × <span className="text-ds-red font-bold">CDCF</span>
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {AACS_FORMULA.map((item) => (
              <div key={item.label} className="gs-formula-block text-center p-5 border-3 border-ds-silver/40 bg-ds-card hover:scale-105 transition-transform card-hover-lift relative overflow-hidden">
                <div className="absolute inset-0 opacity-20" style={{ background: `radial-gradient(circle at bottom, ${item.color}, transparent 70%)` }} />
                <item.icon className="w-6 h-6 mx-auto mb-2 relative z-10" style={{ color: item.color }} />
                <p className="text-3xl font-grotesk font-black relative z-10" style={{ color: item.color }}>{item.weight}</p>
                <p className="font-mono text-sm font-bold mt-1 relative z-10" style={{ color: item.color }}>{item.label}</p>
                <p className="text-xs font-mono text-ds-silver mt-1 relative z-10">{item.desc}</p>
              </div>
            ))}
          </div>
          <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { range: '0-30', label: 'AUTHENTIC', color: '#39ff14', bg: 'rgba(57,255,20,0.1)' },
              { range: '31-60', label: 'UNCERTAIN', color: '#ffd700', bg: 'rgba(255,215,0,0.1)' },
              { range: '61-85', label: 'LIKELY FAKE', color: '#ff8c00', bg: 'rgba(255,140,0,0.1)' },
              { range: '86-100', label: 'DEFINITELY FAKE', color: '#ff3c00', bg: 'rgba(255,60,0,0.1)' },
            ].map((v) => (
              <div key={v.label} className="p-4 border-3 text-center relative overflow-hidden card-hover-lift" style={{ borderColor: v.color, background: v.bg }}>
                <p className="font-grotesk font-black text-2xl" style={{ color: v.color }}>{v.range}</p>
                <p className="font-mono text-xs mt-1 font-bold" style={{ color: v.color }}>{v.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <PaperTear />

      {/* ═══ FEATURES ═══ */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-xs font-mono text-ds-yellow uppercase tracking-[0.3em] mb-3">// CAPABILITIES</p>
          <h2 className="text-3xl md:text-5xl font-grotesk font-black leading-tight">
            Built for <span className="text-ds-yellow neon-yellow">India</span>
          </h2>
        </div>
        <div className="gs-features-container grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((feat, i) => (
            <div key={i} className="" style={{ perspective: '800px' }}>
              <div className="h-full p-6 border-3 border-ds-silver/40 bg-ds-card group relative overflow-hidden card-hover-lift">
                <div className="absolute top-0 right-0 w-24 h-24 opacity-20"
                  style={{ background: `radial-gradient(circle, ${feat.color}, transparent)` }} />
                <div className="absolute top-0 left-0 w-full h-1" style={{ background: feat.color }} />
                <feat.icon className="w-8 h-8 mb-3 group-hover:scale-110 transition-transform" style={{ color: feat.color }} />
                <h3 className="font-grotesk font-bold text-lg mb-2">{feat.title}</h3>
                <p className="text-sm font-mono text-ds-silver leading-relaxed">{feat.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <PaperTear flip />

      {/* ═══ THREAT INTELLIGENCE ═══ */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-xs font-mono text-ds-red uppercase tracking-[0.3em] mb-3">// THREAT INTELLIGENCE</p>
          <h2 className="text-3xl md:text-5xl font-grotesk font-black leading-tight">
            Real <span className="text-ds-red neon-red">Indian</span> Cyber Threats
          </h2>
          <p className="mt-4 text-sm font-mono text-ds-silver max-w-xl mx-auto">
            Every feature maps to a documented cyber fraud case in India.
          </p>
        </div>
        <div className="gs-threats-container grid grid-cols-1 md:grid-cols-2 gap-6">
          {THREAT_CASES.map((threat, i) => (
            <div key={i} className="">
              <div className="p-6 border-3 border-ds-silver/40 bg-ds-card relative overflow-hidden group card-hover-lift">
                <div className="absolute top-0 left-0 w-1 h-full" style={{ background: threat.color }} />
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center border-3 border-ds-silver/20" style={{ color: threat.color }}>
                    <threat.icon className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-grotesk font-bold text-base mb-1" style={{ color: threat.color }}>{threat.title}</h3>
                    <p className="text-xs font-mono text-ds-silver mb-3 font-bold">{threat.desc}</p>
                    <div className="p-2 bg-ds-bg border border-ds-silver/30">
                      <p className="text-xs font-mono text-ds-green">{threat.defense}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <PaperTear />

      {/* ═══ RPPG SECRET WEAPON ═══ */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <p className="text-xs font-mono text-ds-green uppercase tracking-[0.3em] mb-3">// SECRET WEAPON</p>
          <h2 className="text-3xl md:text-5xl font-grotesk font-black leading-tight">
            <span className="text-ds-green neon-green">Heartbeat</span> Detection
          </h2>
          <p className="mt-4 text-sm font-mono text-ds-silver max-w-xl mx-auto">
            No other tool in India uses rPPG (Remote Photoplethysmography) to detect deepfakes.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          <div className="space-y-4">
            <p className="text-sm font-mono text-ds-silver leading-relaxed">
              Real human faces exhibit subtle color changes caused by blood flow — invisible to the naked eye,
              but detectable by our <span className="text-ds-green font-bold">rPPG engine</span>.
            </p>
            <p className="text-sm font-mono text-ds-silver leading-relaxed">
              Deepfake-generated faces have <span className="text-ds-red font-bold">no heartbeat signal</span> —
              they flatline. This is one of the most powerful and hardest-to-fake detection signals.
            </p>
            <div className="flex gap-4 mt-6">
              <div className="flex-1 p-4 border-3 border-ds-green/30 bg-ds-green/5 text-center neon-box-green">
                <HeartPulse className="w-8 h-8 text-ds-green mx-auto mb-2" />
                <p className="font-grotesk font-bold text-ds-green">Real Face</p>
                <p className="text-xs font-mono text-ds-silver mt-1">72 BPM detected</p>
              </div>
              <div className="flex-1 p-4 border-3 border-ds-red/30 bg-ds-red/5 text-center neon-box-red">
                <HeartPulse className="w-8 h-8 text-ds-red mx-auto mb-2" />
                <p className="font-grotesk font-bold text-ds-red">Deepfake</p>
                <p className="text-xs font-mono text-ds-silver mt-1">FLATLINE — 0 BPM</p>
              </div>
            </div>
          </div>
          <HeartbeatVisual />
        </div>
      </section>

      <PaperTear flip />

      {/* ═══ FINAL CTA ═══ */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 relative">
        <div className="absolute inset-0 cyber-grid opacity-20" />
        <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse at center, rgba(255,60,0,0.05), transparent 70%)' }} />
        <div className="max-w-3xl mx-auto text-center relative z-10">
          <p className="text-xs font-mono text-ds-red uppercase tracking-[0.3em] mb-3">// TAKE ACTION</p>
          <h2 className="text-4xl md:text-6xl font-grotesk font-black leading-tight">
            Do Not Get <span className="text-ds-red neon-red">Fooled</span>
          </h2>
          <p className="mt-4 text-ds-silver font-mono text-sm max-w-xl mx-auto leading-relaxed">
            Upload any suspicious media and get a detailed AI-powered analysis in seconds.
            Free. Private. Made in India.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
            <BrutalButton as={Link} to="/analyze" size="lg">
              <Upload className="w-5 h-5" /> Start Scanning
            </BrutalButton>
            <BrutalButton as={Link} to="/learn" variant="secondary" size="lg">
              <Play className="w-5 h-5" /> Learn More
            </BrutalButton>
          </div>
          <p className="mt-6 text-xs font-mono text-ds-silver">
            DeepScan — Multi-modal AI deepfake detection platform
          </p>
        </div>
      </section>
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════════════════
   SPIDER-VERSE HERO — Multi-layered glitch text, halftone, particles
   ═══════════════════════════════════════════════════════════════════════ */
function SpiderVerseHero() {
  const mountRef = useRef(null);
  const heroRef = useRef(null);
  const [showStats, setShowStats] = useState(false);
  const [glitchActive, setGlitchActive] = useState(false);

  // Random glitch bursts
  useEffect(() => {
    const interval = setInterval(() => {
      setGlitchActive(true);
      setTimeout(() => setGlitchActive(false), 150 + Math.random() * 200);
    }, 3000 + Math.random() * 2000);
    return () => clearInterval(interval);
  }, []);

  // Three.js particles
  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, mount.clientWidth / mount.clientHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    const particleCount = 250;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const velocities = [];

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 28;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 28;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 14;
      const r = Math.random();
      if (r < 0.35) { colors[i * 3] = 1; colors[i * 3 + 1] = 0.24; colors[i * 3 + 2] = 0; }
      else if (r < 0.55) { colors[i * 3] = 0; colors[i * 3 + 1] = 0.96; colors[i * 3 + 2] = 1; }
      else if (r < 0.7) { colors[i * 3] = 0.22; colors[i * 3 + 1] = 1; colors[i * 3 + 2] = 0.08; }
      else { colors[i * 3] = 0.88; colors[i * 3 + 1] = 0.88; colors[i * 3 + 2] = 0.88; }
      velocities.push({
        x: (Math.random() - 0.5) * 0.015,
        y: (Math.random() - 0.5) * 0.015,
        z: (Math.random() - 0.5) * 0.007,
      });
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    const material = new THREE.PointsMaterial({ size: 0.09, vertexColors: true, transparent: true, opacity: 0.9, sizeAttenuation: true });
    const points = new THREE.Points(geometry, material);
    scene.add(points);

    const lineGeo = new THREE.BufferGeometry();
    const maxLines = particleCount * 6;
    const linePositions = new Float32Array(maxLines * 6);
    lineGeo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    const lineMat = new THREE.LineBasicMaterial({ color: 0xff3c00, transparent: true, opacity: 0.06 });
    const lines = new THREE.LineSegments(lineGeo, lineMat);
    scene.add(lines);

    camera.position.z = 10;

    let mouseX = 0, mouseY = 0;
    const onMouseMove = (e) => {
      mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
      mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    };
    window.addEventListener('mousemove', onMouseMove);

    let frame;
    const animate = () => {
      frame = requestAnimationFrame(animate);
      const pos = geometry.attributes.position.array;
      for (let i = 0; i < particleCount; i++) {
        pos[i * 3] += velocities[i].x;
        pos[i * 3 + 1] += velocities[i].y;
        pos[i * 3 + 2] += velocities[i].z;
        if (Math.abs(pos[i * 3]) > 14) velocities[i].x *= -1;
        if (Math.abs(pos[i * 3 + 1]) > 14) velocities[i].y *= -1;
        if (Math.abs(pos[i * 3 + 2]) > 7) velocities[i].z *= -1;
      }
      geometry.attributes.position.needsUpdate = true;

      let lineIdx = 0;
      const lpos = lineGeo.attributes.position.array;
      for (let i = 0; i < particleCount && lineIdx < maxLines * 6; i++) {
        for (let j = i + 1; j < particleCount && lineIdx < maxLines * 6; j++) {
          const dx = pos[i * 3] - pos[j * 3];
          const dy = pos[i * 3 + 1] - pos[j * 3 + 1];
          const dz = pos[i * 3 + 2] - pos[j * 3 + 2];
          const dist = dx * dx + dy * dy + dz * dz;
          if (dist < 5) {
            lpos[lineIdx++] = pos[i * 3]; lpos[lineIdx++] = pos[i * 3 + 1]; lpos[lineIdx++] = pos[i * 3 + 2];
            lpos[lineIdx++] = pos[j * 3]; lpos[lineIdx++] = pos[j * 3 + 1]; lpos[lineIdx++] = pos[j * 3 + 2];
          }
        }
      }
      lineGeo.setDrawRange(0, lineIdx / 3);
      lineGeo.attributes.position.needsUpdate = true;

      camera.position.x += (mouseX * 0.5 - camera.position.x) * 0.02;
      camera.position.y += (-mouseY * 0.5 - camera.position.y) * 0.02;
      camera.lookAt(0, 0, 0);
      points.rotation.y += 0.001;
      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => {
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };
    window.addEventListener('resize', onResize);

    // Hero GSAP animations removed to prevent invisible elements on load.

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('resize', onResize);
      if (mount.contains(renderer.domElement)) mount.removeChild(renderer.domElement);
      geometry.dispose(); material.dispose(); lineGeo.dispose(); lineMat.dispose();
      renderer.dispose();
    };
  }, []);

  return (
    <section ref={heroRef} className="relative min-h-screen flex flex-col items-center justify-center pt-28 pb-12 px-4 sm:px-6 overflow-hidden">
      {/* Three.js canvas layer */}
      <div ref={mountRef} className="absolute inset-0 z-0" />
      {/* Grid overlay */}
      <div className="absolute inset-0 cyber-grid z-[1]" />
      {/* Radial gradient vignette */}
      <div className="absolute inset-0 z-[2]" style={{ background: 'radial-gradient(ellipse at center, transparent 30%, #0a0a0f 75%)' }} />
      {/* Scanlines overlay */}
      <div className="absolute inset-0 pointer-events-none z-[3]" style={{ background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,60,0,0.015) 2px, rgba(255,60,0,0.015) 4px)' }} />
      {/* Halftone dots overlay */}
      <div className="absolute inset-0 pointer-events-none z-[4] halftone-overlay" />

      {/* Content */}
      <div className="relative text-center max-w-5xl z-10">
        {/* Badge */}
        <div className="hero-badge inline-flex items-center gap-2 px-5 py-2 border-3 border-ds-red/50 bg-ds-red/10 mb-8 backdrop-blur-sm">
          <span className="w-2 h-2 bg-ds-red rounded-full animate-pulse" />
          <span className="text-xs font-mono text-white uppercase tracking-widest font-bold">
            DeepScan — AI Deepfake Detection
          </span>
          <span className="w-2 h-2 bg-ds-red rounded-full animate-pulse" />
        </div>

        {/* ═══ SPIDER-VERSE TITLE ═══ */}
        <div className="hero-title-wrapper relative">
          {/* Shadow layers for depth - Spider-Verse multi-layer style */}
          <h1
            aria-hidden="true"
            className="absolute inset-0 text-6xl sm:text-8xl md:text-9xl font-grotesk font-black leading-[0.85] tracking-tight select-none pointer-events-none spiderverse-shadow-layer"
            style={{
              transform: glitchActive ? 'translate(4px, -3px)' : 'translate(3px, 2px)',
              color: 'transparent',
              WebkitTextStroke: '2px rgba(0,245,255,0.3)',
              transition: glitchActive ? 'none' : 'transform 0.3s ease',
            }}
          >
            <span>DEEP</span>
            <span>[</span>
            <span>SCAN</span>
            <span>]</span>
          </h1>
          <h1
            aria-hidden="true"
            className="absolute inset-0 text-6xl sm:text-8xl md:text-9xl font-grotesk font-black leading-[0.85] tracking-tight select-none pointer-events-none"
            style={{
              transform: glitchActive ? 'translate(-3px, 2px)' : 'translate(-2px, -1px)',
              color: 'transparent',
              WebkitTextStroke: '2px rgba(255,60,0,0.25)',
              transition: glitchActive ? 'none' : 'transform 0.3s ease',
            }}
          >
            <span>DEEP</span>
            <span>[</span>
            <span>SCAN</span>
            <span>]</span>
          </h1>
          {/* Main title */}
          <h1 className={`relative text-6xl sm:text-8xl md:text-9xl font-grotesk font-black leading-[0.85] tracking-tight ${glitchActive ? 'spiderverse-glitch-active' : ''}`}>
            <span className="text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.8)]">DEEP</span>
            <span className="text-ds-red neon-red">[</span>
            <span className="text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.8)]">SCAN</span>
            <span className="text-ds-red neon-red">]</span>
          </h1>
        </div>

        {/* Subtitle with stipple effect */}
        <p className="hero-subtitle mt-6 text-base md:text-xl font-mono text-white tracking-wider relative font-bold drop-shadow-md">
          <span className="relative z-10">India's First Multi-Modal AI Deepfake Detection Engine</span>
        </p>

        {/* Terminal */}
        <div className="hero-terminal mt-8 inline-block bg-ds-card/90 backdrop-blur-sm border-2 border-ds-silver/60 px-6 py-3 brutal-shadow relative overflow-hidden">
          {/* Scanline inside terminal */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            <div className="absolute w-full h-[2px] bg-ds-cyan/10 animate-terminal-scan" />
          </div>
          <div className="flex items-center gap-2 mb-1 text-left">
            <span className="w-3 h-3 rounded-full bg-ds-red" />
            <span className="w-3 h-3 rounded-full bg-ds-yellow" />
            <span className="text-[10px] font-mono text-[#00f5ff] font-bold ml-2">deepscan@terminal</span>
          </div>
          <div className="text-left text-white drop-shadow-[0_0_5px_rgba(255,255,255,0.5)]">
            <span className="text-ds-green font-mono text-xs font-bold">$</span>{' '}
            <TerminalText
              text="Scanning with 8 AI engines + rPPG heartbeat analysis + CDCF fusion..."
              speed={22}
              onComplete={() => setShowStats(true)}
            />
          </div>
        </div>

        {/* Stats */}
        <AnimatePresence>
          {showStats && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
              className="mt-10 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto"
            >
              {STATS.map((s, i) => (
                <motion.div
                  key={i}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.4, delay: i * 0.1, ease: 'backOut' }}
                  className="text-center p-4 border-2 border-ds-silver/50 bg-ds-card/90 backdrop-blur-sm card-hover-lift"
                >
                  <s.icon className="w-5 h-5 mx-auto mb-2" style={{ color: s.color }} />
                  <p className="text-2xl md:text-3xl font-grotesk font-black" style={{ color: s.color }}>{s.value}</p>
                  <p className="text-[10px] font-mono text-white mt-1 font-bold">{s.label}</p>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* CTA */}
        <div className="hero-cta mt-12 flex flex-col sm:flex-row gap-4 justify-center">
          <BrutalButton as={Link} to="/analyze" size="lg">
            <Shield className="w-5 h-5" /> Scan Media Now
          </BrutalButton>
          <BrutalButton as={Link} to="/learn" variant="secondary" size="lg">
            <ArrowRight className="w-5 h-5" /> How It Works
          </BrutalButton>
        </div>

        <div className="mt-16 animate-bounce">
          <ChevronDown className="w-6 h-6 text-ds-silver mx-auto" />
        </div>
      </div>
    </section>
  );
}


/* ═══════════════════════════════════════════════════════════════════════
   TABLET SCAN ANIMATION — Lives inside the ContainerScroll "tablet"
   Shows a realistic deepfake scanning interface
   ═══════════════════════════════════════════════════════════════════════ */
function TabletScanAnimation() {
  const [step, setStep] = useState(0);
  const [scanLine, setScanLine] = useState(0);
  const [findings, setFindings] = useState([]);
  const [score, setScore] = useState(0);

  useEffect(() => {
    // Auto-advance through scanning steps
    const timer = setInterval(() => {
      setStep((prev) => {
        if (prev >= SCAN_STEPS.length - 1) {
          clearInterval(timer);
          return prev;
        }
        return prev + 1;
      });
    }, 1800);
    return () => clearInterval(timer);
  }, []);

  // Scan line animation
  useEffect(() => {
    const interval = setInterval(() => {
      setScanLine((p) => (p >= 100 ? 0 : p + 0.8));
    }, 30);
    return () => clearInterval(interval);
  }, []);

  // Add findings progressively
  useEffect(() => {
    const allFindings = [
      { text: 'Lip-sync offset: 4 frames detected', severity: 'high', engine: 'VIDEO', delay: 3000 },
      { text: 'Synthetic voice: 92% TTS probability', severity: 'high', engine: 'AUDIO', delay: 5400 },
      { text: 'ELA anomaly in cheek/jawline region', severity: 'high', engine: 'IMAGE', delay: 7000 },
      { text: 'EXIF: created with model_v3.safetensors', severity: 'medium', engine: 'META', delay: 9000 },
      { text: 'rPPG: NO heartbeat signal detected', severity: 'critical', engine: 'rPPG', delay: 10800 },
      { text: 'FFT: unnatural frequency patterns', severity: 'medium', engine: 'FREQ', delay: 12600 },
    ];
    const timers = allFindings.map((f) =>
      setTimeout(() => setFindings((prev) => [...prev, f]), f.delay)
    );
    return () => timers.forEach(clearTimeout);
  }, []);

  // Animate score
  useEffect(() => {
    const targetScore = SCAN_STEPS[step]?.progress || 0;
    const mapped = step >= SCAN_STEPS.length - 2 ? 89.3 : 0;
    if (step >= SCAN_STEPS.length - 2) {
      let current = score;
      const interval = setInterval(() => {
        current += 1.2;
        if (current >= 89.3) {
          current = 89.3;
          clearInterval(interval);
        }
        setScore(current);
      }, 25);
      return () => clearInterval(interval);
    }
  }, [step]);

  const progress = SCAN_STEPS[step]?.progress || 0;
  const isComplete = step >= SCAN_STEPS.length - 1;
  const sevColors = { critical: '#ff3c00', high: '#ff3c00', medium: '#ffd700', low: '#00f5ff' };

  return (
    <div className="h-full w-full bg-ds-bg text-ds-silver font-mono text-xs p-3 md:p-6 flex flex-col gap-3 relative overflow-hidden">
      {/* Scanning line */}
      {!isComplete && (
        <div
          className="absolute left-0 w-full h-[2px] z-20 pointer-events-none"
          style={{
            top: `${scanLine}%`,
            background: 'linear-gradient(90deg, transparent, #00f5ff, #00f5ff, transparent)',
            boxShadow: '0 0 15px #00f5ff, 0 0 30px #00f5ff40',
          }}
        />
      )}

      {/* Header bar */}
      <div className="flex items-center gap-3 pb-2 border-b border-ds-silver/10">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-[#ff3c00]" />
          <span className="font-grotesk font-black text-sm text-white drop-shadow-md tracking-widest">DEEP[SCAN] Analysis</span>
        </div>
        <div className="ml-auto flex items-center gap-2 text-white font-bold">
          <span className={`w-2 h-2 rounded-full ${isComplete ? 'bg-[#ff3c00]' : 'bg-[#39ff14] animate-pulse'}`} />
          <span className="text-[10px] drop-shadow-sm">{isComplete ? 'SCAN COMPLETE' : 'SCANNING...'}</span>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-3 min-h-0">
        {/* Left: Media preview + scan overlay */}
        <div className="relative border border-ds-silver/10 bg-ds-card overflow-hidden">
          {/* Simulated face image with scan effect */}
          <div className="w-full h-full min-h-[120px] relative bg-gradient-to-br from-ds-card via-ds-bg to-ds-card">
            {/* Face silhouette */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="relative">
                <ScanFace className="w-20 h-20 md:w-28 md:h-28 text-ds-silver" />
                {/* Scanning ROI boxes */}
                <motion.div
                  animate={{ opacity: [0.3, 0.8, 0.3] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="absolute top-[15%] left-[20%] w-[30%] h-[25%] border border-ds-red/60"
                />
                <motion.div
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
                  className="absolute top-[45%] left-[15%] w-[70%] h-[20%] border border-ds-cyan/60"
                />
                <motion.div
                  animate={{ opacity: [0.2, 0.7, 0.2] }}
                  transition={{ duration: 1.8, repeat: Infinity, delay: 1 }}
                  className="absolute top-[25%] left-[50%] w-[25%] h-[30%] border border-ds-yellow/60"
                />
              </div>
            </div>
            {/* ELA heatmap spots */}
            {step > 3 && (
              <>
                <div className="absolute w-12 h-8 rounded-full animate-pulse" style={{ top: '30%', left: '25%', background: 'radial-gradient(circle, rgba(255,60,0,0.4), transparent)' }} />
                <div className="absolute w-8 h-6 rounded-full animate-pulse" style={{ top: '50%', left: '55%', background: 'radial-gradient(circle, rgba(255,60,0,0.3), transparent)', animationDelay: '0.5s' }} />
              </>
            )}
          </div>
          <div className="absolute bottom-0 left-0 right-0 bg-ds-bg/80 backdrop-blur-sm px-2 py-1">
            <span className="text-[9px] text-white">suspect_video_frame_047.mp4</span>
          </div>
        </div>

        {/* Middle: Live findings feed */}
        <div className="border border-ds-silver/10 bg-ds-card p-3 overflow-y-auto space-y-1.5">
          <p className="text-[10px] text-ds-cyan uppercase tracking-wider mb-2">Live Findings</p>
          <AnimatePresence>
            {findings.map((f, i) => (
              <motion.div
                key={i}
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ duration: 0.3 }}
                className="flex items-start gap-2 p-1.5 bg-ds-bg/50 border-l-2"
                style={{ borderColor: sevColors[f.severity] || '#e0e0e0' }}
              >
                <div className="w-1.5 h-1.5 rounded-full mt-1 flex-shrink-0" style={{ background: sevColors[f.severity] }} />
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] text-white font-bold leading-tight truncate drop-shadow-sm">{f.text}</p>
                </div>
                <span className="text-[8px] px-1 py-0.5 border flex-shrink-0" style={{ borderColor: sevColors[f.severity], color: sevColors[f.severity] }}>
                  {f.engine}
                </span>
              </motion.div>
            ))}
          </AnimatePresence>
          {findings.length === 0 && (
            <div className="flex items-center gap-2 text-ds-silver">
              <div className="w-3 h-3 border-2 border-ds-cyan border-t-transparent rounded-full animate-spin" />
              <span className="text-[10px]">Analyzing media...</span>
            </div>
          )}
        </div>

        {/* Right: Score + sub-scores */}
        <div className="border border-ds-silver/10 bg-ds-card p-3 flex flex-col gap-2">
          {/* Score gauge */}
          <div className="flex-shrink-0 flex items-center justify-center py-2">
            <div className="relative">
              <svg width="90" height="90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#1a1a2e" strokeWidth="6" />
                <circle
                  cx="50" cy="50" r="40" fill="none"
                  stroke={score > 70 ? '#ff3c00' : score > 40 ? '#ffd700' : '#39ff14'}
                  strokeWidth="6" strokeLinecap="round"
                  strokeDasharray={2 * Math.PI * 40}
                  strokeDashoffset={2 * Math.PI * 40 * (1 - score / 100)}
                  transform="rotate(-90 50 50)"
                  style={{ transition: 'all 0.3s ease' }}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-lg font-grotesk font-black" style={{ color: score > 70 ? '#ff3c00' : '#ffd700' }}>
                  {score > 0 ? score.toFixed(1) : '—'}
                </span>
                <span className="text-[8px] text-ds-silver">AACS</span>
              </div>
            </div>
          </div>

          {/* Sub-scores */}
          <div className="space-y-1.5 flex-1">
            <p className="text-[10px] text-ds-green uppercase tracking-wider">Sub-Scores</p>
            {[
              { label: 'MAS', val: step > 1 ? 87 : 0, color: '#ff3c00' },
              { label: 'PPS', val: step > 4 ? 92 : 0, color: '#39ff14' },
              { label: 'IRS', val: step > 6 ? 84 : 0, color: '#00f5ff' },
              { label: 'AAS', val: step > 5 ? 91 : 0, color: '#ffd700' },
              { label: 'CVS', val: step > 7 ? 76 : 0, color: '#e0e0e0' },
            ].map((s) => (
              <div key={s.label} className="flex items-center gap-1.5">
                <span className="text-[9px] w-6 font-bold" style={{ color: s.color }}>{s.label}</span>
                <div className="flex-1 h-1.5 bg-ds-bg border border-ds-silver/10 overflow-hidden">
                  <motion.div
                    animate={{ width: `${s.val}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                    className="h-full"
                    style={{ background: s.color }}
                  />
                </div>
                <span className="text-[9px] w-7 text-right" style={{ color: s.val > 0 ? s.color : '#333' }}>
                  {s.val > 0 ? `${s.val}%` : '—'}
                </span>
              </div>
            ))}
          </div>

          {/* Verdict */}
          {isComplete && (
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="mt-1 p-2 border-2 border-ds-red bg-ds-red/10 text-center"
            >
              <span className="text-[10px] font-bold text-ds-red">DEFINITELY FAKE</span>
            </motion.div>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="mt-auto space-y-1">
        <div className="flex justify-between text-[9px] text-ds-silver">
          <span>{SCAN_STEPS[step]?.label || 'Complete'}</span>
          <span>{progress}%</span>
        </div>
        <div className="h-2 border border-ds-silver/20 overflow-hidden">
          <motion.div
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className="h-full bg-gradient-to-r from-ds-red via-ds-yellow to-ds-green"
          />
        </div>
      </div>
    </div>
  );
}


/* ═══ HEARTBEAT SVG VISUAL ═══ */
function HeartbeatVisual() {
  const svgRef = useRef(null);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const path = svg.querySelector('.real-line');
    if (path) {
      const length = path.getTotalLength();
      gsap.set(path, { strokeDasharray: length, strokeDashoffset: length });
      gsap.to(path, { strokeDashoffset: 0, duration: 2, ease: 'power2.inOut', repeat: -1, yoyo: true });
    }
  }, []);

  const realPath = 'M0,50 L20,50 L25,50 L28,20 L31,70 L34,40 L37,55 L40,50 L60,50 L65,50 L68,15 L71,75 L74,35 L77,58 L80,50 L100,50 L105,50 L108,10 L111,80 L114,30 L117,55 L120,50 L140,50 L160,50 L165,50 L168,18 L171,72 L174,38 L177,55 L180,50 L200,50';
  const fakePath = 'M0,50 L40,50 L80,50 L120,50 L160,50 L200,50';

  return (
    <div className="p-6 border-3 border-ds-silver/20 bg-ds-card space-y-6">
      <div>
        <p className="text-xs font-mono text-ds-green mb-2 flex items-center gap-2">
          <span className="w-2 h-2 bg-ds-green rounded-full animate-pulse" />
          REAL FACE — 72 BPM
        </p>
        <svg ref={svgRef} viewBox="0 0 200 100" className="w-full h-16">
          <path className="real-line" d={realPath} fill="none" stroke="#39ff14" strokeWidth="2.5" />
        </svg>
      </div>
      <div className="h-px bg-ds-silver/10" />
      <div>
        <p className="text-xs font-mono text-ds-red mb-2 flex items-center gap-2">
          <span className="w-2 h-2 bg-ds-red rounded-full" />
          DEEPFAKE — FLATLINE
        </p>
        <svg viewBox="0 0 200 100" className="w-full h-16">
          <path d={fakePath} fill="none" stroke="#ff3c00" strokeWidth="2.5" strokeDasharray="4,4" />
        </svg>
      </div>
    </div>
  );
}
