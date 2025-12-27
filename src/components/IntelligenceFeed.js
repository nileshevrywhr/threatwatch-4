import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getFeed, downloadReport } from '../lib/api';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Download, Shield, AlertTriangle, FileText, Loader2 } from 'lucide-react';

const getSeverityColor = (severity) => {
  switch (severity?.toLowerCase()) {
    case 'critical': return 'bg-red-500/10 text-red-500 border-red-500/20';
    case 'high': return 'bg-orange-500/10 text-orange-500 border-orange-500/20';
    case 'medium': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
    case 'low': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
    default: return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
  }
};

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
        setReports(data.reports || []);
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
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="flex items-center space-x-3 mb-8">
          <Shield className="h-8 w-8 text-cyan-500" />
          <h1 className="text-2xl font-bold text-white">Intelligence Feed</h1>
        </header>

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
              <Card key={report.id} className="bg-slate-900 border-slate-800">
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <CardTitle className="text-lg text-white font-medium">
                          {report.term}
                        </CardTitle>
                        {report.severity && (
                          <Badge variant="outline" className={getSeverityColor(report.severity)}>
                            {report.severity}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-slate-400">
                        {report.created_at ? new Date(report.created_at).toLocaleDateString() : 'Unknown Date'}
                      </p>
                    </div>
                    {report.status && (
                      <Badge variant="secondary" className="bg-slate-800 text-slate-300">
                        {report.status}
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                {report.summary && (
                  <CardContent className="pb-4">
                    <p className="text-slate-300 text-sm">
                      {report.summary}
                    </p>
                  </CardContent>
                )}
                <CardFooter>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full sm:w-auto border-slate-700 text-slate-300 hover:bg-slate-800"
                    onClick={() => downloadReport(report.id)}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download Report
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default IntelligenceFeed;
