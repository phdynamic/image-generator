import { useMutation, useQueryClient } from '@tanstack/react-query'
import { generateImage } from '../lib/api'
import type { GenerateRequest } from '../lib/types'

export function useGeneration() {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (request: GenerateRequest) => generateImage(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['images'] })
    },
  })

  return {
    generate: mutation.mutate,
    isGenerating: mutation.isPending,
    error: mutation.error,
  }
}
