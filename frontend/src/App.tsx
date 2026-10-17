import { useEffect } from 'react'
import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from '@tanstack/react-query'
import Header from './components/Header'
import Login from './components/Login'
import Generate from './pages/Generate'
import { useTheme } from './hooks/useTheme'
import { getAuthStatus, logout, UNAUTHORIZED_EVENT } from './lib/api'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function Shell({ theme, onToggleTheme }: { theme: 'dark' | 'light'; onToggleTheme: () => void }) {
  const client = useQueryClient()
  const { data: auth, isLoading, isError, refetch } = useQuery({
    queryKey: ['auth-status'],
    queryFn: getAuthStatus,
    retry: false,
  })

  // Any API call that comes back 401 means the session ended: show the sign-in page.
  useEffect(() => {
    const onUnauthorized = () => client.invalidateQueries({ queryKey: ['auth-status'] })
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
  }, [client])

  const handleLogout = async () => {
    await logout()
    client.removeQueries({ predicate: (q) => q.queryKey[0] !== 'auth-status' })
    client.invalidateQueries({ queryKey: ['auth-status'] })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500" />
      </div>
    )
  }

  if (isError || !auth) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-3 text-slate-400">
        <p>Can't reach the Imaginaree server.</p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm transition-colors"
        >
          Try again
        </button>
      </div>
    )
  }

  if (auth.auth_required && !auth.authenticated) {
    return <Login onSuccess={() => client.invalidateQueries({ queryKey: ['auth-status'] })} />
  }

  return (
    <>
      <Header
        theme={theme}
        onToggleTheme={onToggleTheme}
        onLogout={auth.auth_required ? handleLogout : undefined}
      />
      <Generate />
    </>
  )
}

function App() {
  const { theme, toggle } = useTheme()

  return (
    <QueryClientProvider client={queryClient}>
      <div className={`min-h-screen ${theme === 'light' ? 'bg-slate-100 text-slate-900' : 'bg-slate-900 text-white'}`}>
        <Shell theme={theme} onToggleTheme={toggle} />
      </div>
    </QueryClientProvider>
  )
}

export default App
