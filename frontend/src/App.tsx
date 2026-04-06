import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Header from './components/Header'
import Generate from './pages/Generate'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-slate-900">
        <Header />
        <Generate />
      </div>
    </QueryClientProvider>
  )
}

export default App
