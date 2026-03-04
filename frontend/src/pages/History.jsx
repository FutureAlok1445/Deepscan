import React, { useState, useLayoutEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Clock, Search, Filter, Trash2, ExternalLink } from 'lucide-react';
import gsap from 'gsap';
import { getHistory } from '../api/deepscan';
import { formatScore, formatDateTime, getScoreColor, truncateFilename } from '../utils/formatters';
import { VERDICT_CONFIG } from '../utils/constants';
import BrutalCard from '../components/ui/BrutalCard';
import BrutalBadge from '../components/ui/BrutalBadge';
import BrutalButton from '../components/ui/BrutalButton';

const FILTERS = ['all', 'image', 'video', 'audio'];

export default function History() {
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const pageRef = useRef(null);

  const { data: history = [], isLoading } = useQuery({
    queryKey: ['history'],
    queryFn: getHistory,
  });

  const filtered = history.filter((item) => {
    if (filter !== 'all' && !item.file_type?.startsWith(filter)) return false;
    if (search && !item.filename?.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  useLayoutEffect(() => {
    if (isLoading) return;
    const ctx = gsap.context(() => {
      gsap.from('.hist-header', { y: -30, opacity: 0, duration: 0.6, ease: 'power3.out' });
      gsap.from('.hist-filters', { y: 20, opacity: 0, duration: 0.5, delay: 0.15, ease: 'power3.out' });
      if (filtered.length > 0) {
        gsap.from('.hist-item', { y: 30, opacity: 0, stagger: 0.08, duration: 0.5, delay: 0.3, ease: 'power2.out' });
      }
    }, pageRef);
    return () => ctx.revert();
  }, [filtered.length, isLoading]);

  return (
    <div ref={pageRef} className="min-h-screen bg-ds-bg pt-24 pb-16 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Floating background particles */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {[...Array(12)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 rounded-full bg-ds-cyan/20 animate-pulse"
            style={{
              left: `${8 + i * 8}%`,
              top: `${10 + (i * 17) % 80}%`,
              animationDelay: `${i * 0.3}s`,
              animationDuration: `${2 + (i % 3)}s`,
            }}
          />
        ))}
      </div>

      <div className="max-w-4xl mx-auto space-y-8 relative z-10">
        {/* Header */}
        <div className="text-center hist-header">
          <p className="text-xs font-mono text-ds-cyan uppercase tracking-[0.3em] mb-2">
            // HISTORY
          </p>
          <h1 className="text-3xl md:text-4xl font-grotesk font-black text-ds-silver">
            Past <span className="text-ds-cyan">Scans</span>
          </h1>
          <p className="mt-2 text-sm font-mono text-ds-silver/50">
            Review your previous analysis results
          </p>
        </div>

        {/* Filters */}
        <div className="hist-filters flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex gap-2">
            {FILTERS.map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 text-xs font-mono uppercase tracking-wider border-2 transition-colors ${
                  filter === f
                    ? 'text-ds-cyan border-ds-cyan bg-ds-cyan/10'
                    : 'text-ds-silver/40 border-ds-silver/20 hover:border-ds-silver/50'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 border-2 border-ds-silver/30 px-3 py-2 w-full sm:w-auto">
            <Search className="w-4 h-4 text-ds-silver/40" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search filename..."
              className="bg-transparent text-sm font-mono text-ds-silver placeholder:text-ds-silver/20 focus:outline-none w-full sm:w-48"
            />
          </div>
        </div>

        {/* Results */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="w-8 h-8 border-3 border-ds-cyan border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="mt-4 text-sm font-mono text-ds-silver/50">Loading history...</p>
          </div>
        ) : filtered.length === 0 ? (
          <BrutalCard className="text-center py-12">
            <Clock className="w-10 h-10 text-ds-silver/20 mx-auto mb-4" />
            <p className="font-grotesk font-bold text-lg text-ds-silver mb-2">No Scans Found</p>
            <p className="text-sm font-mono text-ds-silver/40 mb-4">
              {search ? 'No results match your search' : 'Start by analyzing some media'}
            </p>
            <BrutalButton as={Link} to="/analyze" variant="secondary" size="sm">
              Start Scanning
            </BrutalButton>
          </BrutalCard>
        ) : (
          <div className="space-y-3">
            {filtered.map((item) => {
              const verdict = VERDICT_CONFIG[item.verdict] || VERDICT_CONFIG.UNCERTAIN;
              return (
                <Link
                  key={item.id}
                  to={`/result/${item.id}`}
                  className="block group hist-item"
                >
                  <BrutalCard className="flex items-center gap-4 !py-4 group-hover:border-ds-cyan transition-colors">
                    {/* Score */}
                    <div className="w-16 text-center flex-shrink-0">
                      <p className={`text-xl font-grotesk font-black ${getScoreColor(item.score)}`}>
                        {formatScore(item.score)}
                      </p>
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-mono text-sm text-ds-silver truncate">
                          {truncateFilename(item.filename, 36)}
                        </p>
                        <BrutalBadge
                          variant={item.score >= 70 ? 'red' : item.score >= 40 ? 'yellow' : 'green'}
                        >
                          {verdict.label}
                        </BrutalBadge>
                      </div>
                      <p className="text-xs font-mono text-ds-silver/40 mt-1">
                        {formatDateTime(item.created_at)} • {item.file_type || 'unknown'}
                      </p>
                    </div>

                    {/* Arrow */}
                    <ExternalLink className="w-4 h-4 text-ds-silver/20 group-hover:text-ds-cyan flex-shrink-0 transition-colors" />
                  </BrutalCard>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
