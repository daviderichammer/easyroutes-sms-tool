import { Button } from '@/components/ui/button.jsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Badge } from '@/components/ui/badge.jsx';
import { CheckCircle, XCircle, RotateCcw, Download, MessageSquare } from 'lucide-react';

const ResultsDisplay = ({ results, onReset }) => {
  const {
    route_name,
    route_id,
    total_stops,
    incomplete_stops,
    messages_sent,
    failures,
    details,
    timestamp
  } = results;

  const successRate = incomplete_stops > 0 ? Math.round((messages_sent / incomplete_stops) * 100) : 0;

  const exportResults = () => {
    const csvContent = [
      ['Stop ID', 'Customer Name', 'Status', 'Phone', 'Details'],
      ...details.map(detail => [
        detail.stop_id,
        detail.customer_name || 'N/A',
        detail.status,
        detail.phone || 'N/A',
        detail.error || detail.message_sid || 'Success'
      ])
    ].map(row => row.map(field => `"${field}"`).join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sms-results-${route_id}-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <MessageSquare className="w-5 h-5" />
          <span>SMS Delivery Results</span>
        </CardTitle>
        <CardDescription>
          Results for route: {route_name} ({route_id})
          {timestamp && (
            <span className="block text-xs text-gray-500 mt-1">
              Completed at: {new Date(timestamp).toLocaleString()}
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Summary Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{total_stops}</div>
            <div className="text-sm text-blue-800">Total Stops</div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">{incomplete_stops}</div>
            <div className="text-sm text-orange-800">Incomplete</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{messages_sent}</div>
            <div className="text-sm text-green-800">Messages Sent</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{failures}</div>
            <div className="text-sm text-red-800">Failures</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">{successRate}%</div>
            <div className="text-sm text-purple-800">Success Rate</div>
          </div>
        </div>

        {/* Success/Failure Summary */}
        <div className="flex space-x-4 mb-6">
          {messages_sent > 0 && (
            <div className="flex items-center space-x-2 text-green-600">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">{messages_sent} messages sent successfully</span>
            </div>
          )}
          {failures > 0 && (
            <div className="flex items-center space-x-2 text-red-600">
              <XCircle className="w-5 h-5" />
              <span className="font-medium">{failures} messages failed</span>
            </div>
          )}
        </div>

        {/* Detailed Results Table */}
        {details && details.length > 0 && (
          <div className="overflow-x-auto mb-6">
            <table className="w-full border-collapse border border-gray-200 rounded-lg">
              <thead>
                <tr className="bg-gray-50">
                  <th className="border border-gray-200 px-3 py-2 text-left text-sm font-medium">Stop ID</th>
                  <th className="border border-gray-200 px-3 py-2 text-left text-sm font-medium">Customer</th>
                  <th className="border border-gray-200 px-3 py-2 text-left text-sm font-medium">Status</th>
                  <th className="border border-gray-200 px-3 py-2 text-left text-sm font-medium">Phone</th>
                  <th className="border border-gray-200 px-3 py-2 text-left text-sm font-medium">Details</th>
                </tr>
              </thead>
              <tbody>
                {details.map((detail, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="border border-gray-200 px-3 py-2 text-sm font-mono">
                      {detail.stop_id}
                    </td>
                    <td className="border border-gray-200 px-3 py-2 text-sm">
                      {detail.customer_name || 'N/A'}
                    </td>
                    <td className="border border-gray-200 px-3 py-2">
                      <Badge
                        variant={detail.status === 'sent' ? 'default' : 'destructive'}
                        className="text-xs"
                      >
                        {detail.status === 'sent' ? (
                          <>
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Sent
                          </>
                        ) : (
                          <>
                            <XCircle className="w-3 h-3 mr-1" />
                            Failed
                          </>
                        )}
                      </Badge>
                    </td>
                    <td className="border border-gray-200 px-3 py-2 text-sm font-mono">
                      {detail.phone || 'N/A'}
                    </td>
                    <td className="border border-gray-200 px-3 py-2 text-sm">
                      {detail.error ? (
                        <span className="text-red-600">{detail.error}</span>
                      ) : detail.message_sid ? (
                        <span className="text-green-600 font-mono text-xs">
                          {detail.message_sid}
                        </span>
                      ) : (
                        <span className="text-gray-500">Success</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
          <Button onClick={onReset} className="flex-1">
            <RotateCcw className="w-4 h-4 mr-2" />
            Send Another Message
          </Button>
          <Button variant="outline" onClick={exportResults} className="flex-1">
            <Download className="w-4 h-4 mr-2" />
            Export Results (CSV)
          </Button>
        </div>

        {/* Additional Information */}
        {incomplete_stops === 0 && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-800 text-sm">
              <strong>Note:</strong> No incomplete stops were found for this route. 
              All deliveries may already be completed.
            </p>
          </div>
        )}

        {failures > 0 && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-yellow-800 text-sm">
              <strong>Some messages failed to send.</strong> Common reasons include:
            </p>
            <ul className="text-yellow-700 text-sm mt-2 list-disc list-inside">
              <li>Invalid or missing phone numbers</li>
              <li>Network connectivity issues</li>
              <li>Twilio service limitations</li>
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ResultsDisplay;

