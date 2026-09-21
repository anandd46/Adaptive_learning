/**
 * Login page with email/password form.
 * Links to registration page.
 */
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { Eye, EyeOff, Zap, ArrowRight } from 'lucide-react'
import { authService } from '@/services/authService'
import { useAuthStore } from '@/store/authStore'

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginForm) => {
    setLoading(true)
    try {
      const response = await authService.login(data)
      setAuth(response.access_token, response.refresh_token, {
        id: response.user_id,
        email: data.email,
        role: response.role as 'student' | 'teacher',
      })
      toast.success('Welcome back!')
      navigate(response.role === 'teacher' ? '/teacher/dashboard' : '/dashboard')
    } catch (err: any) {
      const msg = err?.response?.data?.error?.message || 'Invalid credentials'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-950 flex">
      {/* ─── Left Panel — Hero ──────────────────────────────────── */}
      <div className="hidden lg:flex flex-col w-[55%] bg-hero-gradient relative overflow-hidden p-12">
        {/* Decorative circles */}
        <div className="absolute -top-32 -right-32 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-32 -left-32 w-96 h-96 bg-accent-500/20 rounded-full blur-3xl" />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-16">
            <div className="w-10 h-10 bg-white/10 backdrop-blur rounded-xl flex items-center justify-center">
              <Zap size={20} className="text-primary-300" />
            </div>
            <span className="text-xl font-bold text-white">AdaptLearn</span>
          </div>

          <h1 className="text-5xl font-bold text-white leading-tight mb-6">
            Learning that{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-300 to-accent-300">
              adapts to you
            </span>
          </h1>
          <p className="text-slate-300 text-lg leading-relaxed max-w-md">
            AI-powered personalized education that identifies your knowledge gaps,
            adapts to your level, and explains every recommendation.
          </p>

          <div className="mt-12 space-y-4">
            {[
              { icon: '🎯', label: 'Identifies your exact knowledge gaps' },
              { icon: '🤖', label: 'AI tutor adapts to your mastery level' },
              { icon: '💡', label: 'Explains why each topic was recommended' },
            ].map(({ icon, label }) => (
              <div key={label} className="flex items-center gap-3">
                <span className="text-2xl">{icon}</span>
                <span className="text-slate-300">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ─── Right Panel — Login Form ──────────────────────────── */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center">
              <Zap size={16} className="text-white" />
            </div>
            <span className="font-bold text-gradient">AdaptLearn</span>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-slate-100 mb-1">Welcome back</h2>
            <p className="text-slate-400">Sign in to continue your learning journey</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
            <div>
              <label className="label" htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                className="input"
                {...register('email')}
              />
              {errors.email && (
                <p className="mt-1 text-xs text-danger-400">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label className="label" htmlFor="password">Password</label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="input pr-11"
                  {...register('password')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-xs text-danger-400">{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 py-3"
              id="login-submit-button"
            >
              {loading ? (
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  Sign in <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-400">
            Don't have an account?{' '}
            <Link to="/register" className="text-primary-400 hover:text-primary-300 font-medium transition-colors">
              Create one
            </Link>
          </p>

          {/* Demo credentials hint (development only) */}
          <div className="mt-8 p-4 card-sm text-xs text-slate-500">
            <p className="font-medium text-slate-400 mb-1">🧪 Demo Credentials</p>
            <p>Student: student@demo.com / demo123456</p>
            <p>Teacher: teacher@demo.com / demo123456</p>
          </div>
        </div>
      </div>
    </div>
  )
}
