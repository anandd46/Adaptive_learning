/**
 * Teacher Dashboard — class overview with at-risk students,
 * knowledge gaps, and engagement trends.
 */
import { Users, AlertTriangle, TrendingUp, BookOpen, BarChart3, Target } from 'lucide-react'

const DEMO_STUDENTS = [
  { name: 'Alice Chen', mastery: 0.82, gap_count: 0, risk: 'low' },
  { name: 'Bob Kumar', mastery: 0.45, gap_count: 3, risk: 'high' },
  { name: 'Carol Davis', mastery: 0.67, gap_count: 1, risk: 'medium' },
  { name: 'Dan Wilson', mastery: 0.21, gap_count: 4, risk: 'critical' },
  { name: 'Eve Martinez', mastery: 0.91, gap_count: 0, risk: 'low' },
]

const DEMO_TOPIC_GAPS = [
  { topic: 'Recursion', gap_count: 4, severity: 'high' },
  { topic: 'Data Structures', gap_count: 3, severity: 'high' },
  { topic: 'OOP', gap_count: 2, severity: 'medium' },
  { topic: 'Functions', gap_count: 1, severity: 'low' },
]

function getRiskBadge(risk: string) {
  switch (risk) {
    case 'critical': return 'badge-danger'
    case 'high': return 'badge-warning'
    case 'medium': return 'badge badge-primary'
    default: return 'badge-success'
  }
}

export default function TeacherDashboardPage() {
  const atRisk = DEMO_STUDENTS.filter(s => s.risk === 'high' || s.risk === 'critical').length
  const avgMastery = DEMO_STUDENTS.reduce((s, st) => s + st.mastery, 0) / DEMO_STUDENTS.length

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Teacher Dashboard</h1>
        <p className="text-slate-400 mt-1">Class overview and student analytics</p>
        <span className="badge badge-warning text-xs mt-2 inline-block">⚠️ DEMO DATA — Synthetic</span>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-primary-500/20 flex items-center justify-center text-primary-400">
            <Users size={22} />
          </div>
          <div>
            <p className="text-xs text-slate-400">Total Students</p>
            <p className="text-xl font-bold">{DEMO_STUDENTS.length}</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-danger-500/20 flex items-center justify-center text-danger-400">
            <AlertTriangle size={22} />
          </div>
          <div>
            <p className="text-xs text-slate-400">At-Risk Students</p>
            <p className="text-xl font-bold text-danger-400">{atRisk}</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-accent-500/20 flex items-center justify-center text-accent-400">
            <BarChart3 size={22} />
          </div>
          <div>
            <p className="text-xs text-slate-400">Avg. Mastery</p>
            <p className="text-xl font-bold">{Math.round(avgMastery * 100)}%</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-warning-500/20 flex items-center justify-center text-warning-400">
            <Target size={22} />
          </div>
          <div>
            <p className="text-xs text-slate-400">Knowledge Gaps</p>
            <p className="text-xl font-bold text-warning-400">10</p>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Student List */}
        <div className="card">
          <h2 className="section-title mb-4">Students Overview</h2>
          <div className="space-y-3">
            {DEMO_STUDENTS.map(({ name, mastery, gap_count, risk }) => (
              <div key={name} className="flex items-center gap-3 p-3 bg-surface-800 rounded-xl">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center text-xs font-bold text-white shrink-0">
                  {name[0]}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-200">{name}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <div className="progress-bar h-1.5 flex-1">
                      <div
                        className={`progress-fill h-full ${mastery >= 0.7 ? 'bg-accent-500' : mastery >= 0.5 ? 'bg-warning-500' : 'bg-danger-500'}`}
                        style={{ width: `${mastery * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-slate-500">{Math.round(mastery * 100)}%</span>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`badge ${getRiskBadge(risk)} text-xs capitalize`}>{risk}</span>
                  {gap_count > 0 && (
                    <p className="text-xs text-slate-500 mt-1">{gap_count} gaps</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Class-wide Knowledge Gaps */}
        <div className="card">
          <h2 className="section-title mb-4">Class Knowledge Gaps</h2>
          <div className="space-y-3">
            {DEMO_TOPIC_GAPS.map(({ topic, gap_count, severity }) => (
              <div key={topic} className="flex items-center justify-between p-3 bg-surface-800 rounded-xl">
                <div className="flex items-center gap-3">
                  <BookOpen size={16} className="text-slate-500" />
                  <span className="text-sm text-slate-200">{topic}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-slate-300">{gap_count} students</span>
                  <span className={`badge text-xs capitalize ${
                    severity === 'high' ? 'badge-danger' : severity === 'medium' ? 'badge-warning' : 'badge-success'
                  }`}>{severity}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
