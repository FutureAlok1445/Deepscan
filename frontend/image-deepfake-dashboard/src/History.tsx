import React, { useEffect, useState } from 'react';
import './History.css';

interface HistoryItem {
    id: string;
    status: string;
    score: number | null;
    verdict: string | null;
    created_at: string;
    explainability_summary: string | null;
}

interface HistoryProps {
    onSelectScan: (id: string) => void;
    refreshTrigger: number;
}

const History: React.FC<HistoryProps> = ({ onSelectScan, refreshTrigger }) => {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const fetchHistory = async () => {
        setLoading(true);
        setError('');
        try {
            const response = await fetch('http://127.0.0.1:8000/api/v1/history?limit=10');
            if (!response.ok) throw new Error('Failed to fetch history');
            const data = await response.json();
            setHistory(data.items);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, [refreshTrigger]);

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div className="history-sidebar">
            <div className="history-header">
                <h3>Recent Scans</h3>
                <button className="refresh-btn" onClick={fetchHistory} disabled={loading}>
                    {loading ? '...' : '↻'}
                </button>
            </div>

            {error && <div className="history-error">{error}</div>}

            <div className="history-list">
                {history.length === 0 && !loading && <p className="empty-msg">No scans yet.</p>}
                {history.map((item) => (
                    <div
                        key={item.id}
                        className={`history-item ${item.status}`}
                        onClick={() => onSelectScan(item.id)}
                    >
                        <div className="item-main">
                            <span className="item-verdict">{item.verdict || 'Processing...'}</span>
                            <span className="item-score">{item.score !== null ? `${item.score.toFixed(0)}%` : '--'}</span>
                        </div>
                        <div className="item-meta">
                            <span>{formatDate(item.created_at)}</span>
                            <span className="item-status-tag">{item.status}</span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default History;
