import React, { useState } from 'react';
import { Download, FileText, Loader } from 'lucide-react';
import { downloadReport } from '../../api/deepscan';
import BrutalButton from '../ui/BrutalButton';

export default function DownloadReport({ resultId, currentScore, currentVerdict }) {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    if (!resultId) return;
    setLoading(true);
    try {
      const blob = await downloadReport(resultId, currentScore, currentVerdict);
      if (blob instanceof Blob) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `deepscan-report-${resultId}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } else {
        // Mock mode — blob is not actual blob
        console.log('Report download (mock mode):', blob);
      }
    } catch (err) {
      console.error('Download failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <BrutalButton
      variant="secondary"
      size="sm"
      onClick={handleDownload}
      loading={loading}
      disabled={!resultId}
    >
      {loading ? (
        <Loader className="w-4 h-4 animate-spin" />
      ) : (
        <Download className="w-4 h-4" />
      )}
      <FileText className="w-3.5 h-3.5" />
      PDF Report
    </BrutalButton>
  );
}
