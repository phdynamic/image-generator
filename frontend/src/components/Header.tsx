import { useQuery } from '@tanstack/react-query'
import { Sparkles, Cpu, Sun, Moon } from 'lucide-react'
import { getGpuStatus } from '../lib/api'

interface HeaderProps {
  theme: 'dark' | 'light'
  onToggleTheme: () => void
}

export default function Header({ theme, onToggleTheme }: HeaderProps) {
  const { data: gpu } = useQuery({
    queryKey: ['gpu-status'],
    queryFn: getGpuStatus,
    refetchInterval: 10000,
  })

  const hasCuda = gpu?.device === 'cuda'

  return (
    <header className={`${theme === 'light' ? 'bg-white/80 border-slate-200' : 'bg-slate-800/80 border-slate-700'} backdrop-blur-sm border-b sticky top-0 z-40`}>
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles size={24} className="text-violet-500" />
          <h1 className={`text-xl font-bold tracking-tight ${theme === 'light' ? 'text-slate-900' : 'text-white'}`}>Imaginaree</h1>
        </div>

        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 text-sm ${theme === 'light' ? 'text-slate-500' : 'text-slate-400'}`}>
            <Cpu size={16} />
            <span
              className={`w-2 h-2 rounded-full ${hasCuda ? 'bg-green-500' : 'bg-yellow-500'}`}
            />
            <span>{hasCuda ? 'GPU Ready' : 'CPU Mode'}</span>
          </div>

          <button
            onClick={onToggleTheme}
            className={`p-2 rounded-lg transition-colors ${theme === 'light' ? 'hover:bg-slate-100 text-slate-600' : 'hover:bg-slate-700 text-slate-400'}`}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </div>
    </header>
  )
}
