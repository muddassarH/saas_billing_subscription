"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export default function BillingPage() {
  const invoices = useQuery({
    queryKey: ["invoices"],
    queryFn: async () => {
      const { data } = await api.get("/invoices/");
      return data as { results?: unknown[] } | unknown[];
    },
  });

  async function openPortal() {
    const { data } = await api.post("/billing-portal/", {});
    if (data.url) window.location.href = data.url;
  }

  const list = Array.isArray(invoices.data)
    ? invoices.data
    : invoices.data?.results ?? [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Billing</h1>
        <p className="text-slate-600">Manage payment method and invoices in Stripe</p>
      </div>

      <button
        type="button"
        onClick={openPortal}
        className="rounded-xl bg-slate-900 px-5 py-2.5 font-semibold text-white hover:bg-slate-800"
      >
        Open billing portal
      </button>

      <div>
        <h2 className="text-lg font-semibold text-slate-900">Invoice history</h2>
        {invoices.isLoading && <p className="mt-2 text-slate-500">Loading…</p>}
        {!invoices.isLoading && list.length === 0 && (
          <p className="mt-2 text-sm text-slate-500">No invoices synced yet (webhook: invoice.payment_succeeded).</p>
        )}
        <ul className="mt-4 divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white">
          {(list as { stripe_invoice_id: string; amount_paid_cents: number; status: string }[]).map(
            (inv) => (
              <li key={inv.stripe_invoice_id} className="flex justify-between px-4 py-3 text-sm">
                <span className="font-mono text-slate-600">{inv.stripe_invoice_id}</span>
                <span className="text-slate-900">
                  ${(inv.amount_paid_cents / 100).toFixed(2)} — {inv.status}
                </span>
              </li>
            ),
          )}
        </ul>
      </div>
    </div>
  );
}
