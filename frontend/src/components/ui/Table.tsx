import type { HTMLAttributes, TableHTMLAttributes, ReactNode } from 'react'
import { cn } from '../../utils/cn'
export function Table({ className, children, ...props }: TableHTMLAttributes<HTMLTableElement>) {
  return <div className="overflow-x-auto"><table className={cn('w-full text-sm', className)} {...props}>{children}</table></div>
}
export function Th({ children, className }: { children: ReactNode; className?: string }) {
  return <th className={cn('px-4 py-3 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap', className)}>{children}</th>
}
export function Td({ children, className }: HTMLAttributes<HTMLTableCellElement> & { children?: ReactNode }) {
  return <td className={cn('px-4 py-3', className)}>{children}</td>
}
