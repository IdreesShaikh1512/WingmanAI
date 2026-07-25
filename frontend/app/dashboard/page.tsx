"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";

export default function DashboardRedirect() {
  const router = useRouter();
  const { token } = useAuthStore();
  useEffect(() => {
    router.replace(token ? "/mission-control" : "/login");
  }, [router, token]);
  return null;
}
