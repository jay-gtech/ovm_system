import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ShieldAlert, AlertTriangle, Shield, Info,
  ChevronLeft, ChevronRight, ChevronDown, ChevronUp,
  ExternalLink, Activity,
} from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Card, CardContent } from '../../components/ui/Card'
import { Loader } from '../../components/feedback/Loader'
import { useRiskSummary, useRiskAssessments } from './hooks/useRiskAssessments'
import { timeAgo } from '../../utils/format'
import type { RiskLevel, RiskAssessment } from '../../types'

const PAGE_SIZE = 50

// ---------------------------------------------------------------------------
// Level config
// ---------------------------------------------------------------------------

const LEVEL_CONFIG: Record<RiskLevel, {
  border: string
  badge: string
  card: string
  icon: React.ReactNode
  label: string
}> = {
  CRITICAL: {
    border: 'border-l-red-500',
    badge: 'bg-red-50 text-red-700 border-red-200',
    card: 'border-red-100 bg-red-50 text-red-700',
    icon: <ShieldAlert size={14} className="text-red-500" />,
    label: 'Critical',
  },
  HIGH: {
    border: 'border-l-orange-400',
    badge: 'bg-orange-50 text-orange-700 border-orange-200',
    card: 'border-orange-100 bg-orange-50 text-orange-700',
    icon: <AlertTriangle size={14} className="text-orange-400" />,
    label: 'High',
  },
  MEDIUM: {
    border: 'border-l-amber-400',
    badge: 'bg-amber-50 text-amber-700 border-amber-200',
    card: 'border-amber-100 bg-amber-50 text-amber-700',
    icon: <AlertTriangle size={14} className="text-amber-400" />,
    label: 'Medium',
  },
  LOW: {
    border: 'border-l-blue-400',
    badge: 'bg-blue-50 text-blue-700 border-blue-200',
    card: 'border-blue-100 bg-blue-50 text-blue-700',
    icon: <Info size={14} className="text-blue-400" />,
    label: 'Low',
  },
}

const ENTITY_ROUTE: Record<string, string> = {
  invoice: '/invoices',
  vendor: '/vendors',
  payment: '/payments',
}

const ENTITY_LABEL: Record<string, string> = {
  invoice: 'Invoice',
  vendor: 'Vendor',
  payment: 'Payment',
}

function entityNavPath(entityType: string, entityId: string): string | null {
  const base = ENTITY_ROUTE[entityType]
  return base ? `${base}/${entityId}` : null
}

function entityRef(assessment: RiskAssessment): string {
  const snap = assessment.source_snapshot_json
  if (!snap) return String(assessment.entity_id).slice(0, 8)
  return (
    (snap['invoice_number'] as string) ||
    (snap['vendor_name'] as string) ||
    (snap['payment_reference'] as string) ||
    String(assessment.entity_id).slice(0, 8)
  )
}

// ---------------------------------------------------------------------------
// Risk score bar
// ---------------------------------------------------------------------------

function ScoreBar({ score, level }: { score: number; level: RiskLevel }) {
  const barColor: Record<RiskLevel, string> = {
    CRITICAL: 'bg-red-500',
    HIGH: 'bg-orange-400',
    MEDIUM: 'bg-amber-400',
    LOW: 'bg-blue-400',
  }
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 rounded-full bg-slate-100 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${barColor[level]}`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="text-xs font-semibold text-slate-600 tabular-nums">{score}</span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Contributing factors breakdown (entity-type-aware)
// ---------------------------------------------------------------------------

interface FactorRow { label: string; raw: string; score: number; weight: string }

function parseInvoiceFactors(f: Record<string, unknown>): FactorRow[] {
  return [
    { label: 'Overdue Days',      raw: `${f['overdue_days'] ?? 0} days`,   score: Number(f['overdue_factor_score'] ?? 0),     weight: String(f['overdue_weight'] ?? '0.35') },
    { label: 'Outstanding Amount',raw: `₹${Number(f['outstanding_amount'] ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`, score: Number(f['outstanding_factor_score'] ?? 0), weight: String(f['outstanding_weight'] ?? '0.25') },
    { label: 'Unresolved Alerts', raw: `${f['unresolved_alert_count'] ?? 0}`, score: Number(f['alert_factor_score'] ?? 0),   weight: String(f['alert_weight'] ?? '0.15') },
    { label: 'SLA Breaches',      raw: `${f['sla_breach_count'] ?? 0}`,    score: Number(f['sla_breach_factor_score'] ?? 0), weight: String(f['sla_breach_weight'] ?? '0.15') },
    { label: 'Escalation Level',  raw: `Level ${f['max_escalation_level'] ?? 0}`, score: Number(f['escalation_factor_score'] ?? 0), weight: String(f['escalation_weight'] ?? '0.10') },
  ]
}

function parseVendorFactors(f: Record<string, unknown>): FactorRow[] {
  const pct = Math.round(Number(f['overdue_invoice_ratio'] ?? 0) * 100)
  return [
    { label: 'Overdue Invoice Ratio', raw: `${f['overdue_invoice_count'] ?? 0} of ${f['total_active_invoices'] ?? 0} (${pct}%)`, score: Number(f['overdue_ratio_factor_score'] ?? 0), weight: String(f['overdue_ratio_weight'] ?? '0.35') },
    { label: 'Unresolved Liabilities', raw: `${f['unresolved_liabilities'] ?? 0}`, score: Number(f['unresolved_factor_score'] ?? 0), weight: String(f['unresolved_weight'] ?? '0.30') },
    { label: 'Delayed Settlements', raw: `${f['delayed_settlement_count'] ?? 0}`, score: Number(f['delayed_factor_score'] ?? 0), weight: String(f['delayed_weight'] ?? '0.20') },
    { label: 'SLA Breaches', raw: `${f['sla_breach_count'] ?? 0}`, score: Number(f['sla_breach_factor_score'] ?? 0), weight: String(f['sla_breach_weight'] ?? '0.15') },
  ]
}

function parsePaymentFactors(f: Record<string, unknown>): FactorRow[] {
  return [
    { label: 'Settlement Aging', raw: `${f['settlement_aging_days'] ?? 0} days`, score: Number(f['aging_factor_score'] ?? 0), weight: String(f['aging_weight'] ?? '0.40') },
    { label: 'Pending Amount', raw: `₹${Number(f['pending_amount'] ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`, score: Number(f['pending_factor_score'] ?? 0), weight: String(f['pending_weight'] ?? '0.30') },
    { label: 'Partial Settlements', raw: `${f['partial_settlement_count'] ?? 0} records`, score: Number(f['partial_factor_score'] ?? 0), weight: String(f['partial_weight'] ?? '0.20') },
    { label: 'Unresolved Alerts', raw: `${f['unresolved_alert_count'] ?? 0}`, score: Number(f['alert_factor_score'] ?? 0), weight: String(f['alert_weight'] ?? '0.10') },
  ]
}

function parseFactors(entityType: string, factors: Record<string, unknown>): FactorRow[] {
  if (entityType === 'invoice') return parseInvoiceFactors(factors)
  if (entityType === 'vendor')  return parseVendorFactors(factors)
  if (entityType === 'payment') return parsePaymentFactors(factors)
  return []
}

function FactorBreakdown({ entityType, factors }: { entityType: string; factors: Record<string, unknown> }) {
  const rows = parseFactors(entityType, factors)
  return (
    <div className="mt-3 rounded-lg border border-slate-100 bg-slate-50 overflow-hidden">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-slate-100 text-left">
            <th className="px-3 py-2 font-medium text-slate-500">Factor</th>
            <th className="px-3 py-2 font-medium text-slate-500">Raw Value</th>
            <th className="px-3 py-2 font-medium text-slate-500">Factor Score</th>
            <th className="px-3 py-2 font-medium text-slate-500">Weight</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row) => (
            <tr key={row.label}>
              <td className="px-3 py-2 text-slate-700 font-medium">{row.label}</td>
              <td className="px-3 py-2 text-slate-600">{row.raw}</td>
              <td className="px-3 py-2">
                <div className="flex items-center gap-1.5">
                  <div className="h-1 w-12 rounded-full bg-slate-200 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-brand-400"
                      style={{ width: `${row.score}%` }}
                    />
                  </div>
                  <span className="text-slate-600 tabular-nums">{row.score}/100</span>
                </div>
              </td>
              <td className="px-3 py-2 text-slate-500">
                {Math.round(Number(row.weight) * 100)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Single risk row
// ---------------------------------------------------------------------------

function RiskRow({ assessment }: { assessment: RiskAssessment }) {
  const [expanded, setExpanded] = useState(false)
  const navigate = useNavigate()
  const level = assessment.risk_level as RiskLevel
  const cfg = LEVEL_CONFIG[level]
  const navPath = entityNavPath(assessment.entity_type, String(assessment.entity_id))
  const ref = entityRef(assessment)
  const entityLabel = ENTITY_LABEL[assessment.entity_type] ?? assessment.entity_type

  return (
    <div className={`border-l-4 ${cfg.border} px-5 py-4 hover:bg-slate-50/60 transition-colors`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Badges row */}
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${cfg.badge}`}>
              {cfg.icon}
              {cfg.label}
            </span>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500 uppercase tracking-wide">
              {entityLabel}
            </span>
            <span className="text-xs font-semibold text-slate-700">{ref}</span>
          </div>

          {/* Explanation text */}
          <p className="text-sm text-slate-600 leading-relaxed">
            {expanded
              ? assessment.explanation_text
              : assessment.explanation_text.length > 130
              ? assessment.explanation_text.slice(0, 130) + '…'
              : assessment.explanation_text}
          </p>

          {/* Score bar + metadata row */}
          <div className="mt-2 flex flex-wrap items-center gap-4">
            <ScoreBar score={assessment.risk_score} level={level} />
            <span className="text-[11px] text-slate-400">{timeAgo(assessment.generated_at)}</span>
          </div>

          {/* Factor breakdown (expanded) */}
          {expanded && (
            <FactorBreakdown
              entityType={assessment.entity_type}
              factors={assessment.contributing_factors as Record<string, unknown>}
            />
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 shrink-0">
          {navPath && (
            <button
              onClick={() => navigate(navPath)}
              className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2.5 py-1 text-xs text-slate-500 hover:border-brand-300 hover:text-brand-600 transition-colors whitespace-nowrap"
            >
              <ExternalLink size={11} />
              View {entityLabel}
            </button>
          )}
          <button
            onClick={() => setExpanded((e) => !e)}
            className="rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-500 hover:bg-slate-50 transition-colors"
            aria-label={expanded ? 'Collapse factors' : 'Expand factors'}
          >
            {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Summary card
// ---------------------------------------------------------------------------

function SummaryCard({
  level,
  count,
  selected,
  onClick,
}: {
  level: RiskLevel | 'ALL'
  count: number
  selected: boolean
  onClick: () => void
}) {
  const cfg = level !== 'ALL' ? LEVEL_CONFIG[level] : null
  return (
    <button
      onClick={onClick}
      className={`rounded-xl border px-4 py-3 text-left transition-all ${
        cfg ? cfg.card : 'border-slate-200 bg-slate-50 text-slate-700'
      } ${selected ? 'ring-2 ring-brand-400' : ''}`}
    >
      <div className="flex items-center gap-1.5 mb-1">
        {cfg ? cfg.icon : <Shield size={13} className="text-slate-400" />}
        <p className="text-xs font-medium opacity-70">{cfg ? cfg.label : 'All'}</p>
      </div>
      <p className="text-2xl font-bold">{count}</p>
    </button>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function RiskIntelligencePage() {
  const [levelFilter, setLevelFilter] = useState<string>('ALL')
  const [typeFilter, setTypeFilter] = useState<string>('ALL')
  const [latestOnly, setLatestOnly] = useState(true)
  const [page, setPage] = useState(0)

  const { data: summary, isLoading: summaryLoading } = useRiskSummary()

  const filters = {
    skip: page * PAGE_SIZE,
    limit: PAGE_SIZE,
    latest_only: latestOnly,
    ...(levelFilter !== 'ALL' ? { risk_level: levelFilter } : {}),
    ...(typeFilter !== 'ALL' ? { entity_type: typeFilter } : {}),
  }
  const { data, isLoading, isError } = useRiskAssessments(filters)

  const assessments = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  const summaryData = {
    CRITICAL: summary?.critical_count ?? 0,
    HIGH:     summary?.high_count ?? 0,
    MEDIUM:   summary?.medium_count ?? 0,
    LOW:      summary?.low_count ?? 0,
    ALL:      summary?.total_assessed_entities ?? 0,
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Operational Intelligence"
        subtitle="Deterministic risk scoring — AI assists, humans decide"
        actions={
          <div className="flex items-center gap-2">
            <Activity size={14} className="text-brand-500" />
            <span className="text-xs text-slate-500">
              Updated every 6–12 h by scheduler
            </span>
          </div>
        }
      />

      {/* Summary cards */}
      <div className="grid gap-3 sm:grid-cols-5">
        {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((l) => (
          <SummaryCard
            key={l}
            level={l}
            count={summaryLoading ? 0 : summaryData[l]}
            selected={levelFilter === l}
            onClick={() => {
              setLevelFilter(l)
              setPage(0)
            }}
          />
        ))}
      </div>

      {/* Filter row */}
      <div className="flex flex-wrap gap-3 items-center">
        {/* Entity type tabs */}
        <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1">
          {([
            ['ALL', 'All Entities'],
            ['invoice', 'Invoices'],
            ['vendor', 'Vendors'],
            ['payment', 'Payments'],
          ] as const).map(([val, label]) => (
            <button
              key={val}
              onClick={() => { setTypeFilter(val); setPage(0) }}
              className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                typeFilter === val
                  ? 'bg-brand-500 text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Latest-only toggle */}
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <div
            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
              latestOnly ? 'bg-brand-500' : 'bg-slate-200'
            }`}
            onClick={() => { setLatestOnly((v) => !v); setPage(0) }}
          >
            <span
              className={`inline-block h-3.5 w-3.5 rounded-full bg-white shadow-sm transition-transform ${
                latestOnly ? 'translate-x-[18px]' : 'translate-x-[2px]'
              }`}
            />
          </div>
          <span className="text-xs text-slate-600">Latest per entity</span>
        </label>
      </div>

      {/* Risk entity feed */}
      <Card>
        <div className="border-b border-slate-100 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert size={15} className="text-slate-400" />
            <p className="text-sm font-semibold text-slate-700">Risk Entities</p>
          </div>
          <p className="text-xs text-slate-400">{total} total</p>
        </div>

        <CardContent className="p-0">
          {isLoading && (
            <div className="flex justify-center py-16">
              <Loader />
            </div>
          )}

          {isError && (
            <div className="px-4 py-12 text-center text-sm text-red-500">
              Failed to load risk assessments. Check your connection and try again.
            </div>
          )}

          {!isLoading && !isError && (
            <div className="divide-y divide-slate-50">
              {assessments.length === 0 ? (
                <div className="px-4 py-16 text-center">
                  <Shield size={32} className="mx-auto mb-3 text-slate-200" />
                  <p className="text-sm text-slate-400">
                    {total === 0 && !isLoading
                      ? 'No risk assessments yet — scheduler runs every 6–12 hours.'
                      : 'No entities match the current filters.'}
                  </p>
                </div>
              ) : (
                assessments.map((a) => <RiskRow key={a.id} assessment={a} />)
              )}
            </div>
          )}
        </CardContent>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="border-t border-slate-100 px-4 py-3 flex items-center justify-between">
            <p className="text-xs text-slate-500">
              Page {page + 1} of {totalPages} · {total} assessments
            </p>
            <div className="flex gap-2">
              <button
                disabled={page === 0}
                onClick={() => setPage((p) => p - 1)}
                className="rounded-md border border-slate-200 p-1.5 text-slate-500 hover:bg-slate-50 disabled:opacity-40 transition-colors"
              >
                <ChevronLeft size={14} />
              </button>
              <button
                disabled={page >= totalPages - 1}
                onClick={() => setPage((p) => p + 1)}
                className="rounded-md border border-slate-200 p-1.5 text-slate-500 hover:bg-slate-50 disabled:opacity-40 transition-colors"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}
