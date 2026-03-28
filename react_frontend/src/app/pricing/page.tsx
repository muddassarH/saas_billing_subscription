"use client";

import { useQuery } from "@tanstack/react-query";
import { loadStripe } from "@stripe/stripe-js";
import { api } from "@/lib/api";

const pk = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || "";

type Plan = {
  id: number;
  name: string;
  slug: string;
  description: string;
  price_monthly_cents: number;
  price_yearly_cents: number;
};

export default function PricingPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["plans"],
    queryFn: async () => {
      const { data } = await api.get("/plans/");
      return data as { results?: Plan[] } | Plan[];
    },
  });

  const plans = Array.isArray(data) ? data : data?.results ?? [];

  async function checkout(slug: string, interval: "month" | "year") {
    if (slug === "free") return;
    const { data } = await api.post("/create-checkout-session/", {
      plan_slug: slug,
      billing_interval: interval,
    });
    if (data.checkout_url) {
      if (pk) {
        await loadStripe(pk);
      }
      window.location.href = data.checkout_url;
    }
  }

  return (
    <div className="space-y-10">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-slate-900">Pricing</h1>
        <p className="mt-2 text-slate-600">
          Configure Stripe price IDs in Django admin, then checkout here.
        </p>
      </div>
      {isLoading && <p className="text-center text-slate-500">Loading plans…</p>}
      {error && (
        <p className="text-center text-red-600">Could not load plans. Is the API running?</p>
      )}
      <div className="grid gap-6 md:grid-cols-3">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <h2 className="text-xl font-semibold text-slate-900">{plan.name}</h2>
            <p className="mt-2 flex-1 text-sm text-slate-600">{plan.description}</p>
            <div className="mt-4 space-y-1">
              <p className="text-2xl font-bold text-slate-900">
                ${(plan.price_monthly_cents / 100).toFixed(0)}
                <span className="text-base font-normal text-slate-500">/mo</span>
              </p>
              <p className="text-sm text-slate-500">
                or ${(plan.price_yearly_cents / 100).toFixed(0)}/yr
              </p>
            </div>
            <div className="mt-6 space-y-2">
              {plan.slug === "free" ? (
                <span className="block rounded-lg bg-slate-100 py-2 text-center text-sm text-slate-600">
                  Default plan
                </span>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={() => checkout(plan.slug, "month")}
                    className="w-full rounded-lg bg-indigo-600 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500"
                  >
                    Subscribe monthly
                  </button>
                  <button
                    type="button"
                    onClick={() => checkout(plan.slug, "year")}
                    className="w-full rounded-lg border border-slate-200 py-2.5 text-sm font-semibold text-slate-800 hover:bg-slate-50"
                  >
                    Subscribe yearly
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
