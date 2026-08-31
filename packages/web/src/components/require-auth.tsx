import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { authApi } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import { useAuth } from "@/components/auth-provider";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();

  // Reflect a server restart with a newly-set/unset token promptly rather
  // than trusting a cached "auth disabled" from a previous session.
  const { data, isPending } = useQuery({
    queryKey: queryKeys.auth.config(),
    queryFn: authApi.getConfig,
    staleTime: 0,
    refetchOnMount: "always",
  });

  if (isPending) return null;

  if (data?.enabled && !isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
