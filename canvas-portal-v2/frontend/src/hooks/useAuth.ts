import { useQuery } from '@tanstack/react-query'
import { fetchAuthMe, type AuthMe } from '@/api/auth'

export function useAuth() {
  const query = useQuery<AuthMe, Error>({
    queryKey: ['auth', 'me'],
    queryFn: fetchAuthMe,
    staleTime: 5 * 60_000,   // 5 minutes
    retry: 1,
  })

  return {
    user: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    authenticated: query.data?.authenticated ?? false,
    username: query.data?.username ?? '',
    email: query.data?.email ?? '',
    groups: query.data?.groups ?? [],
    refetch: query.refetch,
  }
}
