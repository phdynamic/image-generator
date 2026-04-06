import { useQuery } from '@tanstack/react-query'
import { ChevronDown, HardDrive, Download } from 'lucide-react'
import { getModels } from '../lib/api'

interface ModelSelectorProps {
  value: string
  onChange: (modelId: string) => void
}

export default function ModelSelector({ value, onChange }: ModelSelectorProps) {
  const { data: models, isLoading } = useQuery({
    queryKey: ['models'],
    queryFn: getModels,
  })

  if (isLoading) {
    return (
      <div className="bg-slate-800 border border-slate-600 rounded-lg p-2 text-sm text-slate-400">
        Loading models...
      </div>
    )
  }

  if (!models || models.length === 0) {
    return (
      <div className="bg-slate-800 border border-slate-600 rounded-lg p-2 text-sm text-slate-400">
        No models available
      </div>
    )
  }

  return (
    <div>
      <label className="block text-sm text-slate-400 mb-1">Model</label>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-slate-800 border border-slate-600 rounded-lg p-2.5 pr-10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent appearance-none"
        >
          {models.map((model) => (
            <option key={model.id} value={model.id}>
              {model.is_loaded ? '\u25CF ' : ''}{model.name} ({model.vram}){model.is_cached ? '' : ' \u2913'}
            </option>
          ))}
        </select>
        <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
      </div>
      {/* Status indicator below dropdown */}
      {value && models.find(m => m.id === value) && (
        <div className="flex items-center gap-1.5 mt-1.5 text-xs text-slate-500">
          {models.find(m => m.id === value)!.is_cached ? (
            <><HardDrive size={12} /> Downloaded locally</>
          ) : (
            <><Download size={12} /> Will download on first use</>
          )}
        </div>
      )}
    </div>
  )
}
