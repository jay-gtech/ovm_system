import type { ReactNode } from 'react'
export function FormField({ label, children, error }: { label: string; children: ReactNode; error?: string }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-slate-500 mb-1">{label}</label>
      {children}
      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  )
}
