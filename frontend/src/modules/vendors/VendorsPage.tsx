import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Star, Edit2, PowerOff } from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Button } from '../../components/ui/Button'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Card, CardContent } from '../../components/ui/Card'
import { Modal } from '../../components/ui/Modal'
import { Loader } from '../../components/feedback/Loader'
import { ErrorState } from '../../components/feedback/ErrorState'
import { EmptyState } from '../../components/feedback/EmptyState'
import { vendorsApi, type VendorCreatePayload, type VendorUpdatePayload } from '../../api/vendors'
import { formatINR } from '../../utils/format'
import type { Vendor } from '../../types'

const VENDOR_KEYS = {
  all: ['vendors'] as const,
}

// ---- form helpers ----

function LabeledInput({ label, ...props }: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-slate-600">{label}</label>
      <input
        className="h-9 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm outline-none focus:border-brand-400 focus:ring-1 focus:ring-brand-100"
        {...props}
      />
    </div>
  )
}

function getApiErrorMessage(error: unknown): string {
  const e = error as { response?: { data?: { detail?: string } } }
  return e?.response?.data?.detail ?? 'An unexpected error occurred. Please try again.'
}

// ---- vendor form modal ----

interface VendorFormModalProps {
  open: boolean
  onClose: () => void
  editing?: Vendor | null
}

function VendorFormModal({ open, onClose, editing }: VendorFormModalProps) {
  const qc = useQueryClient()
  const isEdit = !!editing

  const [form, setForm] = useState({
    vendor_code: '',
    legal_name: editing?.legal_name ?? '',
    display_name: editing?.name ?? '',
    tax_id: editing?.gstin ?? '',
    email: editing?.email ?? '',
    phone: editing?.phone ?? '',
    address: editing?.city ?? '',
  })

  const createMutation = useMutation({
    mutationFn: (data: VendorCreatePayload) => vendorsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: VENDOR_KEYS.all })
      onClose()
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: VendorUpdatePayload) => vendorsApi.update(editing!.id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: VENDOR_KEYS.all })
      onClose()
    },
  })

  const isPending = createMutation.isPending || updateMutation.isPending
  const error = createMutation.error || updateMutation.error

  function field(name: keyof typeof form) {
    return {
      value: form[name],
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
        setForm(prev => ({ ...prev, [name]: e.target.value })),
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (isEdit) {
      updateMutation.mutate({
        legal_name: form.legal_name || undefined,
        display_name: form.display_name || undefined,
        tax_id: form.tax_id || undefined,
        email: form.email || undefined,
        phone: form.phone || undefined,
        address: form.address || undefined,
      })
    } else {
      createMutation.mutate({
        vendor_code: form.vendor_code,
        legal_name: form.legal_name,
        display_name: form.display_name,
        tax_id: form.tax_id || undefined,
        email: form.email || undefined,
        phone: form.phone || undefined,
        address: form.address || undefined,
      })
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? 'Edit Vendor' : 'Add Vendor'}>
      <form onSubmit={handleSubmit} className="space-y-3">
        {!isEdit && (
          <LabeledInput label="Vendor Code *" placeholder="e.g. VND-001" required {...field('vendor_code')} />
        )}
        <LabeledInput label="Legal Name *" placeholder="Full registered name" required {...field('legal_name')} />
        <LabeledInput label="Display Name *" placeholder="Short name shown in UI" required {...field('display_name')} />
        <LabeledInput label="Tax ID / GSTIN" placeholder="e.g. 22AAAAA0000A1Z5" {...field('tax_id')} />
        <LabeledInput label="Email" type="email" placeholder="contact@vendor.com" {...field('email')} />
        <LabeledInput label="Phone" placeholder="+91 98765 43210" {...field('phone')} />
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-slate-600">Address</label>
          <textarea
            rows={2}
            placeholder="Full address"
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-1 focus:ring-brand-100 resize-none"
            {...field('address')}
          />
        </div>
        {error && (
          <p className="rounded-lg bg-red-50 border border-red-100 px-3 py-2 text-xs text-red-600">
            {getApiErrorMessage(error)}
          </p>
        )}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose} disabled={isPending}>
            Cancel
          </Button>
          <Button type="submit" disabled={isPending}>
            {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Vendor'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

// ---- score bar ----

function ScoreBar({ score }: { score: number }) {
  const pct = (score / 5) * 100
  const color = score >= 4.5 ? 'bg-green-500' : score >= 3.5 ? 'bg-amber-400' : 'bg-red-400'
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 rounded-full bg-slate-100 overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-semibold text-slate-700">{score > 0 ? score.toFixed(1) : '—'}</span>
    </div>
  )
}

// ---- main page ----

export default function VendorsPage() {
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('ALL')
  const [view, setView] = useState<'table' | 'card'>('table')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingVendor, setEditingVendor] = useState<Vendor | null>(null)

  const qc = useQueryClient()

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: VENDOR_KEYS.all,
    queryFn: () => vendorsApi.list({ limit: 100 }),
  })

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => vendorsApi.deactivate(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: VENDOR_KEYS.all }),
  })

  const vendors = data?.items ?? []
  const total = data?.total ?? 0

  const filtered = vendors.filter(v => {
    const q = search.toLowerCase()
    const matchSearch = !q ||
      v.name.toLowerCase().includes(q) ||
      v.gstin.toLowerCase().includes(q) ||
      v.city.toLowerCase().includes(q)
    const matchStatus = filterStatus === 'ALL' || v.status === filterStatus
    return matchSearch && matchStatus
  })

  function openCreate() {
    setEditingVendor(null)
    setModalOpen(true)
  }

  function openEdit(v: Vendor) {
    setEditingVendor(v)
    setModalOpen(true)
  }

  function handleDeactivate(v: Vendor) {
    if (window.confirm(`Deactivate "${v.name}"? This will set their status to Inactive.`)) {
      deactivateMutation.mutate(v.id)
    }
  }

  if (isLoading) {
    return <Loader label="Loading vendors…" className="py-32" />
  }

  if (isError) {
    return (
      <ErrorState
        title="Failed to load vendors"
        message="Could not reach the vendor service. Please check your connection and try again."
        onRetry={() => refetch()}
      />
    )
  }

  return (
    <div className="space-y-5">
      {/* Modal — keyed so it remounts (and resets form) on each open/edit switch */}
      <VendorFormModal
        key={`${modalOpen}-${editingVendor?.id ?? 'new'}`}
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editing={editingVendor}
      />

      <PageHeader
        title="Vendors"
        subtitle={`${total} vendors — ${vendors.filter(v => v.status === 'ACTIVE').length} active`}
        actions={
          <Button className="gap-2" onClick={openCreate}>
            <Plus size={16} /> Add Vendor
          </Button>
        }
      />

      {/* Summary cards */}
      <div className="grid gap-3 sm:grid-cols-4">
        {[
          { label: 'Active',      count: vendors.filter(v => v.status === 'ACTIVE').length,      color: 'text-green-600 bg-green-50 border-green-100' },
          { label: 'Pending KYC', count: vendors.filter(v => v.status === 'PENDING_KYC').length, color: 'text-amber-600 bg-amber-50 border-amber-100' },
          { label: 'Suspended',   count: vendors.filter(v => v.status === 'SUSPENDED').length,   color: 'text-red-600 bg-red-50 border-red-100' },
          { label: 'Total Value', count: `₹${(vendors.reduce((a, v) => a + v.totalValue, 0) / 10_000_000).toFixed(1)}Cr`, color: 'text-brand-600 bg-brand-50 border-brand-100' },
        ].map(s => (
          <div key={s.label} className={`rounded-xl border px-4 py-3 ${s.color}`}>
            <p className="text-xs font-medium opacity-70">{s.label}</p>
            <p className="text-2xl font-bold mt-0.5">{s.count}</p>
          </div>
        ))}
      </div>

      <Card>
        {/* Toolbar */}
        <div className="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative flex-1 max-w-xs">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search vendors…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="h-9 w-full rounded-lg border border-slate-200 bg-slate-50 pl-8 pr-3 text-sm outline-none focus:border-brand-400 focus:ring-1 focus:ring-brand-100"
            />
          </div>
          <div className="flex items-center gap-2">
            <select
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-brand-400"
            >
              {['ALL', 'ACTIVE', 'PENDING_KYC', 'SUSPENDED', 'INACTIVE'].map(s => (
                <option key={s} value={s}>{s === 'ALL' ? 'All Statuses' : s.replace(/_/g, ' ')}</option>
              ))}
            </select>
            <div className="flex rounded-lg border border-slate-200 overflow-hidden">
              <button
                onClick={() => setView('table')}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${view === 'table' ? 'bg-brand-600 text-white' : 'text-slate-500 hover:bg-slate-50'}`}
              >
                Table
              </button>
              <button
                onClick={() => setView('card')}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${view === 'card' ? 'bg-brand-600 text-white' : 'text-slate-500 hover:bg-slate-50'}`}
              >
                Cards
              </button>
            </div>
          </div>
        </div>

        <CardContent className="p-0">
          {/* Empty state — no vendors at all */}
          {vendors.length === 0 ? (
            <EmptyState
              title="No vendors yet"
              description="Add your first vendor to start managing your supply chain."
              action={
                <Button onClick={openCreate} className="gap-2">
                  <Plus size={14} /> Add Vendor
                </Button>
              }
            />
          ) : view === 'table' ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50">
                    {['Vendor', 'Tax ID', 'Address', 'Reliability', 'On-Time %', 'Total Value', 'Orders', 'Status', ''].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {filtered.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="px-4 py-16 text-center text-sm text-slate-400">
                        No vendors match your filters.
                      </td>
                    </tr>
                  ) : filtered.map(v => (
                    <tr key={v.id} className="hover:bg-slate-50/60">
                      <td className="px-4 py-3">
                        <p className="font-semibold text-slate-800">{v.name}</p>
                        <p className="text-[11px] text-slate-400">{v.email || '—'}</p>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">{v.gstin || '—'}</td>
                      <td className="px-4 py-3 text-slate-600 max-w-[140px] truncate text-xs">{v.city || '—'}</td>
                      <td className="px-4 py-3"><ScoreBar score={v.reliabilityScore} /></td>
                      <td className="px-4 py-3">
                        <span className={`text-sm font-semibold ${v.onTimeDeliveryRate >= 90 ? 'text-green-600' : v.onTimeDeliveryRate >= 75 ? 'text-amber-600' : v.onTimeDeliveryRate > 0 ? 'text-red-500' : 'text-slate-300'}`}>
                          {v.onTimeDeliveryRate > 0 ? `${v.onTimeDeliveryRate}%` : '—'}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-900 tabular-nums whitespace-nowrap">
                        {v.totalValue > 0 ? formatINR(v.totalValue) : '—'}
                      </td>
                      <td className="px-4 py-3 text-slate-600 tabular-nums">{v.totalOrders || '—'}</td>
                      <td className="px-4 py-3"><StatusBadge status={v.status} /></td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => openEdit(v)}
                            className="rounded-md border border-slate-200 p-1.5 text-slate-400 hover:border-brand-300 hover:text-brand-600 transition-colors"
                            title="Edit vendor"
                          >
                            <Edit2 size={11} />
                          </button>
                          {v.status !== 'INACTIVE' && (
                            <button
                              onClick={() => handleDeactivate(v)}
                              disabled={deactivateMutation.isPending}
                              className="rounded-md border border-slate-200 p-1.5 text-slate-400 hover:border-red-300 hover:text-red-500 transition-colors disabled:opacity-50"
                              title="Deactivate vendor"
                            >
                              <PowerOff size={11} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            /* Card view */
            <div className="grid gap-4 p-4 sm:grid-cols-2 xl:grid-cols-3">
              {filtered.map(v => (
                <div key={v.id} className="rounded-xl border border-slate-200 bg-white p-4 hover:border-brand-200 hover:shadow-sm transition-all">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-100 text-brand-700 font-bold text-sm shrink-0">
                      {v.name.slice(0, 2).toUpperCase()}
                    </div>
                    <StatusBadge status={v.status} />
                  </div>
                  <p className="font-semibold text-slate-800 leading-tight">{v.name}</p>
                  <p className="text-xs text-slate-400 mt-0.5 truncate">
                    {v.city ? `${v.city} · ` : ''}{v.gstin || 'No Tax ID'}
                  </p>
                  <div className="mt-3 grid grid-cols-3 gap-2 border-t border-slate-100 pt-3">
                    <div className="text-center">
                      <p className="text-[10px] text-slate-400 uppercase font-medium">Score</p>
                      <p className="flex items-center justify-center gap-0.5 text-sm font-bold text-slate-700 mt-0.5">
                        <Star size={11} className="text-amber-400 fill-amber-400" />
                        {v.reliabilityScore > 0 ? v.reliabilityScore : '—'}
                      </p>
                    </div>
                    <div className="text-center border-x border-slate-100">
                      <p className="text-[10px] text-slate-400 uppercase font-medium">On-Time</p>
                      <p className={`text-sm font-bold mt-0.5 ${v.onTimeDeliveryRate >= 90 ? 'text-green-600' : v.onTimeDeliveryRate >= 75 ? 'text-amber-500' : v.onTimeDeliveryRate > 0 ? 'text-red-500' : 'text-slate-300'}`}>
                        {v.onTimeDeliveryRate > 0 ? `${v.onTimeDeliveryRate}%` : '—'}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-[10px] text-slate-400 uppercase font-medium">Orders</p>
                      <p className="text-sm font-bold text-slate-700 mt-0.5">{v.totalOrders || '—'}</p>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <div>
                      <p className="text-[10px] text-slate-400">Total Value</p>
                      <p className="text-sm font-bold text-slate-800">
                        {v.totalValue > 0 ? formatINR(v.totalValue) : '—'}
                      </p>
                    </div>
                    <div className="flex gap-1">
                      <button
                        onClick={() => openEdit(v)}
                        className="rounded-lg border border-brand-200 px-3 py-1.5 text-xs font-medium text-brand-600 hover:bg-brand-50 transition-colors"
                      >
                        Edit
                      </button>
                      {v.status !== 'INACTIVE' && (
                        <button
                          onClick={() => handleDeactivate(v)}
                          disabled={deactivateMutation.isPending}
                          className="rounded-lg border border-red-200 px-2 py-1.5 text-xs font-medium text-red-500 hover:bg-red-50 transition-colors disabled:opacity-50"
                        >
                          Deactivate
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Footer count */}
          <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3">
            <p className="text-xs text-slate-400">
              Showing {filtered.length} of {total} vendor{total !== 1 ? 's' : ''}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
