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
import ArbitrationSystem from '../components/analysis/ArbitrationSystem';
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
              <BrutalBadge
                variant={score >= 70 ? 'red' : score >= 40 ? 'yellow' : 'green'}
                pulse
              >
                {verdict.emoji} {verdict.label}
              </BrutalBadge>
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
            <div className="flex items-center gap-4">
              <span className={`text-3xl sm:text-5xl font-grotesk font-black ${getScoreColor(score)}`}>
                {formatScore(score)}
              </span>
              <span className="text-xs sm:text-sm font-mono text-ds-silver/40">AACS Score</span>
            </div>
          </BrutalCard>
        </div>

        {/* --- Image ELA Heatmap Viewer (JET thermal, reference-quality) --- */}
        {result.file_type && result.file_type.includes('image') && result.forensics?.ela && (
          <div className="result-section">
            <ElaHeatmapViewer
              elaData={result.forensics.ela}
              imageFile={originalFile}
            />
          </div>
        )}

        {/* --- Image Forensics (Arbitration System) --- */}
        {result.file_type && result.file_type.includes('image') && (
          <div className="result-section">
            <ArbitrationSystem
              imageFile={originalFile}
              backendScore={score}
            />
          </div>
        )}

        {/* Key Findings */}
        {result.findings?.length > 0 && (
          <div className="result-section"><KeyFindings findings={result.findings} /></div>
        )}

        {/* Detection Engine Breakdown — all 9 engines with score bars */}
        {(result.findings?.length > 0 || result.ltca_data) && (
          <div className="result-section">
            <DetectionBreakdown
              findings={result.findings || []}
              ltcaData={result.ltca_data || {}}
            />
          </div>
        )}

        {/* AI Video Content Description */}
        {result.ltca_data?.video_description && (
          <div className="result-section">
            <VideoDescription videoDescription={result.ltca_data.video_description} />
          </div>
        )}

        {/* Sub-Scores */}
        {result.sub_scores && (
          <div className="result-section"><SubScoreGrid subScores={result.sub_scores} /></div>
        )}

        {/* Two-column: CDCF + Narrative */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 result-section">
          <CdcfPanel cdcf={result.cdcf} />
          <NarrativeExplanation narrative={result.narrative} />
        </div>

        {/* Forensics */}
        {result.forensics && (
          <div className="result-section"><ForensicsViewer forensics={result.forensics} /></div>
        )}

        {/* Grad-CAM */}
        {result.gradcam && (
          <div className="result-section"><GradCamOverlay gradcam={result.gradcam} /></div>
        )}

        {/* Heartbeat */}
        {result.heartbeat && (
          <div className="result-section"><HeartbeatChart heartbeatData={result.heartbeat} /></div>
        )}

        {/* Audio */}
        {result.audio && (
          <div className="result-section"><AudioSpectrum audioData={result.audio} /></div>
        )}

        {/* Latent Trajectory (Physics Graph) */}
        {result.ltca_data && result.ltca_data.trajectory_plot && result.ltca_data.trajectory_plot.length > 0 && (
          <div className="result-section">
            <TrajectoryPlot trajectoryData={result.ltca_data.trajectory_plot} />
          </div>
        )}

        {/* Deep NLM Forensic Analysis */}
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
