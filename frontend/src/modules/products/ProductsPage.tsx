import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Edit2, ToggleLeft, ToggleRight } from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Button } from '../../components/ui/Button'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Card, CardContent } from '../../components/ui/Card'
import { Modal } from '../../components/ui/Modal'
import { Loader } from '../../components/feedback/Loader'
import { ErrorState } from '../../components/feedback/ErrorState'
import { EmptyState } from '../../components/feedback/EmptyState'
import {
  productsApi,
  type Product,
  type ProductCreatePayload,
  type ProductUpdatePayload,
  type ProductStatus,
} from '../../api/products'
import { vendorsApi } from '../../api/vendors'

// Shared with VendorsPage — same key = same cache entry
const PRODUCT_KEYS = { all: ['products'] as const }
const VENDOR_KEYS  = { all: ['vendors']  as const }

function getApiErrorMessage(error: unknown): string {
  const e = error as { response?: { data?: { detail?: string } } }
  return e?.response?.data?.detail ?? 'An unexpected error occurred. Please try again.'
}

function formatPrice(amount: number, currency: string): string {
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      maximumFractionDigits: 2,
    }).format(amount)
  } catch {
    return `${currency} ${amount.toFixed(2)}`
  }
}

// ---- shared input helper ----

function LabeledInput({
  label,
  ...props
}: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
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

// ---- product form modal ----

interface ProductFormModalProps {
  open: boolean
  onClose: () => void
  editing?: Product | null
}

function ProductFormModal({ open, onClose, editing }: ProductFormModalProps) {
  const qc = useQueryClient()
  const isEdit = !!editing

  // Reuse the cached vendor list — no extra network request if already fetched
  const { data: vendorData } = useQuery({
    queryKey: VENDOR_KEYS.all,
    queryFn: () => vendorsApi.list({ limit: 200 }),
  })
  const vendors = vendorData?.items ?? []

  const [form, setForm] = useState({
    sku:         '',
    name:        editing?.name        ?? '',
    description: editing?.description ?? '',
    category:    editing?.category    ?? '',
    unit_price:  editing?.unitPrice != null ? String(editing.unitPrice) : '',
    currency:    editing?.currency    ?? 'USD',
    vendor_id:   editing?.vendor_id   ?? '',
    notes:       editing?.notes       ?? '',
  })

  const createMutation = useMutation({
    mutationFn: (data: ProductCreatePayload) => productsApi.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: PRODUCT_KEYS.all }); onClose() },
  })

  const updateMutation = useMutation({
    mutationFn: (data: ProductUpdatePayload) => productsApi.update(editing!.id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: PRODUCT_KEYS.all }); onClose() },
  })

  const isPending = createMutation.isPending || updateMutation.isPending
  const error     = createMutation.error     || updateMutation.error

  function field(name: keyof typeof form) {
    return {
      value: form[name],
      onChange: (
        e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
      ) => setForm(prev => ({ ...prev, [name]: e.target.value })),
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const unitPrice = parseFloat(form.unit_price)
    if (isNaN(unitPrice) || unitPrice <= 0) return

    if (isEdit) {
      updateMutation.mutate({
        name:        form.name        || undefined,
        description: form.description || undefined,
        category:    form.category    || undefined,
        unit_price:  unitPrice,
        currency:    form.currency    || undefined,
        vendor_id:   form.vendor_id   || null,
        notes:       form.notes       || undefined,
      })
    } else {
      createMutation.mutate({
        sku:         form.sku,
        name:        form.name,
        description: form.description || undefined,
        category:    form.category    || undefined,
        unit_price:  unitPrice,
        currency:    form.currency    || 'USD',
        vendor_id:   form.vendor_id   || undefined,
        notes:       form.notes       || undefined,
      })
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={isEdit ? 'Edit Product' : 'Add Product'}>
      <form onSubmit={handleSubmit} className="space-y-3">
        {!isEdit && (
          <LabeledInput
            label="SKU *"
            placeholder="e.g. PRD-001"
            required
            {...field('sku')}
          />
        )}
        {isEdit && (
          <div className="rounded-lg bg-slate-50 border border-slate-200 px-3 py-2 text-xs text-slate-500">
            SKU: <span className="font-mono font-semibold text-slate-700">{editing?.sku}</span>
            <span className="ml-2 text-slate-400">(immutable)</span>
          </div>
        )}

        <LabeledInput
          label="Name *"
          placeholder="Product name"
          required
          {...field('name')}
        />

        <div className="grid grid-cols-2 gap-3">
          <LabeledInput
            label="Unit Price *"
            type="number"
            step="0.01"
            min="0.01"
            placeholder="0.00"
            required
            {...field('unit_price')}
          />
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-600">Currency</label>
            <select
              className="h-9 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm outline-none focus:border-brand-400"
              {...field('currency')}
            >
              <option value="USD">USD</option>
              <option value="INR">INR</option>
              <option value="EUR">EUR</option>
              <option value="GBP">GBP</option>
            </select>
          </div>
        </div>

        <LabeledInput
          label="Category"
          placeholder="e.g. Raw Materials"
          {...field('category')}
        />

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-slate-600">Vendor (optional)</label>
          <select
            className="h-9 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm outline-none focus:border-brand-400"
            {...field('vendor_id')}
          >
            <option value="">— No vendor —</option>
            {vendors
              .filter(v => v.status === 'ACTIVE')
              .map(v => (
                <option key={v.id} value={v.id}>{v.name}</option>
              ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-slate-600">Description</label>
          <textarea
            rows={2}
            placeholder="Product description"
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-1 focus:ring-brand-100 resize-none"
            {...field('description')}
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
            {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Product'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

// ---- main page ----

export default function ProductsPage() {
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState<'ALL' | ProductStatus>('ALL')
  const [view, setView] = useState<'table' | 'card'>('table')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)

  const qc = useQueryClient()

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: PRODUCT_KEYS.all,
    queryFn: () => productsApi.list({ limit: 200 }),
  })

  // Vendor list for name resolution in table — shares cache with VendorsPage
  const { data: vendorData } = useQuery({
    queryKey: VENDOR_KEYS.all,
    queryFn: () => vendorsApi.list({ limit: 200 }),
  })

  const vendorMap = new Map((vendorData?.items ?? []).map(v => [v.id, v.name]))

  const toggleStatusMutation = useMutation({
    mutationFn: ({ id, current }: { id: string; current: ProductStatus }) =>
      productsApi.setStatus(id, current === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'),
    onSuccess: () => qc.invalidateQueries({ queryKey: PRODUCT_KEYS.all }),
  })

  const products = data?.items ?? []
  const total    = data?.total ?? 0

  const filtered = products.filter(p => {
    const q = search.toLowerCase()
    const matchSearch =
      !q ||
      p.name.toLowerCase().includes(q) ||
      p.sku.toLowerCase().includes(q) ||
      (p.category ?? '').toLowerCase().includes(q)
    const matchStatus = filterStatus === 'ALL' || p.status === filterStatus
    return matchSearch && matchStatus
  })

  const activeCount   = products.filter(p => p.status === 'ACTIVE').length
  const inactiveCount = products.filter(p => p.status === 'INACTIVE').length
  const avgPrice      =
    products.length > 0
      ? products.reduce((sum, p) => sum + p.unitPrice, 0) / products.length
      : 0

  function openCreate() {
    setEditingProduct(null)
    setModalOpen(true)
  }

  function openEdit(p: Product) {
    setEditingProduct(p)
    setModalOpen(true)
  }

  function handleToggleStatus(p: Product) {
    const label = p.status === 'ACTIVE' ? 'Deactivate' : 'Activate'
    if (window.confirm(`${label} "${p.name}"?`)) {
      toggleStatusMutation.mutate({ id: p.id, current: p.status })
    }
  }

  if (isLoading) return <Loader label="Loading products…" className="py-32" />

  if (isError)
    return (
      <ErrorState
        title="Failed to load products"
        message="Could not reach the product service. Please check your connection and try again."
        onRetry={() => refetch()}
      />
    )

  return (
    <div className="space-y-5">
      {/* Keyed so the form resets fully on each open/edit switch */}
      <ProductFormModal
        key={`${modalOpen}-${editingProduct?.id ?? 'new'}`}
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editing={editingProduct}
      />

      <PageHeader
        title="Products"
        subtitle={`${total} product${total !== 1 ? 's' : ''} in catalog`}
        actions={
          <Button className="gap-2" onClick={openCreate}>
            <Plus size={16} /> Add Product
          </Button>
        }
      />

      {/* Summary cards */}
      <div className="grid gap-3 sm:grid-cols-4">
        {[
          {
            label: 'Active',
            count: activeCount,
            color: 'text-green-600 bg-green-50 border-green-100',
          },
          {
            label: 'Inactive',
            count: inactiveCount,
            color: 'text-slate-600 bg-slate-50 border-slate-200',
          },
          {
            label: 'Total SKUs',
            count: total,
            color: 'text-brand-600 bg-brand-50 border-brand-100',
          },
          {
            label: 'Avg Unit Price',
            count:
              avgPrice > 0
                ? new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                    maximumFractionDigits: 0,
                  }).format(avgPrice)
                : '—',
            color: 'text-indigo-600 bg-indigo-50 border-indigo-100',
          },
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
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              type="text"
              placeholder="Search name, SKU, category…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="h-9 w-full rounded-lg border border-slate-200 bg-slate-50 pl-8 pr-3 text-sm outline-none focus:border-brand-400 focus:ring-1 focus:ring-brand-100"
            />
          </div>
          <div className="flex items-center gap-2">
            <select
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value as 'ALL' | ProductStatus)}
              className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-brand-400"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
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
          {products.length === 0 ? (
            <EmptyState
              title="No products yet"
              description="Add your first product to build your catalog."
              action={
                <Button onClick={openCreate} className="gap-2">
                  <Plus size={14} /> Add Product
                </Button>
              }
            />
          ) : view === 'table' ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50">
                    {['Product', 'SKU', 'Category', 'Unit Price', 'Vendor', 'Status', ''].map(
                      h => (
                        <th
                          key={h}
                          className="px-4 py-3 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap"
                        >
                          {h}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {filtered.length === 0 ? (
                    <tr>
                      <td
                        colSpan={7}
                        className="px-4 py-16 text-center text-sm text-slate-400"
                      >
                        No products match your filters.
                      </td>
                    </tr>
                  ) : (
                    filtered.map(p => (
                      <tr key={p.id} className="hover:bg-slate-50/60">
                        <td className="px-4 py-3">
                          <p className="font-semibold text-slate-800">{p.name}</p>
                          {p.description && (
                            <p className="text-[11px] text-slate-400 truncate max-w-[200px]">
                              {p.description}
                            </p>
                          )}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-slate-500">
                          {p.sku}
                        </td>
                        <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                          {p.category || '—'}
                        </td>
                        <td className="px-4 py-3 font-semibold text-slate-900 tabular-nums whitespace-nowrap">
                          {formatPrice(p.unitPrice, p.currency)}
                        </td>
                        <td className="px-4 py-3 text-slate-600 text-xs">
                          {p.vendor_id
                            ? (vendorMap.get(p.vendor_id) ?? '—')
                            : '—'}
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge status={p.status} />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => openEdit(p)}
                              className="rounded-md border border-slate-200 p-1.5 text-slate-400 hover:border-brand-300 hover:text-brand-600 transition-colors"
                              title="Edit product"
                            >
                              <Edit2 size={11} />
                            </button>
                            <button
                              onClick={() => handleToggleStatus(p)}
                              disabled={toggleStatusMutation.isPending}
                              className={`rounded-md border p-1.5 transition-colors disabled:opacity-50 ${
                                p.status === 'ACTIVE'
                                  ? 'border-slate-200 text-slate-400 hover:border-red-300 hover:text-red-500'
                                  : 'border-slate-200 text-slate-400 hover:border-green-300 hover:text-green-600'
                              }`}
                              title={p.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
                            >
                              {p.status === 'ACTIVE' ? (
                                <ToggleRight size={11} />
                              ) : (
                                <ToggleLeft size={11} />
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          ) : (
            /* Card view */
            <div className="grid gap-4 p-4 sm:grid-cols-2 xl:grid-cols-3">
              {filtered.map(p => (
                <div
                  key={p.id}
                  className="rounded-xl border border-slate-200 bg-white p-4 hover:border-brand-200 hover:shadow-sm transition-all"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-100 text-brand-700 font-bold text-sm shrink-0">
                      {p.name.slice(0, 2).toUpperCase()}
                    </div>
                    <StatusBadge status={p.status} />
                  </div>
                  <p className="font-semibold text-slate-800 leading-tight">{p.name}</p>
                  <p className="text-xs font-mono text-slate-400 mt-0.5">{p.sku}</p>
                  {p.category && (
                    <p className="text-xs text-slate-400 mt-0.5">{p.category}</p>
                  )}
                  <div className="mt-3 border-t border-slate-100 pt-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-[10px] text-slate-400 uppercase font-medium">
                          Unit Price
                        </p>
                        <p className="text-lg font-bold text-slate-800 mt-0.5">
                          {formatPrice(p.unitPrice, p.currency)}
                        </p>
                      </div>
                      {p.vendor_id && vendorMap.has(p.vendor_id) && (
                        <div className="text-right">
                          <p className="text-[10px] text-slate-400 uppercase font-medium">
                            Vendor
                          </p>
                          <p className="text-xs font-medium text-slate-600 mt-0.5 max-w-[100px] truncate">
                            {vendorMap.get(p.vendor_id)}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="mt-3 flex gap-1">
                    <button
                      onClick={() => openEdit(p)}
                      className="flex-1 rounded-lg border border-brand-200 py-1.5 text-xs font-medium text-brand-600 hover:bg-brand-50 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleToggleStatus(p)}
                      disabled={toggleStatusMutation.isPending}
                      className={`flex-1 rounded-lg border py-1.5 text-xs font-medium transition-colors disabled:opacity-50 ${
                        p.status === 'ACTIVE'
                          ? 'border-red-200 text-red-500 hover:bg-red-50'
                          : 'border-green-200 text-green-600 hover:bg-green-50'
                      }`}
                    >
                      {p.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3">
            <p className="text-xs text-slate-400">
              Showing {filtered.length} of {total} product{total !== 1 ? 's' : ''}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
