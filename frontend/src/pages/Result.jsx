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
import AnalysisReportGenerator from '../components/analysis/AnalysisReportGenerator';

export default function Result() {
  const { id } = useParams();
  const location = useLocation();
  const originalFile = location.state?.originalFile || null;
  const resultRef = useRef(null);

  const [localElaScore, setLocalElaScore] = React.useState(null);

  const { data: result, isLoading, error } = useQuery({
    queryKey: ['result', id],
    queryFn: () => getResult(id),
    retry: 1,
  });

  console.log("Result.jsx loaded, AACS Score and ContextVerification were removed in the previous version");

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

  const baseVerdict = VERDICT_CONFIG[result.verdict] || VERDICT_CONFIG.UNCERTAIN;
  const baseScore = result.score ?? result.aacs_score ?? 0;

  // Sync with client-side ELA calculation if it's rendered
  const displayScore = localElaScore ? localElaScore.score : baseScore;
  const displayVerdictLabel = localElaScore
    ? (localElaScore.verdict === 'FAKE' ? 'DEFINITELY FAKE' : localElaScore.verdict === 'PARTIAL' ? 'LIKELY AI' : 'AUTHENTIC')
    : baseVerdict.label;

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

        {/* Top row — Verdict Details */}
        <div className="grid grid-cols-1 gap-6 result-section">

          {/* Details */}
          <BrutalCard className="space-y-4">
            <div className="flex items-start justify-between flex-wrap gap-2">
              <div>
                <h1 className="font-grotesk font-black text-xl sm:text-2xl text-ds-silver">
                  Analysis Result
                </h1>
                <p className="text-xs font-mono text-ds-silver/40 mt-1">
                  ID: {result.id || id} &bull; {formatDateTime(result.created_at)}
                </p>
                {localElaScore && (
                  <div className="mt-4 flex items-center gap-2 text-sm font-mono text-ds-silver mb-2 border border-ds-silver/20 p-2 rounded max-w-fit">
                    <span className="font-bold">System Score:</span>
                    <span className="px-2 py-0.5 text-white rounded text-xs uppercase tracking-widest" style={{ background: localElaScore.score > 62 ? '#ff4422' : localElaScore.score > 32 ? '#ffaa00' : '#00cc55' }}>
                      ELA ANOMALY: {localElaScore.score}%
                    </span>
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <DownloadReport resultId={result.id || id} currentScore={displayScore} currentVerdict={displayVerdictLabel} />
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
            <ShareVerdict verdict={displayVerdictLabel} score={displayScore} resultId={result.id || id} />

          </BrutalCard>
        </div>

        {/* --- Image Advanced Analysis Block --- */}
        {result.file_type && result.file_type.includes('image') && result.forensics?.ela && (
          <div className="space-y-6 result-section">
            <ElaHeatmapViewer
              elaData={result.forensics.ela}
              imageFile={originalFile}
              onScoreComputed={setLocalElaScore}
            />
          </div>
        )}

        {/* --- AI Video Content Description --- */}
        {result.ltca_data?.video_description && (
          <div className="result-section">
            <VideoDescription videoDescription={result.ltca_data.video_description} />
          </div>
        )}

        {/* --- Automatically Generated Analysis Report --- */}
        <div className="result-section">
          <AnalysisReportGenerator result={result} sysScore={displayScore} />
        </div>


        {/* --- Secondary Metrics Grid --- */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 result-section items-start">
          <div className="space-y-6 w-full flex flex-col">
            {/* Key Findings */}
            {result.findings?.length > 0 && <KeyFindings findings={result.findings} />}
            {/* Sub-Scores */}
            {result.sub_scores && <SubScoreGrid subScores={result.sub_scores} />}
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
