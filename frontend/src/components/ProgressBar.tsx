import { forwardRef, useImperativeHandle } from 'react'
import { useGenerationProgress } from '../hooks/useWebSocket'

export interface ProgressBarHandle {
  clear: () => void
}

interface ProgressBarProps {
  isGenerating: boolean
}

const ProgressBar = forwardRef<ProgressBarHandle, ProgressBarProps>(
  ({ isGenerating }, ref) => {
    const { progress, clearProgress } = useGenerationProgress()

    useImperativeHandle(ref, () => ({
      clear: clearProgress,
    }))

    if (!isGenerating && !progress) return null

    const percentage = progress
      ? Math.round((progress.step / progress.total_steps) * 100)
      : 0

    return (
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-slate-400">
          <span>
            {progress
              ? `Step ${progress.step} / ${progress.total_steps}`
              : 'Starting...'}
          </span>
          <span>{percentage}%</span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-2.5 overflow-hidden">
          <div
            className="bg-violet-500 h-full rounded-full transition-all duration-300 ease-out"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    )
  }
)

ProgressBar.displayName = 'ProgressBar'

export default ProgressBar
