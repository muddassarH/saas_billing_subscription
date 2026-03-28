"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export default function AdminPage() {
  const users = useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => {
      const { data } = await api.get("/admin/users/");
      return data as { results?: unknown[] } | unknown[];
    },
  });

  const plans = useQuery({
    queryKey: ["admin-plans"],
    queryFn: async () => {
      const { data } = await api.get("/admin/plans/");
      return data as { results?: unknown[] } | unknown[];
    },
  });

  const userList = Array.isArray(users.data) ? users.data : users.data?.results ?? [];
  const planList = Array.isArray(plans.data) ? plans.data : plans.data?.results ?? [];

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Admin</h1>
        <p className="text-slate-600">Requires USER role ADMIN (or superuser).</p>
      </div>

      <section>
        <h2 className="text-lg font-semibold text-slate-900">Plans</h2>
        {plans.isError && (
          <p className="mt-2 text-sm text-red-600">Forbidden or not authenticated.</p>
        )}
        {plans.isLoading && <p className="text-slate-500">Loading…</p>}
        <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2">Slug</th>
                <th className="px-4 py-2">Stripe monthly price</th>
              </tr>
            </thead>
            <tbody>
              {(planList as { id: number; name: string; slug: string; stripe_price_id_monthly: string }[]).map(
                (p) => (
                  <tr key={p.id} className="border-t border-slate-100">
                    <td className="px-4 py-2">{p.name}</td>
                    <td className="px-4 py-2 font-mono text-xs">{p.slug}</td>
                    <td className="px-4 py-2 font-mono text-xs">{p.stripe_price_id_monthly || "—"}</td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-slate-900">Users</h2>
        {users.isError && (
          <p className="mt-2 text-sm text-red-600">Forbidden or not authenticated.</p>
        )}
        {users.isLoading && <p className="text-slate-500">Loading…</p>}
        <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-2">Email</th>
                <th className="px-4 py-2">Role</th>
              </tr>
            </thead>
            <tbody>
              {(userList as { id: number; email: string; role: string }[]).map((u) => (
                <tr key={u.id} className="border-t border-slate-100">
                  <td className="px-4 py-2">{u.email}</td>
                  <td className="px-4 py-2">{u.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
