import type { FormHTMLAttributes, ReactNode } from 'react'
export function Form({ children, ...props }: FormHTMLAttributes<HTMLFormElement> & { children: ReactNode }) {
  return <form {...props}>{children}</form>
}
