import React, { useState, useEffect, useCallback } from 'react';
import { getMonitors, getReportsForMonitor, downloadReport } from '../lib/api';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { AlertTriangle, FileText, Loader2 } from 'lucide-react';
import Header from './Header';
import ReportCard from './ReportCard';
import NewMonitorModal from './NewMonitorModal';

const IntelligenceFeed = () => {
  const [monitors, setMonitors] = useState([]);
  const [showNewMonitorModal, setShowNewMonitorModal] = useState(false);
  const [selectedMonitor, setSelectedMonitor] = useState(null);
  const [reports, setReports] = useState([]);
  const [monitorsLoading, setMonitorsLoading] = useState(true);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reportsError, setReportsError] = useState(null);

  const fetchMonitors = useCallback(async () => {
    try {
      setMonitorsLoading(true);
      setError(null);
      const monitorsData = await getMonitors();
      setMonitors(monitorsData.monitors || []);
      if (monitorsData.monitors && monitorsData.monitors.length > 0) {
        setSelectedMonitor(monitorsData.monitors[0]);
      }
    } catch (err) {
      console.error('Failed to fetch monitors:', err);
      setError('Failed to load monitors. Please try again.');
    } finally {
      setMonitorsLoading(false);
    }
  }, []);

  const fetchReports = useCallback(async (monitor) => {
    if (!monitor) return;
    try {
      setReportsLoading(true);
      setReportsError(null);
      const reportsData = await getReportsForMonitor(monitor.monitor_id);
      setReports(reportsData.reports || []);
    } catch (err) {
      console.error(`Failed to fetch reports for ${monitor.term}:`, err);
      setReportsError(`Failed to load reports for ${monitor.term}. Please try again.`);
    } finally {
      setReportsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMonitors();
  }, [fetchMonitors]);

  useEffect(() => {
    if (selectedMonitor) {
      fetchReports(selectedMonitor);
    }
  }, [selectedMonitor, fetchReports]);

  if (monitorsLoading) {
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800">
      <Header onNewMonitorClick={() => setShowNewMonitorModal(true)} />

      <NewMonitorModal
        isOpen={showNewMonitorModal}
        onClose={() => setShowNewMonitorModal(false)}
      />

      <div className="max-w-7xl mx-auto p-6 grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Left Column: Monitors */}
        <div className="md:col-span-1">
          <h2 className="text-lg font-semibold text-white mb-4">Monitors</h2>
          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="p-4 space-y-2">
              {error ? (
                <div className="text-center">
                  <p className="text-red-400 text-sm mb-4">{error}</p>
                  <Button
                    onClick={fetchMonitors}
                    variant="outline"
                    className="w-full border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
                  >
                    Retry
                  </Button>
                </div>
              ) : monitors.length === 0 ? (
                <div className="text-center">
                  <p className="text-slate-400 text-sm mb-4">No monitors yet.</p>
                  <Button
                    onClick={() => setShowNewMonitorModal(true)}
                    className="w-full bg-cyan-600 hover:bg-cyan-700 text-white"
                  >
                    Create First Monitor
                  </Button>
                </div>
              ) : (
                monitors.map((monitor) => (
                  <button
                    key={monitor.monitor_id}
                    onClick={() => setSelectedMonitor(monitor)}
                    className={`w-full text-left p-2 rounded-md transition-colors ${
                      selectedMonitor?.monitor_id === monitor.monitor_id
                        ? 'bg-slate-800 font-bold text-white'
                        : 'text-slate-400 hover:bg-slate-800'
                    }`}
                  >
                    {monitor.term}
                  </button>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Reports */}
        <div className="md:col-span-3">
          <h1 className="text-2xl font-bold text-white mb-4">Intelligence Feed</h1>
          {reportsLoading ? (
            <div className="flex justify-center items-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-cyan-500" />
            </div>
          ) : reportsError ? (
            <Card className="bg-red-900/20 border-red-500">
              <CardContent className="flex flex-col items-center justify-center p-12 text-center">
                <AlertTriangle className="h-12 w-12 text-red-500 mb-4" />
                <h3 className="text-lg font-semibold text-white mb-2">Error</h3>
                <p className="text-red-300">{reportsError}</p>
              </CardContent>
            </Card>
          ) : reports.length === 0 ? (
            <Card className="bg-slate-900 border-slate-800">
              <CardContent className="flex flex-col items-center justify-center p-12 text-center">
                <FileText className="h-12 w-12 text-slate-600 mb-4" />
                <h3 className="text-lg font-semibold text-white mb-2">
                  {selectedMonitor
                    ? `No reports for "${selectedMonitor.term}" yet.`
                    : 'No reports yet.'}
                </h3>
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
    </div>
  );
};

export default IntelligenceFeed;
