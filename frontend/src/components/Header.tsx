import { useQuery } from '@tanstack/react-query'
import { Sparkles, Cpu } from 'lucide-react'
import { getGpuStatus } from '../lib/api'

export default function Header() {
  const { data: gpu } = useQuery({
    queryKey: ['gpu-status'],
    queryFn: getGpuStatus,
    refetchInterval: 10000,
  })

  const hasCuda = gpu?.device === 'cuda'
  const vramUsed = gpu?.vram ? (gpu.vram.used / (1024 ** 3)).toFixed(1) : null
  const vramTotal = gpu?.vram ? (gpu.vram.total / (1024 ** 3)).toFixed(1) : null

  return (
    <header className="bg-slate-800/80 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles size={24} className="text-violet-400" />
          <h1 className="text-xl font-bold text-white tracking-tight">Imaginaree</h1>
        </div>

        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Cpu size={16} />
          <span
            className={`w-2 h-2 rounded-full ${hasCuda ? 'bg-green-500' : 'bg-yellow-500'}`}
          />
          <span>
            {hasCuda
              ? vramUsed && vramTotal
                ? `GPU ${vramUsed}/${vramTotal} GB`
                : 'GPU Ready'
              : gpu?.device ?? 'CPU'}
          </span>
        </div>
      </div>
    </header>
  )
}
