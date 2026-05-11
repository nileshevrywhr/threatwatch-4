import React, { memo, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Download, Loader2 } from 'lucide-react';

const getSeverityColor = (severity) => {
  switch (severity?.toLowerCase()) {
    case 'critical': return 'bg-red-500/10 text-red-500 border-red-500/20';
    case 'high': return 'bg-orange-500/10 text-orange-500 border-orange-500/20';
    case 'medium': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
    case 'low': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
    default: return 'bg-muted text-muted-foreground border-border';
  }
};

const ReportCard = memo(({ report, onDownload }) => {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    try {
      setIsDownloading(true);
      await onDownload(report.report_id);
    } catch (error) {
      console.error("Download failed", error);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <Card className="border-border">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <CardTitle className="text-lg font-medium">
                {report.term}
              </CardTitle>
              {report.severity && (
                <Badge variant="outline" className={getSeverityColor(report.severity)}>
                  {report.severity}
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              {report.created_at ? new Date(report.created_at).toLocaleDateString() : 'Unknown Date'}
            </p>
          </div>
          {report.status && (
            <Badge variant="secondary">
              {report.status}
            </Badge>
          )}
        </div>
      </CardHeader>
      {report.summary && (
        <CardContent className="pb-4">
          <p className="text-muted-foreground text-sm">
            {report.summary}
          </p>
        </CardContent>
      )}
      <CardFooter>
        <Button
          variant="outline"
          size="sm"
          className="w-full sm:w-auto"
          onClick={handleDownload}
          disabled={isDownloading}
        >
          {isDownloading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Downloading...
            </>
          ) : (
            <>
              <Download className="h-4 w-4 mr-2" />
              Download Report
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
});

ReportCard.displayName = 'ReportCard';

export default ReportCard;
