# AGENCY OS — Web UI Foundation
# React + TypeScript frontend for the creative intelligence platform

// This file provides the complete React app structure and core components.
// Run with: cd aurora/ui && npm install && npm run dev

"""
Directory Structure:
aurora/ui/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── src/
│   ├── main.tsx              # App entry point
│   ├── App.tsx               # Main app component
│   ├── router.tsx            # React Router config
│   ├── api/
│   │   ├── client.ts         # API client (axios/fetch)
│   │   ├── interpretations.ts
│   │   ├── projects.ts
│   │   ├── erp.ts
│   │   └── ai.ts
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── Breadcrumbs.tsx
│   │   │   └── PageLayout.tsx
│   │   ├── Common/
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Spinner.tsx
│   │   │   └── EmptyState.tsx
│   │   ├── Intelligence/
│   │   │   ├── InsightCard.tsx
│   │   │   ├── QualityScore.tsx
│   │   │   ├── TagList.tsx
│   │   │   ├── InterpretationView.tsx
│   │   │   └── ComparisonView.tsx
│   │   ├── ERP/
│   │   │   ├── InvoiceList.tsx
│   │   │   ├── PipelineChart.tsx
│   │   │   ├── TaskBoard.tsx
│   │   │   └── TeamUtilization.tsx
│   │   ├── AI/
│   │   │   ├── AIChat.tsx
│   │   │   ├── InsightFeed.tsx
│   │   │   ├── ForecastChart.tsx
│   │   │   └── ChurnRiskList.tsx
│   │   └── Workflow/
│   │       ├── WorkflowBuilder.tsx
│   │       ├── NodeEditor.tsx
│   │       └── NodeTypes.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Interpret.tsx
│   │   ├── Projects.tsx
│   │   ├── ProjectDetail.tsx
│   │   ├── Memory.tsx
│   │   ├── Observe.tsx
│   │   ├── ERP/
│   │   │   ├── CRM.tsx
│   │   │   ├── Finance.tsx
│   │   │   ├── HR.tsx
│   │   │   ├── Assets.tsx
│   │   │   ├── Production.tsx
│   │   │   └── Sales.tsx
│   │   ├── AI/
│   │   │   ├── AIStudio.tsx
│   │   │   ├── Forecasts.tsx
│   │   │   └── Insights.tsx
│   │   ├── Workflows.tsx
│   │   ├── Agents.tsx
│   │   ├── Marketplace.tsx
│   │   └── Settings.tsx
│   ├── hooks/
│   │   ├── useApi.ts
│   │   ├── useAuth.ts
│   │   ├── useWebSocket.ts
│   │   ├── useInterpretation.ts
│   │   └── useERP.ts
│   ├── stores/
│   │   ├── authStore.ts
│   │   ├── projectStore.ts
│   │   ├── interpretationStore.ts
│   │   └── erpStore.ts
│   ├── types/
│   │   ├── index.ts
│   │   ├── interpretation.ts
│   │   ├── project.ts
│   │   ├── erp.ts
│   │   └── user.ts
│   └── styles/
│       ├── globals.css
│       ├── tailwind.config.js
│       └── theme.ts
"""


# ─── package.json ───

PACKAGE_JSON = """
{
  "name": "agency-os-ui",
  "version": "1.0.0-alpha",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src/",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "@tanstack/react-query": "^5.50.0",
    "zustand": "^4.5.0",
    "axios": "^1.7.0",
    "recharts": "^2.12.0",
    "reactflow": "^11.11.0",
    "lucide-react": "^0.400.0",
    "date-fns": "^3.6.0",
    "react-hot-toast": "^2.4.0",
    "tailwindcss": "^3.4.0",
    "@headlessui/react": "^2.1.0",
    "@heroicons/react": "^2.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.3.0",
    "vitest": "^2.0.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
"""


# ─── Key Components ───

# src/App.tsx
APP_TSX = """
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { Layout } from './components/Layout/PageLayout';
import { Dashboard } from './pages/Dashboard';
import { Interpret } from './pages/Interpret';
import { Projects } from './pages/Projects';
import { ProjectDetail } from './pages/ProjectDetail';
import { Memory } from './pages/Memory';
import { Observe } from './pages/Observe';
import { AIStudio } from './pages/AI/AIStudio';
import { CRM } from './pages/ERP/CRM';
import { Finance } from './pages/ERP/Finance';
import { Workflows } from './pages/Workflows';
import { Settings } from './pages/Settings';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/interpret" element={<Interpret />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
            <Route path="/memory" element={<Memory />} />
            <Route path="/observe" element={<Observe />} />
            <Route path="/ai" element={<AIStudio />} />
            <Route path="/erp/crm" element={<CRM />} />
            <Route path="/erp/finance" element={<Finance />} />
            <Route path="/workflows" element={<Workflows />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
        <Toaster position="top-right" />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
"""


# src/api/client.ts
API_CLIENT = """
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
});

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('agency_os_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('agency_os_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
"""


# src/pages/Dashboard.tsx
DASHBOARD_TSX = """
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { QualityScore } from '../components/Intelligence/QualityScore';
import { InsightCard } from '../components/Intelligence/InsightCard';
import { PipelineChart } from '../components/ERP/PipelineChart';
import { TeamUtilization } from '../components/ERP/TeamUtilization';

export function Dashboard() {
  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: () => api.get('/status').then(r => r.data),
    refetchInterval: 30000
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Projects" value={status?.stats?.total_projects || 0} />
        <StatCard title="Assets" value={status?.stats?.memory_nodes || 0} />
        <StatCard title="Team Members" value={status?.stats?.users || 0} />
        <StatCard title="Uptime" value={`${Math.floor((status?.uptime_seconds || 0) / 3600)}h`} />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <PipelineChart />
        </div>
        <div>
          <TeamUtilization />
        </div>
      </div>

      {/* Recent Insights */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Recent Insights</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Would fetch from API */}
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value }: { title: string; value: number | string }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <p className="text-sm text-gray-500">{title}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}
"""


# src/pages/Interpret.tsx
INTERPRET_TSX = """
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../api/client';
import { InterpretationView } from '../components/Intelligence/InterpretationView';

export function Interpret() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);

  const interpretMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('critique', 'true');
      formData.append('improve', 'true');
      return api.post('/interpret', formData).then(r => r.data);
    },
    onSuccess: (data) => setResult(data)
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Interpret Media</h1>

      {/* Upload */}
      <div className="bg-white rounded-lg shadow p-6">
        <input
          type="file"
          accept="image/*,video/*,audio/*,.pdf,.docx,.py,.js,.fig,.blend"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        {file && (
          <button
            onClick={() => interpretMutation.mutate(file)}
            disabled={interpretMutation.isPending}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
          >
            {interpretMutation.isPending ? 'Analyzing...' : 'Interpret'}
          </button>
        )}
      </div>

      {/* Results */}
      {result && <InterpretationView data={result} />}
    </div>
  );
}
"""


# src/components/Intelligence/InterpretationView.tsx
INTERPRETATION_VIEW_TSX = """
import { QualityScore } from './QualityScore';
import { TagList } from './TagList';
import { InsightCard } from './InsightCard';

export function InterpretationView({ data }: { data: any }) {
  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">{data.summary}</h2>
            <p className="text-sm text-gray-500 mt-1">
              Type: {data.media_type} | ID: {data.media_id}
            </p>
          </div>
          <QualityScore score={data.quality_score} />
        </div>
        <TagList tags={data.tags} />
      </div>

      {/* Insights */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Insights ({data.insights.length})</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.insights.map((insight: any, i: number) => (
            <InsightCard key={i} insight={insight} />
          ))}
        </div>
      </div>
    </div>
  );
}
"""


# src/components/Intelligence/QualityScore.tsx
QUALITY_SCORE_TSX = """
export function QualityScore({ score }: { score: number }) {
  const color = score >= 8 ? 'text-green-600' : score >= 5 ? 'text-yellow-600' : 'text-red-600';

  return (
    <div className={`text-center ${color}`}>
      <div className="text-3xl font-bold">{score.toFixed(1)}</div>
      <div className="text-xs">/10</div>
    </div>
  );
}
"""


# src/components/Intelligence/TagList.tsx
TAG_LIST_TSX = """
export function TagList({ tags }: { tags: string[] }) {
  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {tags.map((tag, i) => (
        <span key={i} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
          {tag}
        </span>
      ))}
    </div>
  );
}
"""


# src/components/Intelligence/InsightCard.tsx
INSIGHT_CARD_TSX = """
export function InsightCard({ insight }: { insight: any }) {
  const domainColors: Record<string, string> = {
    narrative: 'bg-purple-100 text-purple-800',
    visual: 'bg-blue-100 text-blue-800',
    symbolism: 'bg-pink-100 text-pink-800',
    design: 'bg-green-100 text-green-800',
    marketing: 'bg-orange-100 text-orange-800',
    psychological: 'bg-red-100 text-red-800',
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-2">
        <span className={`px-2 py-0.5 text-xs rounded ${domainColors[insight.domain] || 'bg-gray-100'}`}>
          {insight.domain}
        </span>
        <span className="text-xs text-gray-500">
          {Math.round(insight.confidence * 100)}% confidence
        </span>
      </div>
      <h4 className="font-medium text-sm">{insight.category}</h4>
      <p className="text-sm text-gray-600 mt-1">{insight.finding}</p>
      {insight.suggestions?.length > 0 && (
        <div className="mt-2">
          <p className="text-xs font-medium text-gray-500">Suggestions:</p>
          <ul className="text-xs text-gray-600 list-disc list-inside">
            {insight.suggestions.map((s: string, i: number) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
"""


# src/pages/AI/AIStudio.tsx
AI_STUDIO_TSX = """
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../../api/client';

export function AIStudio() {
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState<any>(null);

  const queryMutation = useMutation({
    mutationFn: (q: string) => api.post('/ai/query', { question: q }).then(r => r.data),
    onSuccess: (data) => setResult(data)
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">AI Studio</h1>

      <div className="bg-white rounded-lg shadow p-6">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about your agency data... e.g., 'Which clients are at risk of churning?'"
          className="w-full p-3 border rounded-lg"
          rows={3}
        />
        <button
          onClick={() => queryMutation.mutate(question)}
          disabled={queryMutation.isPending || !question}
          className="mt-3 px-4 py-2 bg-blue-600 text-white rounded"
        >
          {queryMutation.isPending ? 'Analyzing...' : 'Ask AI'}
        </button>
      </div>

      {result && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="font-semibold mb-2">Result</h2>
          <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
"""


# Print the complete UI structure
if __name__ == "__main__":
    print("AGENCY OS Web UI Structure:")
    print("=" * 60)
    for name, content in [
        ("package.json", PACKAGE_JSON),
        ("App.tsx", APP_TSX),
        ("API Client", API_CLIENT),
        ("Dashboard", DASHBOARD_TSX),
        ("Interpret", INTERPRET_TSX),
        ("InterpretationView", INTERPRETATION_VIEW_TSX),
        ("QualityScore", QUALITY_SCORE_TSX),
        ("TagList", TAG_LIST_TSX),
        ("InsightCard", INSIGHT_CARD_TSX),
        ("AI Studio", AI_STUDIO_TSX),
    ]:
        print(f"\n{'─' * 40}")
        print(f"📄 {name}")
        print(f"{'─' * 40}")
        print(content[:200] + "..." if len(content) > 200 else content)