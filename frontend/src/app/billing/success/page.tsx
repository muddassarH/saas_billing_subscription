import Link from "next/link";

export default function BillingSuccessPage() {
  return (
    <div className="mx-auto max-w-lg space-y-4 text-center">
      <h1 className="text-2xl font-bold text-slate-900">Checkout complete</h1>
      <p className="text-slate-600">
        Thanks for subscribing. Webhooks will sync your subscription shortly.
      </p>
      <Link href="/dashboard" className="inline-block font-medium text-indigo-600 hover:underline">
        Back to dashboard
      </Link>
    </div>
  );
}
