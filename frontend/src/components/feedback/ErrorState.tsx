import { AlertCircle, RefreshCcw } from 'lucide-react'
import { Button } from '../ui/Button'

interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
}

export function ErrorState({ 
  title = "Something went wrong", 
  message = "We encountered an error while loading the data. Please try again.", 
  onRetry 
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-100 text-red-600 dark:bg-red-900/20 dark:text-red-500">
        <AlertCircle size={32} />
      </div>
      <h3 className="mt-4 text-lg font-semibold text-slate-900 dark:text-white">{title}</h3>
      <p className="mt-2 max-w-sm text-sm text-slate-500 dark:text-slate-400">
        {message}
      </p>
      {onRetry && (
        <Button 
          variant="outline" 
          size="sm" 
          onClick={onRetry} 
          className="mt-6 gap-2"
        >
          <RefreshCcw size={16} />
          Try Again
        </Button>
      )}
    </div>
  )
}
