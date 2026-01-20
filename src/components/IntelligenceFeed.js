import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getFeed, downloadReport } from '../lib/api';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { AlertTriangle, FileText, Loader2 } from 'lucide-react';
import Header from './Header';
import ReportCard from './ReportCard';

const IntelligenceFeed = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const fetchFeed = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getFeed();
      // API returns { reports: [...] }
      setReports(Array.isArray(data) ? data : (data.reports || []));
    } catch (err) {
      console.error('Failed to fetch feed:', err);
      setError('Failed to load reports. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFeed();
  }, [fetchFeed]);

  if (loading) {
    return (
      <div
        className="min-h-screen bg-slate-950 flex flex-col items-center justify-center space-y-4"
        role="status"
        aria-label="Loading intelligence reports"
      >
        <Loader2 className="h-10 w-10 animate-spin text-cyan-500" aria-hidden="true" />
        <p className="text-slate-400 animate-pulse font-medium">Loading intelligence reports...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4"
        role="alert"
      >
        <AlertTriangle className="h-12 w-12 text-red-500 mb-4" aria-hidden="true" />
        <h2 className="text-xl font-semibold text-white mb-2">Unable to load feed</h2>
        <p className="text-slate-400 mb-6 text-center max-w-md">{error}</p>
        <Button
          onClick={fetchFeed}
          variant="outline"
          className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
        >
          Retry Connection
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800">
      <Header />

      <div className="max-w-4xl mx-auto p-6 space-y-6">
        <h1 className="text-2xl font-bold text-white">Intelligence Feed</h1>

        {reports.length === 0 ? (
          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="flex flex-col items-center justify-center p-12 text-center">
              <FileText className="h-12 w-12 text-slate-600 mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">No reports found</h3>
              <p className="text-slate-400 mb-6">Start your first scan to generate intelligence reports.</p>
              <Button onClick={() => navigate('/')} className="bg-cyan-600 hover:bg-cyan-700 text-white">
                Run First Scan
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {reports.map((report) => (
              <ReportCard
                key={report.report_id}
                report={report}
                onDownload={downloadReport}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default IntelligenceFeed;
