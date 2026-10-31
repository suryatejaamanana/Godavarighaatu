"use client";

import { useQuery } from "@tanstack/react-query";
import { getMe } from "@/services/admin";
import type { Role } from "@/types/api";

const RANK: Record<Role, number> = { staff: 1, manager: 2, super_admin: 3 };

export function useAdmin() {
  return useQuery({ queryKey: ["me"], queryFn: getMe, retry: false, staleTime: 60_000 });
}

/** UI hint only. The API enforces permissions, so hiding a button is never the security boundary. */
export function useCan(minimum: Role) {
  const { data } = useAdmin();
  return !!data && RANK[data.role] >= RANK[minimum];
}
