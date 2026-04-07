import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Header from './components/Header'
import Generate from './pages/Generate'
import { useTheme } from './hooks/useTheme'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  const { theme, toggle } = useTheme()

  return (
    <QueryClientProvider client={queryClient}>
      <div className={`min-h-screen ${theme === 'light' ? 'bg-slate-100 text-slate-900' : 'bg-slate-900 text-white'}`}>
        <Header theme={theme} onToggleTheme={toggle} />
        <Generate />
      </div>
    </QueryClientProvider>
  )
}

export default App
