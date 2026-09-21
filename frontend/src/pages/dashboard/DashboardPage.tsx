/**
 * Student Dashboard — main hub showing mastery, today's plan,
 * recommendations, and progress.
 * 
 * NOTE: Currently uses placeholder data. Real data flows in Phase 2+.
 */
import { BarChart3, Target, Brain, Calendar, TrendingUp, Star, AlertTriangle, BookOpen } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

// ─── Placeholder Data (Phase 2 will replace with real API) ───────────────────
const DEMO_MASTERY = [
  { topic: 'Variables', mastery: 0.92, level: 'mastered' },
  { topic: 'Functions', mastery: 0.74, level: 'advanced' },
  { topic: 'Recursion', mastery: 0.38, level: 'beginner' },
  { topic: 'OOP', mastery: 0.65, level: 'intermediate' },
  { topic: 'Data Structures', mastery: 0.21, level: 'beginner' },
]

const DEMO_RECOMMENDATIONS = [
  {
    topic: 'Recursion Basics',
    reason: 'Recent quiz accuracy: 38%. Repeated mistakes in base cases.',
    confidence: 91,
    priority: 1,
    difficulty: 'Beginner',
  },
  {
    topic: 'Stack & Queues',
    reason: 'Low mastery (21%). Required for upcoming topics.',
    confidence: 84,
    priority: 2,
    difficulty: 'Beginner',
  },
]

const DEMO_PLAN = [
  { activity: 'Recursion — Base Cases', duration: 10, type: 'concept', reason: 'Mastery: 38%' },
  { activity: 'Recursion — Practice Problems', duration: 10, type: 'practice', reason: 'Recent accuracy: 38%' },
  { activity: 'Recursion Quiz', duration: 10, type: 'quiz', reason: 'Verify improvement' },
]

// ─── Utility helpers ──────────────────────────────────────────────────────────
function getMasteryColor(mastery: number): string {
  if (mastery >= 0.8) return 'bg-accent-500'
  if (mastery >= 0.5) return 'bg-warning-500'
  return 'bg-danger-500'
}

function getMasteryTextColor(mastery: number): string {
  if (mastery >= 0.8) return 'mastery-strong'
  if (mastery >= 0.5) return 'mastery-moderate'
  return 'mastery-weak'
}

function getActivityIcon(type: string) {
  switch (type) {
    case 'concept': return '📖'
    case 'practice': return '✏️'
    case 'quiz': return '🎯'
    default: return '📚'
  }
}

// ─── Sub-components ───────────────────────────────────────────────────────────
function StatCard({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string; sub?: string }) {
  return (
    <div className="card flex items-center gap-4">
      <div className="w-12 h-12 rounded-xl bg-primary-500/20 flex items-center justify-center text-primary-400 shrink-0">
        {icon}
      </div>
      <div>
        <p className="text-xs text-slate-400 mb-0.5">{label}</p>
        <p className="text-xl font-bold text-slate-100">{value}</p>
        {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { user } = useAuthStore()
  const overallMastery = DEMO_MASTERY.reduce((sum, t) => sum + t.mastery, 0) / DEMO_MASTERY.length

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-fade-in">
      {/* ─── Header ─────────────────────────────────────────── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">
            Good {new Date().getHours() < 12 ? 'morning' : 'afternoon'} 👋
          </h1>
          <p className="text-slate-400 mt-1">
            Here's your personalized learning overview.
          </p>
          <div className="mt-2">
            <span className="badge badge-warning text-xs">⚠️ DEMO DATA — Synthetic</span>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-500">Today</p>
          <p className="text-sm text-slate-300">{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</p>
        </div>
      </div>

      {/* ─── Stat Cards ─────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<BarChart3 size={22} />}
          label="Overall Mastery"
          value={`${Math.round(overallMastery * 100)}%`}
          sub="Across 5 topics"
        />
        <StatCard
          icon={<AlertTriangle size={22} />}
          label="Knowledge Gaps"
          value="2"
          sub="High priority"
        />
        <StatCard
          icon={<TrendingUp size={22} />}
          label="Learning Streak"
          value="5 days"
          sub="Keep it up!"
        />
        <StatCard
          icon={<Star size={22} />}
          label="Quiz Score (avg)"
          value="72%"
          sub="Last 7 days"
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* ─── Topic Mastery ──────────────────────────────── */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="section-title">Topic Mastery</h2>
              <p className="section-subtitle">Your current mastery per topic</p>
            </div>
            <BookOpen size={20} className="text-slate-500" />
          </div>
          <div className="space-y-3">
            {DEMO_MASTERY.map(({ topic, mastery }) => (
              <div key={topic}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-slate-300">{topic}</span>
                  <span className={`text-sm font-semibold ${getMasteryTextColor(mastery)}`}>
                    {Math.round(mastery * 100)}%
                  </span>
                </div>
                <div className="progress-bar h-2">
                  <div
                    className={`progress-fill h-full ${getMasteryColor(mastery)}`}
                    style={{ width: `${mastery * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ─── Today's Study Plan ─────────────────────────── */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="section-title">Today's Plan</h2>
              <p className="section-subtitle">30 minutes • 3 activities</p>
            </div>
            <Calendar size={20} className="text-slate-500" />
          </div>
          <div className="space-y-3">
            {DEMO_PLAN.map(({ activity, duration, type, reason }, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-surface-800 rounded-xl">
                <span className="text-xl">{getActivityIcon(type)}</span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-slate-200 truncate">{activity}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{duration} min • {reason}</p>
                </div>
              </div>
            ))}
          </div>
          <button className="btn-primary w-full mt-4 flex items-center justify-center gap-2 text-sm py-2.5">
            <Target size={16} />
            Start Learning
          </button>
        </div>
      </div>

      {/* ─── Personalized Recommendations ──────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="section-title">What should I learn next?</h2>
            <p className="section-subtitle">Personalized recommendations based on your gaps</p>
          </div>
          <Brain size={20} className="text-slate-500" />
        </div>
        <div className="grid sm:grid-cols-2 gap-4">
          {DEMO_RECOMMENDATIONS.map(({ topic, reason, confidence, priority, difficulty }) => (
            <div key={topic} className="card-hover group">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <span className="badge badge-danger text-xs mb-2">Priority #{priority}</span>
                  <h3 className="font-semibold text-slate-100">{topic}</h3>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500 mb-1">Confidence</p>
                  <p className="text-lg font-bold text-accent-400">{confidence}%</p>
                </div>
              </div>

              {/* WHY recommendation */}
              <div className="p-3 bg-primary-500/10 rounded-xl border border-primary-500/20 mb-3">
                <p className="text-xs font-medium text-primary-300 mb-1">Why recommended?</p>
                <p className="text-xs text-slate-400">{reason}</p>
              </div>

              <div className="flex items-center justify-between">
                <span className="badge badge-warning text-xs">{difficulty}</span>
                <button className="text-xs text-primary-400 hover:text-primary-300 font-medium transition-colors group-hover:underline">
                  Start → 
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
