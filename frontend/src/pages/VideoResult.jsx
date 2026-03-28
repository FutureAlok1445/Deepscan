import React, { useRef, useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Loader, AlertCircle } from 'lucide-react';
import gsap from 'gsap';
import { getResult } from '../api/deepscan';
import BrutalCard from '../components/ui/BrutalCard';
import BrutalButton from '../components/ui/BrutalButton';
import VideoResultDashboard from '../components/analysis/VideoResultDashboard';

export default function VideoResult() {
  const { id } = useParams();
  const resultRef = useRef(null);

  const { data: result, isLoading, error } = useQuery({
    queryKey: ['result', id],
    queryFn: () => getResult(id),
    retry: 1,
  });

  useEffect(() => {
    if (!resultRef.current || !result) return;
    const ctx = gsap.context(() => {
      gsap.from('.result-section', {
        y: 30,
        opacity: 0,
        duration: 0.5,
        stagger: 0.08,
        ease: 'power2.out',
      });
    }, resultRef);
    return () => ctx.revert();
  }, [result]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-ds-bg flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-10 h-10 text-ds-red animate-spin mx-auto mb-4" />
          <p className="font-mono text-sm text-ds-silver/50">Analyzing video forensics...</p>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="min-h-screen bg-ds-bg flex items-center justify-center px-4">
        <BrutalCard className="max-w-md text-center">
          <AlertCircle className="w-10 h-10 text-ds-red mx-auto mb-4" />
          <h2 className="font-grotesk font-bold text-xl text-ds-silver mb-2">Result Not Found</h2>
          <p className="text-sm font-mono text-ds-silver/50 mb-4">
            {error?.message || 'The video analysis result could not be loaded.'}
          </p>
          <BrutalButton as={Link} to="/analyze" variant="secondary">
            Try Another Scan
          </BrutalButton>
        </BrutalCard>
      </div>
    );
  }

  return (
    <div ref={resultRef} className="relative min-h-screen bg-ds-bg pt-24 pb-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-6">

        {/* ─ Back link ─ */}
        <div className="result-section">
          <Link
            to="/analyze"
            className="inline-flex items-center gap-2 text-sm font-mono text-ds-silver/50 hover:text-ds-silver transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Analyze
          </Link>
        </div>

        {/* ─ Full video forensic dashboard ─ */}
        <div className="result-section">
          <VideoResultDashboard result={result} />
        </div>

        <div className="text-center pt-8 result-section">
          <BrutalButton as={Link} to="/analyze" size="lg">Scan Another File</BrutalButton>
        </div>
      </div>
    </div>
  );
}
