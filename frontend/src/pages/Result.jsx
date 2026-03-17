import React, { useRef, useEffect } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Loader, AlertCircle } from 'lucide-react';
import gsap from 'gsap';
import { getResult } from '../api/deepscan';
import { VERDICT_CONFIG } from '../utils/constants';
import { formatScore, formatDateTime, getScoreColor } from '../utils/formatters';

import BrutalCard from '../components/ui/BrutalCard';
import BrutalBadge from '../components/ui/BrutalBadge';
import BrutalButton from '../components/ui/BrutalButton';
import TrustScoreGauge from '../components/analysis/TrustScoreGauge';
import KeyFindings from '../components/analysis/KeyFindings';
import CdcfPanel from '../components/analysis/CdcfPanel';
import ForensicsViewer from '../components/analysis/ForensicsViewer';
import SubScoreGrid from '../components/analysis/SubScoreGrid';
import NarrativeExplanation from '../components/analysis/NarrativeExplanation';
import HeartbeatChart from '../components/analysis/HeartbeatChart';
import GradCamOverlay from '../components/analysis/GradCamOverlay';
import AudioSpectrum from '../components/analysis/AudioSpectrum';
import TrajectoryPlot from '../components/analysis/TrajectoryPlot';
import GrokNLMAnalysis from '../components/analysis/GrokNLMAnalysis';
import DetectionBreakdown from '../components/analysis/DetectionBreakdown';
import VideoDescription from '../components/analysis/VideoDescription';
import ShareVerdict from '../components/accessibility/ShareVerdict';
import DownloadReport from '../components/accessibility/DownloadReport';
import ElaHeatmapViewer from '../components/analysis/ElaHeatmapViewer';

export default function Result() {
  const { id } = useParams();
  const location = useLocation();
  const originalFile = location.state?.originalFile || null;
  const resultRef = useRef(null);

  const { data: result, isLoading, error } = useQuery({
    queryKey: ['result', id],
    queryFn: () => getResult(id),
    retry: 1,
  });

  // GSAP staggered entry animation — runs whenever result changes
  useEffect(() => {
    if (!resultRef.current || !result) return;
    const ctx = gsap.context(() => {
      gsap.from('.result-section', {
        y: 40,
        opacity: 0,
        duration: 0.6,
        stagger: 0.12,
        ease: 'power2.out',
      });
      gsap.from('.score-display', {
        scale: 0.5,
        opacity: 0,
        duration: 0.8,
        ease: 'back.out(1.7)',
        delay: 0.2,
      });
    }, resultRef);
    return () => ctx.revert();
  }, [result]);

  // ─── Loading state ───
  if (isLoading) {
    return (
      <div className="min-h-screen bg-ds-bg flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-10 h-10 text-ds-red animate-spin mx-auto mb-4" />
          <p className="font-mono text-sm text-ds-silver/50">Loading result...</p>
        </div>
      </div>
    );
  }

  // ─── Error state ───
  if (error || !result) {
    return (
      <div className="min-h-screen bg-ds-bg flex items-center justify-center px-4">
        <BrutalCard className="max-w-md text-center">
          <AlertCircle className="w-10 h-10 text-ds-red mx-auto mb-4" />
          <h2 className="font-grotesk font-bold text-xl text-ds-silver mb-2">Result Not Found</h2>
          <p className="text-sm font-mono text-ds-silver/50 mb-4">
            {error?.message || 'The analysis result could not be loaded.'}
          </p>
          <BrutalButton as={Link} to="/analyze" variant="secondary">
            Try Another Scan
          </BrutalButton>
        </BrutalCard>
      </div>
    );
  }

  const verdict = VERDICT_CONFIG[result.verdict] || VERDICT_CONFIG.UNCERTAIN;
  const score = result.score ?? result.aacs_score ?? 0;

  return (
    <div ref={resultRef} className="relative min-h-screen bg-ds-bg pt-24 pb-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Back link */}
        <Link
          to="/analyze"
          className="inline-flex items-center gap-2 text-sm font-mono text-ds-silver/50 hover:text-ds-silver transition-colors result-section"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Analyze
        </Link>

        {/* Top row — Score + Verdict */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 result-section">
          {/* Score Gauge */}
          <BrutalCard className="flex flex-col items-center justify-center lg:col-span-1 score-display">
            <TrustScoreGauge score={score} size={typeof window !== 'undefined' && window.innerWidth < 640 ? 160 : 220} />
            <div className="mt-4 text-center">
              <span className="px-3 py-1 text-white rounded font-mono font-bold text-xs uppercase tracking-widest" style={{ background: score >= 70 ? 'rgb(255, 68, 34)' : score >= 40 ? '#ffd700' : '#39ff14', color: score >= 40 && score < 70 ? '#000' : '#fff' }}>
                {verdict.emoji} {verdict.label} — {formatScore(score)}
              </span>
            </div>
          </BrutalCard>

          {/* Details */}
          <BrutalCard className="lg:col-span-2 space-y-4">
            <div className="flex items-start justify-between flex-wrap gap-2">
              <div>
                <h1 className="font-grotesk font-black text-xl sm:text-2xl text-ds-silver">
                  Analysis Result
                </h1>
                <p className="text-xs font-mono text-ds-silver/40 mt-1">
                  ID: {result.id || id} &bull; {formatDateTime(result.created_at)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <DownloadReport resultId={result.id || id} />
              </div>
            </div>

            {/* File info */}
            {result.filename && (
              <div className="flex items-center gap-4 p-3 bg-ds-bg border border-ds-silver/20">
                <div className="text-xs font-mono text-ds-silver/50 space-y-1">
                  <p>File: <span className="text-ds-silver">{result.filename}</span></p>
                  {result.file_type && <p>Type: <span className="text-ds-silver">{result.file_type}</span></p>}
                  {result.processing_time_ms && (
                    <p>Processing: <span className="text-ds-silver">{(result.processing_time_ms / 1000).toFixed(1)}s</span></p>
                  )}
                </div>
              </div>
            )}

            {/* Share */}
            <ShareVerdict verdict={verdict.label} score={score} resultId={result.id || id} />

            {/* Quick score */}
            <div className="flex items-center gap-4 pt-2">
              <span className="px-4 py-2 text-white rounded font-mono font-bold text-lg border-2 border-white/10 shadow-lg" style={{ background: score >= 70 ? 'rgb(255, 68, 34)' : score >= 40 ? '#ffd700' : '#39ff14', color: score >= 40 && score < 70 ? '#000' : '#fff' }}>
                {formatScore(score)}
              </span>
              <span className="text-xs sm:text-sm font-mono text-ds-silver/40 uppercase tracking-widest font-black">AACS Score</span>
            </div>
          </BrutalCard>
        </div>

        {/* --- Image Advanced Analysis Block --- */}
        {result.file_type && result.file_type.includes('image') && result.forensics?.ela && (
          <div className="result-section w-full">
            <ElaHeatmapViewer
              elaData={result.forensics.ela}
              imageFile={originalFile}
              systemScore={score}
              systemVerdict={verdict}
            />
          </div>
        )}

        {/* --- AI Video Content Description --- */}
        {result.ltca_data?.video_description && (
          <div className="result-section">
            <VideoDescription videoDescription={result.ltca_data.video_description} />
          </div>
        )}

        {/* --- Deep NLM Forensic Analysis --- */}
        {result.ltca_data && result.ltca_data.nlm_report && (
          <div className="result-section">
            <BrutalCard className="!p-3 sm:!p-6 bg-ds-silver/5 border-l-4 sm:border-l-8 border-l-ds-cyan">
              <h3 className="font-grotesk font-black text-ds-silver text-base sm:text-xl uppercase tracking-wider sm:tracking-widest mb-3 sm:mb-4 flex items-center gap-2">
                <span className="text-ds-cyan">[NLM]</span> Deep Expert Analysis
              </h3>
              <div className="font-mono text-sm text-ds-silver/80 leading-relaxed space-y-4">
                {result.ltca_data.nlm_report.split('\n\n').map((paragraph, i) => (
                  <p key={i}>{paragraph}</p>
                ))}
              </div>
            </BrutalCard>
          </div>
        )}

        {/* --- Secondary Metrics Grid --- */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 result-section items-start">
          <div className="space-y-6 w-full flex flex-col">
            {/* Key Findings */}
            {result.findings?.length > 0 && <KeyFindings findings={result.findings} />}
            {/* Sub-Scores */}
            {result.sub_scores && <SubScoreGrid subScores={result.sub_scores} />}
            <CdcfPanel cdcf={result.cdcf} />
          </div>
          <div className="space-y-6 w-full flex flex-col">
            {/* Detection Engine Breakdown — all 9 engines with score bars */}
            {(result.findings?.length > 0 || result.ltca_data) && (
              <DetectionBreakdown
                findings={result.findings || []}
                ltcaData={result.ltca_data || {}}
              />
            )}
            <NarrativeExplanation narrative={result.narrative} />
          </div>
        </div>

        {/* --- Audio / Video Specific Blocks --- */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 result-section">
          {result.heartbeat && <HeartbeatChart heartbeatData={result.heartbeat} />}
          {result.audio && <AudioSpectrum audioData={result.audio} />}
          {result.ltca_data && result.ltca_data.trajectory_plot && result.ltca_data.trajectory_plot.length > 0 && (
            <div className="lg:col-span-2">
              <TrajectoryPlot trajectoryData={result.ltca_data.trajectory_plot} />
            </div>
          )}
        </div>

        {/* --- Raw Forensic Data (Collapsible) --- */}
        {(result.forensics || result.gradcam) && (
          <div className="result-section mt-8">
            <details className="group [&_summary::-webkit-details-marker]:hidden border-2 border-ds-silver/20 hover:border-ds-red transition-all">
              <summary className="flex items-center justify-between cursor-pointer p-4 bg-[#111] outline-none font-mono text-xs uppercase tracking-widest text-ds-silver/70 hover:text-ds-silver">
                <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-ds-silver/40 group-open:bg-ds-red transition-colors" />View Raw Backend Forensics</span>
                <span className="transition duration-300 group-open:rotate-180">▼</span>
              </summary>
              <div className="p-4 border-t-2 border-ds-silver/20 bg-[#0a0a0f] space-y-6">
                {result.forensics && <ForensicsViewer forensics={result.forensics} />}
                {result.gradcam && <GradCamOverlay gradcam={result.gradcam} />}
              </div>
            </details>
          </div>
        )}

        {/* Bottom CTA */}
        <div className="text-center pt-8 result-section">
          <BrutalButton as={Link} to="/analyze" size="lg">
            Scan Another File
          </BrutalButton>
        </div>
      </div>
    </div>
  );
}
