import React, { useState } from 'react';
import { Share2, Copy, Check, Twitter } from 'lucide-react';
import BrutalBadge from '../ui/BrutalBadge';

export default function ShareVerdict({ verdict, score, resultId }) {
  const [copied, setCopied] = useState(false);

  const shareUrl = `${window.location.origin}/result/${resultId || 'demo'}`;
  const shareText = `DeepScan verdict: ${verdict} (${score}% fake probability). Check it out:`;

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(`${shareText}\n${shareUrl}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
      const textarea = document.createElement('textarea');
      textarea.value = `${shareText}\n${shareUrl}`;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const shareTwitter = () => {
    const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const shareWhatsApp = () => {
    const url = `https://wa.me/?text=${encodeURIComponent(`${shareText}\n${shareUrl}`)}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <BrutalBadge variant="silver">
        <Share2 className="w-3 h-3" /> Share
      </BrutalBadge>

      <button
        onClick={copyToClipboard}
        className="flex items-center gap-1 px-2.5 py-1 text-xs font-mono text-ds-silver/70 border border-ds-silver/30 hover:border-ds-silver hover:text-ds-silver transition-colors"
        title="Copy link"
      >
        {copied ? <Check className="w-3 h-3 text-ds-green" /> : <Copy className="w-3 h-3" />}
        {copied ? 'Copied!' : 'Copy'}
      </button>

      <button
        onClick={shareTwitter}
        className="flex items-center gap-1 px-2.5 py-1 text-xs font-mono text-ds-cyan border border-ds-cyan/30 hover:border-ds-cyan hover:bg-ds-cyan/10 transition-colors"
        title="Share on Twitter"
      >
        <Twitter className="w-3 h-3" /> Tweet
      </button>

      <button
        onClick={shareWhatsApp}
        className="flex items-center gap-1 px-2.5 py-1 text-xs font-mono text-ds-green border border-ds-green/30 hover:border-ds-green hover:bg-ds-green/10 transition-colors"
        title="Share on WhatsApp"
      >
        WhatsApp
      </button>
    </div>
  );
}
