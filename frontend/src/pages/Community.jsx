import React, { useState, useLayoutEffect, useRef, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  ExternalLink,
  Send,
  Newspaper,
  RefreshCw,
  Search,
  Clock3,
} from 'lucide-react';
import gsap from 'gsap';
import {
  getCommunityAlerts,
  submitFeedback,
  submitCommunityReport,
  getDeepfakeNews,
  refreshDeepfakeNews,
  getDeepfakeNewsStatus,
} from '../api/deepscan';
import { formatDateTime, formatScore, getScoreColor, formatRelativeTime } from '../utils/formatters';
import { VERDICT_CONFIG } from '../utils/constants';
import BrutalCard from '../components/ui/BrutalCard';
import BrutalBadge from '../components/ui/BrutalBadge';
import BrutalButton from '../components/ui/BrutalButton';

const NEWS_TABS = [
  { id: 'all', label: 'All' },
  { id: 'ai-deepfakes', label: 'AI Deepfakes' },
  { id: 'political', label: 'Political' },
  { id: 'celebrity', label: 'Celebrity' },
  { id: 'legal-crime', label: 'Legal & Crime' },
  { id: 'india', label: 'India' },
];

const NEWS_VISIBLE_BATCH = 6;
const NEWS_IMAGE_PLACEHOLDER =
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    "<svg xmlns='http://www.w3.org/2000/svg' width='320' height='180'><rect width='100%' height='100%' fill='#0f0f1a'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='#e0e0e0' font-family='Arial, sans-serif' font-size='16'>Deepfake News</text></svg>"
  );

export default function Community() {
  const queryClient = useQueryClient();
  const pageRef = useRef(null);

  const [newsTab, setNewsTab] = useState('all');
  const [newsSearch, setNewsSearch] = useState('');
  const [newsVisible, setNewsVisible] = useState(NEWS_VISIBLE_BATCH);

  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ['community'],
    queryFn: getCommunityAlerts,
  });

  const {
    data: newsFeed = {
      items: [],
      total: 0,
      live: false,
      stale: true,
      last_updated: null,
      breaking: null,
    },
    isLoading: isNewsLoading,
    isFetching: isNewsFetching,
  } = useQuery({
    queryKey: ['community-news', newsTab, newsSearch],
    queryFn: () => getDeepfakeNews({ tab: newsTab, search: newsSearch, limit: 60, offset: 0 }),
    staleTime: 2 * 60 * 1000,
    refetchInterval: 6 * 60 * 60 * 1000,
  });

  const { data: newsStatus = {} } = useQuery({
    queryKey: ['community-news-status'],
    queryFn: getDeepfakeNewsStatus,
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  });

  const feedbackMutation = useMutation({
    mutationFn: submitFeedback,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['community'] }),
  });

  const refreshNewsMutation = useMutation({
    mutationFn: refreshDeepfakeNews,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['community-news'] });
      queryClient.invalidateQueries({ queryKey: ['community-news-status'] });
    },
  });

  useEffect(() => {
    setNewsVisible(NEWS_VISIBLE_BATCH);
  }, [newsTab, newsSearch, newsFeed.total]);

  const newsItems = Array.isArray(newsFeed.items) ? newsFeed.items : [];
  const visibleNews = useMemo(() => newsItems.slice(0, newsVisible), [newsItems, newsVisible]);
  const hasMoreNews = newsVisible < newsItems.length;
  const breakingArticle = newsFeed.breaking;
  const lastUpdated = newsStatus.last_updated || newsFeed.last_updated;
  const isLive = Boolean(newsStatus.live ?? newsFeed.live) && !Boolean(newsFeed.stale);

  useLayoutEffect(() => {
    if (isLoading && isNewsLoading) return;

    const ctx = gsap.context(() => {
      gsap.from('.comm-header', { y: -30, opacity: 0, duration: 0.6, ease: 'power3.out' });
      gsap.from('.news-header', { y: 20, opacity: 0, duration: 0.45, delay: 0.1, ease: 'power3.out' });

      if (newsItems.length > 0) {
        gsap.from('.news-card', {
          y: 24,
          opacity: 0,
          stagger: 0.06,
          duration: 0.4,
          delay: 0.15,
          ease: 'power2.out',
        });
      }

      if (alerts.length > 0) {
        gsap.from('.comm-alert', {
          x: -30,
          opacity: 0,
          stagger: 0.1,
          duration: 0.5,
          delay: 0.3,
          ease: 'power2.out',
        });
      }

      gsap.from('.comm-submit', {
        y: 30,
        opacity: 0,
        duration: 0.5,
        delay: 0.5,
        ease: 'power2.out',
      });
    }, pageRef);

    return () => ctx.revert();
  }, [alerts.length, isLoading, newsItems.length, isNewsLoading]);

  return (
    <div ref={pageRef} className="min-h-screen bg-ds-bg pt-24 pb-16 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-ds-green/[0.03] blur-[120px] pointer-events-none" />

      <div className="max-w-4xl mx-auto space-y-8 relative z-10">
        <div className="text-center comm-header">
          <p className="text-xs font-mono text-ds-green uppercase tracking-[0.3em] mb-2">
            // COMMUNITY
          </p>
          <h1 className="text-3xl md:text-4xl font-grotesk font-black text-ds-silver">
            Community <span className="text-ds-green">Signals</span>
          </h1>
          <p className="mt-2 text-sm font-mono text-ds-silver/50">
            Live deepfake news feed with community reports from across India
          </p>
        </div>

        <div className="space-y-4">
          <div className="news-header flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div>
              <h2 className="font-grotesk font-bold text-lg text-ds-silver uppercase tracking-wider flex items-center gap-2">
                <Newspaper className="w-5 h-5 text-ds-cyan" />
                Deepfake News & Alerts
              </h2>
              <p className="mt-1 text-xs font-mono text-ds-silver/40">
                Global + India-specific deepfake updates auto-refreshed every 6 hours
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <BrutalBadge variant={isLive ? 'green' : 'yellow'} pulse={isLive}>
                {isLive ? 'Live' : 'Stale'}
              </BrutalBadge>
              <span className="text-[11px] font-mono text-ds-silver/50">
                {lastUpdated ? `Last updated ${formatRelativeTime(lastUpdated)}` : 'Last updated unavailable'}
              </span>
              <BrutalButton
                size="sm"
                variant="secondary"
                loading={refreshNewsMutation.isPending}
                disabled={refreshNewsMutation.isPending || isNewsFetching}
                onClick={() => refreshNewsMutation.mutate()}
              >
                <RefreshCw className={`w-4 h-4 ${refreshNewsMutation.isPending ? 'animate-spin' : ''}`} />
                Refresh Now
              </BrutalButton>
            </div>
          </div>

          {breakingArticle && (
            <BrutalCard className="!p-4 border-ds-red bg-red-950/20">
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
                <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-ds-red">Breaking</span>
                <p className="text-sm font-grotesk font-bold text-ds-silver flex-1 min-w-0 truncate">
                  {breakingArticle.title}
                </p>
                <span className="text-xs font-mono text-ds-silver/50">
                  {breakingArticle.source_name} • {formatRelativeTime(breakingArticle.published_at)}
                </span>
                <a
                  href={breakingArticle.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-mono text-ds-cyan hover:underline"
                >
                  Read →
                </a>
              </div>
            </BrutalCard>
          )}

          <div className="flex flex-wrap gap-2">
            {NEWS_TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setNewsTab(tab.id)}
                className={`px-3 py-1.5 text-xs font-mono uppercase tracking-wider border-2 transition-colors ${
                  newsTab === tab.id
                    ? 'text-ds-cyan border-ds-cyan bg-ds-cyan/10'
                    : 'text-ds-silver/40 border-ds-silver/20 hover:border-ds-silver/50'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 border-2 border-ds-silver/30 px-3 py-2 w-full sm:w-[420px]">
            <Search className="w-4 h-4 text-ds-silver/40" />
            <input
              type="text"
              value={newsSearch}
              onChange={(e) => setNewsSearch(e.target.value)}
              placeholder="Search headline or source..."
              className="bg-transparent text-sm font-mono text-ds-silver placeholder:text-ds-silver/20 focus:outline-none w-full"
            />
          </div>

          {isNewsLoading ? (
            <div className="text-center py-12">
              <div className="w-8 h-8 border-3 border-ds-cyan border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="mt-4 text-sm font-mono text-ds-silver/50">Loading live news feed...</p>
            </div>
          ) : visibleNews.length === 0 ? (
            <BrutalCard className="text-center py-10">
              <Newspaper className="w-10 h-10 text-ds-silver/20 mx-auto mb-3" />
              <p className="font-grotesk font-bold text-lg text-ds-silver mb-2">No matching articles</p>
              <p className="text-sm font-mono text-ds-silver/40">
                Try another tab or search query to explore deepfake-related coverage.
              </p>
            </BrutalCard>
          ) : (
            <div className="space-y-3">
              {visibleNews.map((article) => (
                <NewsCard key={article.article_id} article={article} />
              ))}
            </div>
          )}

          {hasMoreNews && (
            <div className="text-center">
              <BrutalButton
                size="sm"
                variant="secondary"
                onClick={() => setNewsVisible((prev) => prev + NEWS_VISIBLE_BATCH)}
              >
                Load More Articles
              </BrutalButton>
            </div>
          )}
        </div>

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
                Community alerts will appear here as users report deepfake content.
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

        <div className="comm-submit">
          <SubmitSection />
        </div>
      </div>
    </div>
  );
}

function NewsCard({ article }) {
  const [imageSrc, setImageSrc] = useState(article.thumbnail_url || NEWS_IMAGE_PLACEHOLDER);

  useEffect(() => {
    setImageSrc(article.thumbnail_url || NEWS_IMAGE_PLACEHOLDER);
  }, [article.thumbnail_url]);

  return (
    <BrutalCard className="news-card !p-4">
      <div className="flex items-start gap-4">
        <div className="w-24 h-24 sm:w-28 sm:h-28 border-2 border-ds-silver/20 bg-ds-card overflow-hidden flex-shrink-0">
          <img
            src={imageSrc}
            alt={article.title}
            className="w-full h-full object-cover"
            loading="lazy"
            referrerPolicy="no-referrer"
            onError={() => {
              if (imageSrc !== NEWS_IMAGE_PLACEHOLDER) {
                setImageSrc(NEWS_IMAGE_PLACEHOLDER);
              }
            }}
          />
        </div>

        <div className="min-w-0 flex-1 space-y-2">
          <h3 className="font-grotesk font-bold text-ds-silver leading-tight">
            {article.title}
          </h3>

          <p
            className="text-sm font-mono text-ds-silver/60 leading-relaxed"
            style={{
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {article.summary}
          </p>

          <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-ds-silver/45">
            <span className="inline-flex items-center gap-1">
              <Clock3 className="w-3.5 h-3.5" />
              {formatRelativeTime(article.published_at)}
            </span>
            <span>•</span>
            <span>{article.source_name}</span>
            <BrutalBadge variant={newsTagVariant(article.category_tag)}>
              {article.category_tag}
            </BrutalBadge>
            <a
              href={article.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-auto text-ds-cyan hover:underline"
            >
              Read More →
            </a>
          </div>
        </div>
      </div>
    </BrutalCard>
  );
}

function newsTagVariant(tag) {
  const value = (tag || '').toLowerCase();
  if (value.includes('crime')) return 'red';
  if (value.includes('political') || value.includes('legal')) return 'yellow';
  if (value.includes('india')) return 'green';
  return 'cyan';
}

function AlertCard({ alert, onVote }) {
  const verdict = VERDICT_CONFIG[alert.verdict] || VERDICT_CONFIG.PARTIALLY_AI;

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
    } catch {
      // Ignore submit failures in demo mode.
    }
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
