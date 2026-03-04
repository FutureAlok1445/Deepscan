import React, { useState, useLayoutEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle, ThumbsUp, ThumbsDown, MessageSquare, TrendingUp, Users, Shield,
  ExternalLink, Send,
} from 'lucide-react';
import gsap from 'gsap';
import { getCommunityAlerts, submitFeedback, submitCommunityReport } from '../api/deepscan';
import { formatDateTime, formatScore, getScoreColor } from '../utils/formatters';
import { VERDICT_CONFIG } from '../utils/constants';
import BrutalCard from '../components/ui/BrutalCard';
import BrutalBadge from '../components/ui/BrutalBadge';
import BrutalButton from '../components/ui/BrutalButton';

/* ─── Fake community stats for demo ─── */
const COMMUNITY_STATS = [
  { icon: Shield, label: 'Total Scans', value: '12,847', color: 'text-ds-red' },
  { icon: AlertTriangle, label: 'Fakes Caught', value: '3,291', color: 'text-ds-yellow' },
  { icon: Users, label: 'Active Users', value: '2,104', color: 'text-ds-cyan' },
  { icon: TrendingUp, label: 'This Week', value: '+342', color: 'text-ds-green' },
];

export default function Community() {
  const queryClient = useQueryClient();
  const pageRef = useRef(null);

  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ['community'],
    queryFn: getCommunityAlerts,
  });

  const feedbackMutation = useMutation({
    mutationFn: submitFeedback,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['community'] }),
  });

  useLayoutEffect(() => {
    if (isLoading) return;
    const ctx = gsap.context(() => {
      gsap.from('.comm-header', { y: -30, opacity: 0, duration: 0.6, ease: 'power3.out' });
      gsap.from('.comm-stat', { scale: 0.8, opacity: 0, stagger: 0.1, duration: 0.5, delay: 0.15, ease: 'back.out(1.5)' });
      if (alerts.length > 0) {
        gsap.from('.comm-alert', { x: -30, opacity: 0, stagger: 0.1, duration: 0.5, delay: 0.3, ease: 'power2.out' });
      }
      gsap.from('.comm-submit', { y: 30, opacity: 0, duration: 0.5, delay: 0.5, ease: 'power2.out' });
    }, pageRef);
    return () => ctx.revert();
  }, [alerts.length, isLoading]);

  return (
    <div ref={pageRef} className="min-h-screen bg-ds-bg pt-24 pb-16 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-ds-green/[0.03] blur-[120px] pointer-events-none" />

      <div className="max-w-4xl mx-auto space-y-8 relative z-10">
        {/* Header */}
        <div className="text-center comm-header">
          <p className="text-xs font-mono text-ds-green uppercase tracking-[0.3em] mb-2">
            // COMMUNITY
          </p>
          <h1 className="text-3xl md:text-4xl font-grotesk font-black text-ds-silver">
            Community <span className="text-ds-green">Alerts</span>
          </h1>
          <p className="mt-2 text-sm font-mono text-ds-silver/50">
            Crowdsourced deepfake alerts from users across India
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {COMMUNITY_STATS.map(({ icon: Icon, label, value, color }, i) => (
            <BrutalCard key={i} hover={false} className="!p-4 text-center comm-stat">
              <Icon className={`w-6 h-6 mx-auto mb-2 ${color}`} />
              <p className={`text-xl font-grotesk font-black ${color}`}>{value}</p>
              <p className="text-xs font-mono text-ds-silver/40 mt-1">{label}</p>
            </BrutalCard>
          ))}
        </div>

        {/* Alert Feed */}
        <div className="space-y-4">
          <h2 className="font-grotesk font-bold text-lg text-ds-silver uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-ds-yellow" />
            Recent Alerts
          </h2>

          {isLoading ? (
            <div className="text-center py-12">
              <div className="w-8 h-8 border-3 border-ds-green border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="mt-4 text-sm font-mono text-ds-silver/50">Loading alerts...</p>
            </div>
          ) : alerts.length === 0 ? (
            <BrutalCard className="text-center py-12">
              <MessageSquare className="w-10 h-10 text-ds-silver/20 mx-auto mb-4" />
              <p className="font-grotesk font-bold text-lg text-ds-silver mb-2">No Alerts Yet</p>
              <p className="text-sm font-mono text-ds-silver/40">
                Community alerts will appear here as users report deepfake content
              </p>
            </BrutalCard>
          ) : (
            alerts.map((alert) => (
              <div key={alert.id} className="comm-alert">
              <AlertCard
                alert={alert}
                onVote={(vote) => feedbackMutation.mutate({ alertId: alert.id, vote })}
              />
              </div>
            ))
          )}
        </div>

        {/* Submit a report */}
        <div className="comm-submit">
          <SubmitSection />
        </div>
      </div>
    </div>
  );
}

function AlertCard({ alert, onVote }) {
  const verdict = VERDICT_CONFIG[alert.verdict] || VERDICT_CONFIG.UNCERTAIN;

  return (
    <BrutalCard className="space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-grotesk font-bold text-ds-silver">
              {alert.title || alert.filename || 'Untitled Alert'}
            </h3>
            <BrutalBadge
              variant={alert.score >= 70 ? 'red' : alert.score >= 40 ? 'yellow' : 'green'}
            >
              {verdict.label}
            </BrutalBadge>
          </div>
          <p className="text-xs font-mono text-ds-silver/40 mt-1">
            {formatDateTime(alert.created_at)} • Reported by {alert.reporter || 'anonymous'}
          </p>
        </div>
        <span className={`text-2xl font-grotesk font-black ${getScoreColor(alert.score)}`}>
          {formatScore(alert.score)}
        </span>
      </div>

      {alert.description && (
        <p className="text-sm font-mono text-ds-silver/60 leading-relaxed">
          {alert.description}
        </p>
      )}

      {alert.tags && (
        <div className="flex flex-wrap gap-1.5">
          {alert.tags.map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider bg-ds-silver/5 text-ds-silver/50 border border-ds-silver/20"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-4 pt-2 border-t border-ds-silver/10">
        <button
          onClick={() => onVote?.('up')}
          className="flex items-center gap-1 text-xs font-mono text-ds-silver/40 hover:text-ds-green transition-colors"
        >
          <ThumbsUp className="w-4 h-4" />
          {alert.upvotes || 0}
        </button>
        <button
          onClick={() => onVote?.('down')}
          className="flex items-center gap-1 text-xs font-mono text-ds-silver/40 hover:text-ds-red transition-colors"
        >
          <ThumbsDown className="w-4 h-4" />
          {alert.downvotes || 0}
        </button>
        {alert.source_url && (
          <a
            href={alert.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs font-mono text-ds-cyan hover:underline ml-auto"
          >
            <ExternalLink className="w-3.5 h-3.5" /> Source
          </a>
        )}
      </div>
    </BrutalCard>
  );
}

function SubmitSection() {
  const [url, setUrl] = useState('');
  const [note, setNote] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await submitCommunityReport(url, note);
    } catch { /* ignore in demo */ }
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 3000);
    setUrl('');
    setNote('');
  };

  return (
    <BrutalCard className="space-y-4">
      <h2 className="font-grotesk font-bold text-lg text-ds-silver uppercase tracking-wider flex items-center gap-2">
        <Send className="w-5 h-5 text-ds-green" />
        Report Suspicious Content
      </h2>

      {submitted ? (
        <div className="p-4 bg-ds-green/10 border-2 border-ds-green text-center">
          <p className="text-sm font-mono text-ds-green">
            Thank you! Your report has been submitted for review.
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-mono text-ds-silver/50 uppercase tracking-wider mb-1">
              URL of suspicious content
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://..."
              required
              className="w-full bg-ds-bg border-2 border-ds-silver/30 px-4 py-2 font-mono text-sm text-ds-silver placeholder:text-ds-silver/20 focus:border-ds-green focus:outline-none transition-colors"
            />
          </div>
          <div>
            <label className="block text-xs font-mono text-ds-silver/50 uppercase tracking-wider mb-1">
              Additional notes (optional)
            </label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Why do you think this is a deepfake?"
              rows={3}
              className="w-full bg-ds-bg border-2 border-ds-silver/30 px-4 py-2 font-mono text-sm text-ds-silver placeholder:text-ds-silver/20 focus:border-ds-green focus:outline-none transition-colors resize-none"
            />
          </div>
          <BrutalButton type="submit" variant="success" size="sm">
            <Send className="w-4 h-4" /> Submit Report
          </BrutalButton>
        </form>
      )}
    </BrutalCard>
  );
}
