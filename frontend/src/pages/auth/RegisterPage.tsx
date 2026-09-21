/**
 * Registration page for both students and teachers.
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
import { clsx } from 'clsx'

const registerSchema = z.object({
  full_name: z.string().min(2, 'Full name must be at least 2 characters'),
  email: z.string().email('Please enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  role: z.enum(['student', 'teacher']),
  grade_level: z.string().optional(),
})

type RegisterForm = z.infer<typeof registerSchema>

export default function RegisterPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { role: 'student' },
  })

  const selectedRole = watch('role')

  const onSubmit = async (data: RegisterForm) => {
    setLoading(true)
    try {
      const response = await authService.register(data)
      setAuth(response.access_token, response.refresh_token, {
        id: response.user_id,
        email: data.email,
        role: response.role as 'student' | 'teacher',
      })
      toast.success('Account created! Welcome to AdaptLearn.')
      navigate(response.role === 'teacher' ? '/teacher/dashboard' : '/dashboard')
    } catch (err: any) {
      const msg = err?.response?.data?.error?.message || 'Registration failed'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-950 flex items-center justify-center p-8">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center gap-2 mb-8">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center">
            <Zap size={16} className="text-white" />
          </div>
          <span className="font-bold text-gradient">AdaptLearn</span>
        </div>

        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Create your account</h1>
          <p className="text-slate-400">Start your personalized learning journey today</p>
        </div>

        {/* Role selector */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {(['student', 'teacher'] as const).map((role) => (
            <label
              key={role}
              className={clsx(
                'flex flex-col items-center gap-2 p-4 rounded-xl border cursor-pointer transition-all',
                selectedRole === role
                  ? 'border-primary-500 bg-primary-500/10 text-primary-300'
                  : 'border-surface-600/50 bg-surface-800 text-slate-400 hover:border-surface-500'
              )}
            >
              <input type="radio" value={role} className="sr-only" {...register('role')} />
              <span className="text-2xl">{role === 'student' ? '📚' : '🎓'}</span>
              <span className="text-sm font-medium capitalize">{role}</span>
            </label>
          ))}
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div>
            <label className="label" htmlFor="full-name">Full name</label>
            <input
              id="full-name"
              type="text"
              autoComplete="name"
              placeholder="Your full name"
              className="input"
              {...register('full_name')}
            />
            {errors.full_name && (
              <p className="mt-1 text-xs text-danger-400">{errors.full_name.message}</p>
            )}
          </div>

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
            <label className="label" htmlFor="register-password">Password</label>
            <div className="relative">
              <input
                id="register-password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder="Minimum 8 characters"
                className="input pr-11"
                {...register('password')}
              />
              <button
                type="button"
                onClick={() => setShowPassword(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors"
                aria-label="Toggle password visibility"
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
            id="register-submit-button"
          >
            {loading ? (
              <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                Create account <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="text-primary-400 hover:text-primary-300 font-medium transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
