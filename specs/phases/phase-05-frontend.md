# Phase 5: Frontend Development

**Timeline**: Week 5-6

## Objectives

- Build email dashboard with real-time updates
- Create response editor component
- Implement triage queue interface
- Build settings and preferences UI
- Setup state management and data fetching

## 5.1 Email Dashboard Component

### Main Dashboard

```typescript
// frontend/app/dashboard/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { EmailList } from '@/components/EmailList';
import { TriageQueue } from '@/components/TriageQueue';
import { Stats } from '@/components/Stats';

interface Email {
  id: string;
  subject: string;
  sender: string;
  receivedAt: string;
  category: string;
  priority: 'urgent' | 'high' | 'medium' | 'low';
  urgencyScore: number;
  requiresAction: boolean;
}

export default function Dashboard() {
  const { data: emails, isLoading } = useQuery<Email[]>({
    queryKey: ['emails'],
    queryFn: async () => {
      const response = await fetch('/api/v1/emails');
      return response.json();
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await fetch('/api/v1/emails/stats');
      return response.json();
    },
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Email Dashboard</h1>

      <Stats data={stats} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        <div className="lg:col-span-2">
          <EmailList emails={emails} isLoading={isLoading} />
        </div>

        <div>
          <TriageQueue emails={emails?.filter(e => e.requiresAction)} />
        </div>
      </div>
    </div>
  );
}
```

## 5.2 Response Editor Component

### Interactive Response Editor

```typescript
// frontend/components/ResponseEditor.tsx
'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

interface ResponseEditorProps {
  emailId: string;
  originalEmail: {
    subject: string;
    body: string;
    sender: string;
  };
  onSend: () => void;
}

export function ResponseEditor({ emailId, originalEmail, onSend }: ResponseEditorProps) {
  const [response, setResponse] = useState('');
  const [tone, setTone] = useState<'professional' | 'casual' | 'formal'>('professional');
  const [isEditing, setIsEditing] = useState(false);

  const generateMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`/api/v1/responses/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_id: emailId,
          tone,
          length: 'medium',
        }),
      });
      return res.json();
    },
    onSuccess: (data) => {
      setResponse(data.response_text);
      setIsEditing(true);
    },
  });

  const sendMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`/api/v1/responses/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_id: emailId,
          response_text: response,
        }),
      });
      return res.json();
    },
    onSuccess: () => {
      onSend();
    },
  });

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Original Email</h3>
        <div className="bg-gray-50 p-4 rounded">
          <p className="text-sm text-gray-600">From: {originalEmail.sender}</p>
          <p className="text-sm font-medium mt-1">Subject: {originalEmail.subject}</p>
          <p className="text-sm mt-2 whitespace-pre-wrap">{originalEmail.body.substring(0, 200)}...</p>
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">Response Tone</label>
        <select
          value={tone}
          onChange={(e) => setTone(e.target.value as any)}
          className="w-full border rounded px-3 py-2"
        >
          <option value="professional">Professional</option>
          <option value="casual">Casual</option>
          <option value="formal">Formal</option>
        </select>
      </div>

      {!isEditing ? (
        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {generateMutation.isPending ? 'Generating...' : 'Generate Response'}
        </button>
      ) : (
        <>
          <textarea
            value={response}
            onChange={(e) => setResponse(e.target.value)}
            rows={10}
            className="w-full border rounded px-3 py-2 mb-4"
            placeholder="Edit your response..."
          />

          <div className="flex gap-2">
            <button
              onClick={() => generateMutation.mutate()}
              className="flex-1 bg-gray-200 py-2 rounded hover:bg-gray-300"
            >
              Regenerate
            </button>
            <button
              onClick={() => sendMutation.mutate()}
              disabled={sendMutation.isPending}
              className="flex-1 bg-green-600 text-white py-2 rounded hover:bg-green-700 disabled:opacity-50"
            >
              {sendMutation.isPending ? 'Sending...' : 'Send Email'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
```

## 5.3 Triage Queue Component

### Priority-Based Queue

```typescript
// frontend/components/TriageQueue.tsx
'use client';

import { useMemo } from 'react';

interface Email {
  id: string;
  subject: string;
  sender: string;
  priority: 'urgent' | 'high' | 'medium' | 'low';
  category: string;
  urgencyScore: number;
}

interface TriageQueueProps {
  emails?: Email[];
}

const priorityColors = {
  urgent: 'bg-red-100 border-red-500 text-red-800',
  high: 'bg-orange-100 border-orange-500 text-orange-800',
  medium: 'bg-yellow-100 border-yellow-500 text-yellow-800',
  low: 'bg-green-100 border-green-500 text-green-800',
};

export function TriageQueue({ emails = [] }: TriageQueueProps) {
  const sortedEmails = useMemo(() => {
    return [...emails].sort((a, b) => b.urgencyScore - a.urgencyScore);
  }, [emails]);

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h2 className="text-xl font-bold mb-4">Action Required</h2>

      {sortedEmails.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No emails require action</p>
      ) : (
        <div className="space-y-3">
          {sortedEmails.map((email) => (
            <div
              key={email.id}
              className={`border-l-4 p-3 rounded ${priorityColors[email.priority]}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="font-medium text-sm truncate">{email.subject}</p>
                  <p className="text-xs mt-1 opacity-75">{email.sender}</p>
                </div>
                <span className="text-xs font-semibold ml-2">{email.priority.toUpperCase()}</span>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <span className="text-xs bg-white bg-opacity-50 px-2 py-1 rounded">
                  {email.category}
                </span>
                <div className="flex-1 bg-white bg-opacity-30 rounded-full h-1">
                  <div
                    className="bg-current h-full rounded-full"
                    style={{ width: `${email.urgencyScore * 100}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

## 5.4 Email List Component

### Filterable Email List

```typescript
// frontend/components/EmailList.tsx
'use client';

import { useState } from 'react';
import { EmailCard } from './EmailCard';

interface Email {
  id: string;
  subject: string;
  sender: string;
  receivedAt: string;
  category: string;
  priority: string;
  urgencyScore: number;
}

interface EmailListProps {
  emails?: Email[];
  isLoading: boolean;
}

export function EmailList({ emails = [], isLoading }: EmailListProps) {
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');

  const filteredEmails = emails.filter((email) => {
    if (categoryFilter !== 'all' && email.category !== categoryFilter) return false;
    if (priorityFilter !== 'all' && email.priority !== priorityFilter) return false;
    return true;
  });

  if (isLoading) {
    return <div className="text-center py-8">Loading emails...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex gap-4 mb-4">
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="border rounded px-3 py-2"
        >
          <option value="all">All Categories</option>
          <option value="work">Work</option>
          <option value="personal">Personal</option>
          <option value="marketing">Marketing</option>
          <option value="support">Support</option>
          <option value="finance">Finance</option>
        </select>

        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="border rounded px-3 py-2"
        >
          <option value="all">All Priorities</option>
          <option value="urgent">Urgent</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      <div className="space-y-2">
        {filteredEmails.map((email) => (
          <EmailCard key={email.id} email={email} />
        ))}
      </div>
    </div>
  );
}
```

## 5.5 Statistics Component

### Dashboard Stats

```typescript
// frontend/components/Stats.tsx
'use client';

interface StatsProps {
  data?: {
    total_emails: number;
    unread_count: number;
    categories: Record<string, number>;
    priorities: Record<string, number>;
  };
}

export function Stats({ data }: StatsProps) {
  if (!data) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div className="bg-white rounded-lg shadow-md p-4">
        <h3 className="text-sm text-gray-600 mb-1">Total Emails</h3>
        <p className="text-3xl font-bold">{data.total_emails}</p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-4">
        <h3 className="text-sm text-gray-600 mb-1">Unread</h3>
        <p className="text-3xl font-bold text-blue-600">{data.unread_count}</p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-4">
        <h3 className="text-sm text-gray-600 mb-1">Urgent</h3>
        <p className="text-3xl font-bold text-red-600">
          {data.priorities.urgent || 0}
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-4">
        <h3 className="text-sm text-gray-600 mb-1">Requires Action</h3>
        <p className="text-3xl font-bold text-orange-600">
          {(data.priorities.urgent || 0) + (data.priorities.high || 0)}
        </p>
      </div>
    </div>
  );
}
```

## 5.6 Settings Page

### User Preferences UI

```typescript
// frontend/app/settings/page.tsx
'use client';

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';

export default function SettingsPage() {
  const { data: preferences } = useQuery({
    queryKey: ['preferences'],
    queryFn: async () => {
      const res = await fetch('/api/v1/preferences');
      return res.json();
    },
  });

  const [autoTriage, setAutoTriage] = useState(preferences?.auto_triage_enabled ?? true);
  const [responseTone, setResponseTone] = useState(preferences?.response_tone ?? 'professional');

  const updateMutation = useMutation({
    mutationFn: async (data: any) => {
      const res = await fetch('/api/v1/preferences', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      return res.json();
    },
  });

  const handleSave = () => {
    updateMutation.mutate({
      auto_triage_enabled: autoTriage,
      response_tone: responseTone,
    });
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>

      <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
        <div>
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={autoTriage}
              onChange={(e) => setAutoTriage(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="font-medium">Enable Auto-Triage</span>
          </label>
          <p className="text-sm text-gray-600 mt-1 ml-7">
            Automatically classify incoming emails
          </p>
        </div>

        <div>
          <label className="block font-medium mb-2">Default Response Tone</label>
          <select
            value={responseTone}
            onChange={(e) => setResponseTone(e.target.value)}
            className="w-full border rounded px-3 py-2"
          >
            <option value="professional">Professional</option>
            <option value="casual">Casual</option>
            <option value="formal">Formal</option>
            <option value="concise">Concise</option>
          </select>
        </div>

        <button
          onClick={handleSave}
          disabled={updateMutation.isPending}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {updateMutation.isPending ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
}
```

## Deliverables

- ✅ Email dashboard with real-time updates
- ✅ Response editor with multi-tone support
- ✅ Triage queue with priority sorting
- ✅ Email list with filtering
- ✅ Statistics dashboard
- ✅ Settings and preferences UI
- ✅ Mobile-responsive design
- ✅ Loading states and error handling

## Success Criteria

- Dashboard loads in <2 seconds
- Real-time updates without page refresh
- Mobile-responsive on all screen sizes
- Intuitive navigation and UX
- Proper loading and error states
- Accessibility compliant (WCAG 2.1)
- Cross-browser compatible
