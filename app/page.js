'use client';

import { useState, useRef } from 'react';
import { Upload, Users, CheckCircle, AlertCircle, TrendingUp, Mail, Send, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

export default function Home() {
  const [file, setFile] = useState(null);
  const [students, setStudents] = useState([]);
  const [emails, setEmails] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [sendResult, setSendResult] = useState(null);
  const [previewEmail, setPreviewEmail] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && (selectedFile.name.endsWith('.xlsx') || selectedFile.name.endsWith('.xls'))) {
      setFile(selectedFile);
      setStudents([]);
      setEmails([]);
      setAnalytics(null);
      setSendResult(null);
    } else {
      alert('Please select a valid Excel file (.xlsx or .xls)');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && (droppedFile.name.endsWith('.xlsx') || droppedFile.name.endsWith('.xls'))) {
      setFile(droppedFile);
      setStudents([]);
      setEmails([]);
      setAnalytics(null);
      setSendResult(null);
    }
  };

  const startAgent = async () => {
    if (!file) return;

    setIsAnalyzing(true);
    setProgress(0);
    setProgressMessage('Starting AI agent...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/agent', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        setStudents(result.data.students);
        setEmails(result.data.emails);
        setAnalytics({
          total: result.data.total_students,
          incomplete: result.data.incomplete_students,
          complete: result.data.total_students - result.data.incomplete_students,
          critical: result.data.students.filter(s => s.completion < 70).length,
        });
        setProgress(100);
        setProgressMessage('Analysis complete!');
      } else {
        alert('Error: ' + result.error);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to analyze file');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const sendEmails = async () => {
    if (emails.length === 0) return;

    setIsSending(true);
    setSendResult(null);

    try {
      const response = await fetch('/api/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emails }),
      });

      const result = await response.json();

      if (result.success) {
        setSendResult({
          success: true,
          sent: result.sent,
          total: result.total,
        });
      } else {
        setSendResult({
          success: false,
          error: result.error,
        });
      }
    } catch (error) {
      console.error('Error:', error);
      setSendResult({
        success: false,
        error: 'Failed to send emails',
      });
    } finally {
      setIsSending(false);
    }
  };

  const getCompletionBadge = (completion) => {
    if (completion >= 90) return <Badge className="bg-green-500">Complete {completion}%</Badge>;
    if (completion >= 70) return <Badge className="bg-yellow-500">Incomplete {completion}%</Badge>;
    return <Badge className="bg-red-500">Critical {completion}%</Badge>;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">🤖 Agentic Student Profile System</h1>
          <p className="text-lg text-gray-600">AI-powered autonomous agent for profile completion</p>
        </div>

        {/* Upload Section */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Upload Student Excel File
            </CardTitle>
            <CardDescription>Upload an Excel file with student profiles</CardDescription>
          </CardHeader>
          <CardContent>
            <div
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center cursor-pointer hover:border-blue-500 transition-colors"
            >
              <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p className="text-lg font-medium text-gray-700 mb-2">
                {file ? file.name : 'Click to upload or drag and drop'}
              </p>
              <p className="text-sm text-gray-500">Excel files (.xlsx, .xls)</p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>

            {file && (
              <Button
                onClick={startAgent}
                disabled={isAnalyzing}
                className="w-full mt-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                size="lg"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    AI Agent Analyzing...
                  </>
                ) : (
                  <>
                    <TrendingUp className="mr-2 h-5 w-5" />
                    Start AI Agent
                  </>
                )}
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Progress */}
        {isAnalyzing && (
          <Card className="mb-8">
            <CardContent className="pt-6">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="font-medium">{progressMessage}</span>
                  <span className="text-gray-500">{progress}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Analytics */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Total Students</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-blue-500" />
                  <span className="text-3xl font-bold">{analytics.total}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Complete</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-3xl font-bold">{analytics.complete}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Incomplete</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-yellow-500" />
                  <span className="text-3xl font-bold">{analytics.incomplete}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Critical</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-red-500" />
                  <span className="text-3xl font-bold">{analytics.critical}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Students Table */}
        {students.length > 0 && (
          <Card className="mb-8">
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Student Profiles</CardTitle>
                  <CardDescription>AI-analyzed student profiles with missing fields highlighted</CardDescription>
                </div>
                {emails.length > 0 && (
                  <Button
                    onClick={sendEmails}
                    disabled={isSending}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    {isSending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      <>
                        <Send className="mr-2 h-4 w-4" />
                        Send {emails.length} Emails
                      </>
                    )}
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3 font-medium">Name</th>
                      <th className="text-left p-3 font-medium">Email</th>
                      <th className="text-left p-3 font-medium">Roll Number</th>
                      <th className="text-left p-3 font-medium">Completion</th>
                      <th className="text-left p-3 font-medium">Missing Fields</th>
                      <th className="text-left p-3 font-medium">Email Status</th>
                      <th className="text-left p-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map((student, idx) => {
                      const email = emails.find(e => e.student_email === student.email);
                      return (
                        <tr key={idx} className="border-b hover:bg-gray-50">
                          <td className="p-3">{student.student_name || 'N/A'}</td>
                          <td className="p-3">{student.email || 'N/A'}</td>
                          <td className="p-3">{student.roll_number || 'N/A'}</td>
                          <td className="p-3">{getCompletionBadge(student.completion)}</td>
                          <td className="p-3">
                            {student.missing_fields.length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {student.missing_fields.map((field, i) => (
                                  <Badge
                                    key={i}
                                    variant="outline"
                                    className="bg-yellow-100 text-yellow-800 border-yellow-300"
                                  >
                                    {field.replace('_', ' ')}
                                  </Badge>
                                ))}
                              </div>
                            ) : (
                              <span className="text-green-600 font-medium">Complete ✓</span>
                            )}
                          </td>
                          <td className="p-3">
                            {email ? (
                              <Badge className="bg-blue-500">
                                <Mail className="h-3 w-3 mr-1" />
                                Ready
                              </Badge>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          <td className="p-3">
                            {email && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  setPreviewEmail(email);
                                  setShowPreview(true);
                                }}
                              >
                                Preview
                              </Button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Send Result */}
        {sendResult && (
          <Card className={sendResult.success ? 'border-green-500' : 'border-red-500'}>
            <CardContent className="pt-6">
              {sendResult.success ? (
                <div className="flex items-center gap-3 text-green-700">
                  <CheckCircle className="h-6 w-6" />
                  <div>
                    <p className="font-semibold text-lg">Emails Sent Successfully!</p>
                    <p className="text-sm">
                      {sendResult.sent} of {sendResult.total} emails sent
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3 text-red-700">
                  <AlertCircle className="h-6 w-6" />
                  <div>
                    <p className="font-semibold text-lg">Failed to Send Emails</p>
                    <p className="text-sm">{sendResult.error}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Email Preview Modal */}
        {showPreview && previewEmail && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-3xl max-h-[90vh] overflow-hidden">
              <CardHeader className="border-b">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle>Email Preview - {previewEmail.student_name}</CardTitle>
                    <CardDescription className="mt-2">
                      <div className="flex flex-col gap-1 text-sm">
                        <span><strong>To:</strong> {previewEmail.student_email || 'No email address'}</span>
                        <span><strong>Subject:</strong> {previewEmail.subject}</span>
                        <span><strong>Completion:</strong> {previewEmail.completion}%</span>
                      </div>
                    </CardDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setShowPreview(false);
                      setPreviewEmail(null);
                    }}
                  >
                    ✕
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-y-auto max-h-[60vh] p-6">
                  <div 
                    dangerouslySetInnerHTML={{ __html: previewEmail.body_html }}
                    className="prose max-w-none"
                  />
                </div>
              </CardContent>
              <div className="border-t p-4 flex justify-end gap-2 bg-gray-50">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowPreview(false);
                    setPreviewEmail(null);
                  }}
                >
                  Close
                </Button>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}