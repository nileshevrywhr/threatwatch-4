import React, { memo } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Download } from 'lucide-react';

const getSeverityColor = (severity) => {
  switch (severity?.toLowerCase()) {
    case 'critical': return 'bg-red-500/10 text-red-500 border-red-500/20';
    case 'high': return 'bg-orange-500/10 text-orange-500 border-orange-500/20';
    case 'medium': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
    case 'low': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
    default: return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
  }
};

const ReportCard = memo(({ report, onDownload }) => {
  return (
    <Card className="bg-slate-900 border-slate-800">
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
          onClick={() => onDownload(report.report_id)}
        >
          <Download className="h-4 w-4 mr-2" />
          Download Report
        </Button>
      </CardFooter>
    </Card>
  );
});

ReportCard.displayName = 'ReportCard';

export default ReportCard;
