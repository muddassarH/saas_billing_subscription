"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { api } from "@/lib/api";

export default function DashboardPage() {
  const usage = useQuery({
    queryKey: ["usage"],
    queryFn: async () => {
      const { data } = await api.get("/usage/");
      return data as {
        period_start: string;
        limits: { api_calls_per_month: number; credits: number };
        usage: { api_calls: number; credits: number };
        feature_flags: string[];
      };
    },
  });

  const sub = useQuery({
    queryKey: ["subscription"],
    queryFn: async () => {
      const { data } = await api.get("/subscription/");
      return data as {
        subscription: { plan: { name: string; slug: string }; status: string } | null;
        effective_plan: { name: string; slug: string };
      };
    },
  });

  return (
    <div className="space-y-8">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-600">Usage and subscription overview</p>
        </div>
        <Link
          href="/pricing"
          className="inline-flex justify-center rounded-xl bg-indigo-600 px-5 py-2.5 font-semibold text-white hover:bg-indigo-500"
        >
          Upgrade plan
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Current plan</h2>
          {sub.isLoading && <p className="mt-2 text-slate-500">Loading…</p>}
          {sub.data && (
            <div className="mt-3 space-y-1">
              <p className="text-2xl font-bold text-slate-900">
                {sub.data.subscription?.plan.name ?? sub.data.effective_plan.name}
              </p>
              <p className="text-sm text-slate-500">
                Status: {sub.data.subscription?.status ?? "free tier"}
              </p>
            </div>
          )}
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Usage this period</h2>
          {usage.isLoading && <p className="mt-2 text-slate-500">Loading…</p>}
          {usage.data && (
            <dl className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-600">API calls</dt>
                <dd className="font-medium text-slate-900">
                  {usage.data.usage.api_calls} / {usage.data.limits.api_calls_per_month}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-600">Credits</dt>
                <dd className="font-medium text-slate-900">
                  {usage.data.usage.credits} / {usage.data.limits.credits}
                </dd>
              </div>
            </dl>
          )}
        </div>
      </div>

      <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-slate-900">Feature flags</h2>
        <ul className="mt-2 list-inside list-disc text-sm text-slate-600">
          {(usage.data?.feature_flags ?? []).map((f) => (
            <li key={f}>{f}</li>
          ))}
          {usage.data && usage.data.feature_flags.length === 0 && (
            <li className="list-none text-slate-400">No flags on current plan</li>
          )}
        </ul>
      </div>
    </div>
  );
}
