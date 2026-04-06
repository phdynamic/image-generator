import { useQuery } from '@tanstack/react-query'
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
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-slate-800 border border-slate-600 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
      >
        {models.map((model) => (
          <option key={model.id} value={model.id}>
            {model.is_loaded ? '\u25CF ' : ''}{model.name} ({model.vram})
          </option>
        ))}
      </select>
    </div>
  )
}
