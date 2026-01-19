import React, { useState, useEffect } from 'react';
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

  useEffect(() => {
    const fetchFeed = async () => {
      try {
        setLoading(true);
        const data = await getFeed();
        // API returns { reports: [...] }
        setReports(Array.isArray(data) ? data : (data.reports || []));
      } catch (err) {
        console.error('Failed to fetch feed:', err);
        setError('Failed to load reports. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchFeed();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-cyan-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
        <AlertTriangle className="h-12 w-12 text-red-500 mb-4" />
        <p className="text-red-400 mb-4">{error}</p>
        <Button onClick={() => window.location.reload()} variant="outline">Retry</Button>
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
