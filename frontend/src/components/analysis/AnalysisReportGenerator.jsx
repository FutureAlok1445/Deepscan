import React from 'react';
import BrutalCard from '../ui/BrutalCard';
import { FileText } from 'lucide-react';

export default function AnalysisReportGenerator({ result, sysScore }) {
  if (!result) return null;

  const fileType = result.file_type ? result.file_type.replace('image/', 'Image: ').replace('video/', 'Video: ') : 'Unknown Format';
  
  // Generate Summary dynamically
  let summary = "";
  if (sysScore > 70) {
    summary = `The analysis reveals strong evidence of AI generation or deep manipulation. Multiple forensic layers triggered high-confidence warnings across structural, frequency, and pixel-level domains. These elements strongly suggest a sophisticated composite image likely created or enhanced with generative AI techniques.`;
  } else if (sysScore > 35) {
    summary = `The analysis reveals partial anomalies consistent with localized manipulation or light AI filtering. While some regions remain authentic, conflicting signals in compression or error levels warrant moderate caution.`;
  } else {
    summary = `The analysis confirms the integrity of the image. Key indicators such as natural noise distribution, consistent physical lighting, and correct pixel-level error characteristics align perfectly with a genuine photograph. No significant AI artifacts were detected.`;
  }

  // Generate Breakdown dynamically
  const findings = result.findings || [];
  
  return (
    <BrutalCard className="!p-4 sm:!p-6 bg-[#0a0a0f] border-l-4 sm:border-l-8 border-l-[#ffaa00]">
      <h3 className="font-grotesk font-black text-ds-silver text-base sm:text-xl uppercase tracking-wider mb-4 flex items-center gap-2">
        <FileText className="text-[#ffaa00] w-5 h-5" /> 
        <span className="text-[#ffaa00]">Real-Time Analysis Report</span>
      </h3>
      
      <div className="font-mono text-[13px] sm:text-sm text-ds-silver/90 leading-relaxed whitespace-pre-wrap">
        <p className="font-bold text-white mb-1">Detection Report</p>
        <p className="mb-4">Image Type: {fileType}</p>

        <p className="font-bold text-[#ff4422] mb-4">Overall Forgery Score: {sysScore}%</p>

        <p className="font-bold text-white mb-2">Analysis Summary</p>
        <p className="text-ds-silver/70 mb-5">{summary}</p>

        <p className="font-bold text-white mb-3">Detailed Breakdown</p>
        
        {findings.length > 0 ? findings.map((f, idx) => {
          let featureName = f.engine || 'Indicator';
          let rawDetail = f.detail || '';
          let finalDetail = rawDetail;
          let anomalyScore = Math.round(Number(f.score || 0));

          // Parse backend string format: "Some feature name score: X/100. Description here."
          const match = rawDetail.match(/^([\w\s]+?)\s*score:\s*([\d.]+)\/100\.?\s*(.*)$/i);
          if (match) {
             let rawName = match[1].trim();
             
             // Clean up standard names from Deepscan models
             if (rawName.match(/Visual forensics/i)) featureName = "Visual Forensics (MAS)";
             else if (rawName.match(/Facial proportion/i)) featureName = "Facial Geometry & Proportions";
             else if (rawName.match(/Frequency fingerprint/i)) featureName = "Frequency & Spectrum Analysis";
             else if (rawName.match(/Context validity/i)) featureName = "Metadata & Contextual Integrity";
             else if (rawName.match(/Diffusion noise/i)) featureName = "Generative Diffusion Noise";
             else {
               // Capitalize unknown custom matches automatically
               featureName = rawName.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
             }

             // Backend raw scores are authenticity (0=FAKE, 100=REAL). 
             // Convert them to Anomaly Risk (0=REAL, 100=FAKE).
             const authenticityScore = parseFloat(match[2]);
             anomalyScore = Math.max(0, Math.min(100, 100 - Math.round(authenticityScore)));

             finalDetail = match[3] || 'No specific description provided.';
          } else if (rawDetail.includes('score:') && rawDetail.includes('/100')) {
             // Fallback fuzzy extraction
             const valMatch = rawDetail.match(/([\d.]+)\/100/);
             if (valMatch) {
                anomalyScore = Math.max(0, Math.min(100, 100 - Math.round(parseFloat(valMatch[1]))));
             }
          }

          const isWarning = anomalyScore >= 50;

          return (
            <div key={idx} className="mb-4 pl-3 border-l-2 border-[#2a2a2a] transition-all hover:border-[#ffaa00]/50 hover:bg-[#ffaa00]/10 p-2 -ml-2 rounded-r relative overflow-hidden">
              {isWarning && <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-[#ffaa00]/20 to-transparent pointer-events-none" />}
              <p className="font-bold mb-1 tracking-wide" style={{ color: isWarning ? '#ffaa00' : '#44aaff' }}>
                {featureName} | {anomalyScore}% {isWarning ? <span className="text-[#ff4422] drop-shadow-sm">(WARNING)</span> : ''}
              </p>
              <p className="text-ds-silver/70 text-[13px] leading-relaxed relative z-10">{finalDetail}</p>
            </div>
          );
        }) : (
          <p className="text-ds-silver/50 text-xs italic">No detailed forensic findings were recorded for this analysis.</p>
        )}
      </div>
    </BrutalCard>
  );
}
