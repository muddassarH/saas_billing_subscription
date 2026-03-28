import Link from "next/link";

export default function Home() {
  return (
    <div className="space-y-12 text-center">
      <div className="space-y-4">
        <p className="text-sm font-medium uppercase tracking-wide text-indigo-600">
          Django · Stripe · Next.js
        </p>
        <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Production-ready billing & subscriptions
        </h1>
        <p className="mx-auto max-w-2xl text-lg text-slate-600">
          Plans, Stripe Checkout, webhooks with Celery, usage limits, and dashboards — wired for
          test mode and Docker deployment.
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-4">
        <Link
          href="/pricing"
          className="rounded-xl bg-indigo-600 px-6 py-3 font-semibold text-white shadow-sm hover:bg-indigo-500"
        >
          View pricing
        </Link>
        <Link
          href="/register"
          className="rounded-xl border border-slate-200 bg-white px-6 py-3 font-semibold text-slate-800 shadow-sm hover:bg-slate-50"
        >
          Create account
        </Link>
      </div>
    </div>
  );
}
