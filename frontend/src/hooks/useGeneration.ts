import { useMutation, useQueryClient } from '@tanstack/react-query'
import { generateImage } from '../lib/api'
import type { GenerateRequest } from '../lib/types'

export function useGeneration(onComplete?: () => void) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (request: GenerateRequest) => generateImage(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['images'] })
      onComplete?.()
    },
    onError: () => {
      onComplete?.()
    },
  })

  return {
    generate: mutation.mutate,
    isGenerating: mutation.isPending,
    error: mutation.error,
  }
}
