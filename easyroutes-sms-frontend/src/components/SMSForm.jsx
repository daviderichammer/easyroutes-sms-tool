import { useState } from 'react';
import { Button } from '@/components/ui/button.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Textarea } from '@/components/ui/textarea.jsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Alert, AlertDescription } from '@/components/ui/alert.jsx';
import { Badge } from '@/components/ui/badge.jsx';
import { MessageSquare, Send, Loader2, LogOut, Eye } from 'lucide-react';
import ResultsDisplay from './ResultsDisplay.jsx';

const SMSForm = ({ onLogout }) => {
  const [routeNumber, setRouteNumber] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [preview, setPreview] = useState(null);
  const [showPreview, setShowPreview] = useState(false);

  const handleLogout = async () => {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
      onLogout();
    } catch (err) {
      console.error('Logout error:', err);
      onLogout(); // Logout anyway
    }
  };

  const handlePreview = async () => {
    if (!routeNumber) {
      setError('Please enter a route number first');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/sms/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ route_number: routeNumber }),
      });

      const data = await response.json();

      if (response.ok) {
        setPreview(data.preview);
        setShowPreview(true);
      } else {
        setError(data.error || 'Failed to preview route');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResults(null);

    try {
      const response = await fetch('/api/sms/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          route_number: routeNumber,
          message: message,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setResults(data.results);
        setShowPreview(false);
      } else {
        setError(data.error || 'Failed to send messages');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setRouteNumber('');
    setMessage('');
    setResults(null);
    setError('');
    setPreview(null);
    setShowPreview(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">EasyRoutes SMS Tool</h1>
              <p className="text-gray-600">Send notifications to incomplete delivery stops</p>
            </div>
          </div>
          <Button variant="outline" onClick={handleLogout}>
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </div>

        {/* Main Form */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Send className="w-5 h-5" />
              <span>Send SMS Messages</span>
            </CardTitle>
            <CardDescription>
              Enter a route number and custom message to send SMS notifications to all incomplete stops
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label htmlFor="routeNumber" className="text-sm font-medium">
                    Route Number
                  </label>
                  <Input
                    id="routeNumber"
                    type="text"
                    value={routeNumber}
                    onChange={(e) => setRouteNumber(e.target.value)}
                    placeholder="e.g., RT-12345"
                    required
                    disabled={loading}
                  />
                  <p className="text-xs text-gray-500">
                    Enter the route ID or name to target
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <label htmlFor="message" className="text-sm font-medium">
                      Custom Message
                    </label>
                    <Badge variant="secondary">
                      {message.length}/160
                    </Badge>
                  </div>
                  <Textarea
                    id="message"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Enter your custom message..."
                    rows={4}
                    maxLength={160}
                    required
                    disabled={loading}
                    className="resize-none"
                  />
                  <p className="text-xs text-gray-500">
                    SMS messages are limited to 160 characters
                  </p>
                </div>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="flex space-x-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handlePreview}
                  disabled={loading || !routeNumber}
                  className="flex-1"
                >
                  {loading ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Eye className="mr-2 h-4 w-4" />
                  )}
                  Preview Route
                </Button>

                <Button
                  type="submit"
                  disabled={loading || !routeNumber || !message}
                  className="flex-1"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Sending Messages...
                    </>
                  ) : (
                    <>
                      <Send className="mr-2 h-4 w-4" />
                      Send SMS Messages
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Preview Display */}
        {showPreview && preview && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Route Preview</CardTitle>
              <CardDescription>
                Review the stops that will receive SMS messages
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {preview.route_summary?.total_stops || 0}
                  </div>
                  <div className="text-sm text-blue-800">Total Stops</div>
                </div>
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {preview.total_incomplete || 0}
                  </div>
                  <div className="text-sm text-orange-800">Incomplete</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {preview.valid_phone_numbers || 0}
                  </div>
                  <div className="text-sm text-green-800">Valid Phones</div>
                </div>
                <div className="text-center p-3 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {preview.will_receive_sms || 0}
                  </div>
                  <div className="text-sm text-purple-800">Will Receive SMS</div>
                </div>
              </div>

              {preview.incomplete_stops && preview.incomplete_stops.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse border border-gray-200 rounded-lg">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="border border-gray-200 px-3 py-2 text-left text-sm font-medium">Stop ID</th>
                        <th className="border border-gray-200 px-3 py-2 text-left text-sm font-medium">Customer</th>
                        <th className="border border-gray-200 px-3 py-2 text-left text-sm font-medium">Phone</th>
                        <th className="border border-gray-200 px-3 py-2 text-left text-sm font-medium">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {preview.incomplete_stops.map((stop, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="border border-gray-200 px-3 py-2 text-sm">{stop.stop_id}</td>
                          <td className="border border-gray-200 px-3 py-2 text-sm">{stop.customer_name}</td>
                          <td className="border border-gray-200 px-3 py-2 text-sm">
                            {stop.has_phone ? (
                              <Badge variant="secondary">{stop.phone}</Badge>
                            ) : (
                              <Badge variant="destructive">No phone</Badge>
                            )}
                          </td>
                          <td className="border border-gray-200 px-3 py-2 text-sm">
                            <Badge variant="outline">{stop.delivery_status}</Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Results Display */}
        {results && <ResultsDisplay results={results} onReset={resetForm} />}
      </div>
    </div>
  );
};

export default SMSForm;

