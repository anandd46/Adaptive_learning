/**
 * Main application layout with sidebar navigation.
 * Used for both student and teacher views.
 */
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, BookOpen, Brain, Target, Calendar,
  BarChart3, Star, Settings, LogOut, GraduationCap,
  Users, TrendingUp, FlaskConical, Menu, X, Zap
} from 'lucide-react'
import { useState } from 'react'
import { useAuthStore } from '@/store/authStore'
import { authService } from '@/services/authService'
import { clsx } from 'clsx'

interface AppLayoutProps {
  isTeacher?: boolean
}

const studentNav = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/courses', icon: BookOpen, label: 'Courses' },
  { to: '/learning-path', icon: Target, label: 'Learning Path' },
  { to: '/tutor', icon: Brain, label: 'AI Tutor' },
  { to: '/recommendations', icon: Star, label: 'Recommendations' },
  { to: '/study-plan', icon: Calendar, label: 'Study Plan' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
]

const teacherNav = [
  { to: '/teacher/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/teacher/students', icon: Users, label: 'Students' },
  { to: '/teacher/analytics', icon: TrendingUp, label: 'Analytics' },
  { to: '/teacher/experiments', icon: FlaskConical, label: 'Experiments' },
]

export default function AppLayout({ isTeacher = false }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const navItems = isTeacher ? teacherNav : studentNav

  const handleLogout = () => {
    authService.logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden bg-surface-950">
      {/* ─── Sidebar ──────────────────────────────────────────── */}
      <aside className={clsx(
        'flex flex-col border-r border-surface-700/50 bg-surface-900 transition-all duration-300 shrink-0',
        sidebarOpen ? 'w-64' : 'w-16'
      )}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-surface-700/50">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center shrink-0">
            <Zap size={16} className="text-white" />
          </div>
          {sidebarOpen && (
            <span className="font-bold text-sm text-gradient">AdaptLearn</span>
          )}
          <button
            onClick={() => setSidebarOpen(v => !v)}
            className="ml-auto text-slate-400 hover:text-slate-100 transition-colors"
            aria-label="Toggle sidebar"
          >
            {sidebarOpen ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>

        {/* Role badge */}
        {sidebarOpen && (
          <div className="px-4 py-3">
            <span className={clsx(
              'badge text-xs',
              isTeacher ? 'badge-primary' : 'badge-success'
            )}>
              {isTeacher ? '🎓 Teacher' : '📚 Student'}
            </span>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => clsx(
                'nav-item',
                isActive && 'active',
                !sidebarOpen && 'justify-center px-2'
              )}
              title={!sidebarOpen ? label : undefined}
            >
              <Icon size={18} className="shrink-0" />
              {sidebarOpen && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Footer: user + settings + logout */}
        <div className="px-3 py-3 border-t border-surface-700/50 space-y-1">
          <NavLink
            to={isTeacher ? '/teacher/settings' : '/settings'}
            className={({ isActive }) => clsx('nav-item', isActive && 'active', !sidebarOpen && 'justify-center px-2')}
          >
            <Settings size={18} className="shrink-0" />
            {sidebarOpen && <span>Settings</span>}
          </NavLink>

          {sidebarOpen && (
            <div className="flex items-center gap-2 px-3 py-2 mt-2">
              <div className="w-7 h-7 rounded-lg bg-primary-600 flex items-center justify-center text-xs font-bold text-white shrink-0">
                {user?.email?.[0]?.toUpperCase() ?? 'U'}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-slate-200 truncate">{user?.email}</p>
                <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
              </div>
            </div>
          )}

          <button
            onClick={handleLogout}
            className={clsx('nav-item w-full text-danger-400 hover:text-danger-300 hover:bg-danger-900/20', !sidebarOpen && 'justify-center px-2')}
          >
            <LogOut size={18} className="shrink-0" />
            {sidebarOpen && <span>Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* ─── Main Content ─────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
