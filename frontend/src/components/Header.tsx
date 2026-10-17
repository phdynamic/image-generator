import { useQuery } from '@tanstack/react-query'
import { Sparkles, Cpu, Sun, Moon, LogOut } from 'lucide-react'
import { getGpuStatus } from '../lib/api'

interface HeaderProps {
  theme: 'dark' | 'light'
  onToggleTheme: () => void
  onLogout?: () => void
}

const GIB = 1024 ** 3

export default function Header({ theme, onToggleTheme, onLogout }: HeaderProps) {
  const { data: gpu } = useQuery({
    queryKey: ['gpu-status'],
    queryFn: getGpuStatus,
    refetchInterval: 10000,
  })

  const hasCuda = gpu?.device === 'cuda'
  const gpuName = gpu?.name?.replace(/^NVIDIA\s+(GeForce\s+)?/i, '')
  const freeGb = gpu?.vram ? (gpu.vram.free / GIB).toFixed(1) : null

  const iconButton = `p-2 rounded-lg transition-colors ${
    theme === 'light' ? 'hover:bg-slate-100 text-slate-600' : 'hover:bg-slate-700 text-slate-400'
  }`

  return (
    <header className={`${theme === 'light' ? 'bg-white/80 border-slate-200' : 'bg-slate-800/80 border-slate-700'} backdrop-blur-sm border-b sticky top-0 z-40`}>
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles size={24} className="text-violet-500" />
          <h1 className={`text-xl font-bold tracking-tight ${theme === 'light' ? 'text-slate-900' : 'text-white'}`}>Imaginaree</h1>
        </div>

        <div className="flex items-center gap-3">
          <div
            className={`flex items-center gap-2 text-sm ${theme === 'light' ? 'text-slate-500' : 'text-slate-400'}`}
            title={hasCuda ? 'Free VRAM changes as other programs use the GPU' : 'No CUDA GPU found. Generation will be very slow.'}
          >
            <Cpu size={16} />
            <span className={`w-2 h-2 rounded-full ${hasCuda ? 'bg-green-500' : 'bg-yellow-500'}`} />
            <span>
              {hasCuda
                ? `${gpuName ?? 'GPU'}${freeGb ? ` · ${freeGb} GB free` : ''}`
                : 'No GPU (CPU mode)'}
            </span>
          </div>

          <button
            onClick={onToggleTheme}
            className={iconButton}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>

          {onLogout && (
            <button onClick={onLogout} className={iconButton} title="Sign out">
              <LogOut size={18} />
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
