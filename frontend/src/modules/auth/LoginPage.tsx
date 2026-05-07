import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Input } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { authApi } from '../../api/auth'
import { useAuthStore } from '../../store/authStore'

const schema = z.object({
  organization_slug: z.string().min(1, 'Organization workspace is required'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
})
type FormValues = z.infer<typeof schema>

export default function LoginPage() {
  const navigate = useNavigate()
  const { token, setAuth } = useAuthStore()
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  if (token) return <Navigate to="/" replace />

  const onSubmit = async (data: FormValues) => {
    setServerError(null)
    try {
      const res = await authApi.login(data)
      setAuth(res.user, res.access_token)
      navigate('/', { replace: true })
    } catch {
      setServerError('Invalid credentials. Please check your workspace, email, and password.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="text-3xl font-bold tracking-tight">
            <span className="text-slate-900">OVM</span>
            <span className="text-brand-600">System</span>
          </div>
          <p className="mt-2 text-sm text-slate-500">Sign in to your account</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
            <div>
              <label htmlFor="organization_slug" className="mb-1.5 block text-sm font-medium text-slate-700">
                Workspace
              </label>
              <Input
                id="organization_slug"
                type="text"
                autoComplete="organization"
                placeholder="your-company"
                {...register('organization_slug')}
              />
              {errors.organization_slug && (
                <p className="mt-1 text-xs text-red-500">{errors.organization_slug.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-slate-700">
                Email address
              </label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@company.com"
                {...register('email')}
              />
              {errors.email && (
                <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-slate-700">
                Password
              </label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                {...register('password')}
              />
              {errors.password && (
                <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>
              )}
            </div>

            {serverError && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-600">
                {serverError}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
