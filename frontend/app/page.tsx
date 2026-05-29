"use client";

import { FormEvent, useState } from "react";
import { submitRequest, type SubmitResponse, type Urgency } from "@/lib/api";

const DEPARTMENTS = ["IT", "HR", "Operations"];

export default function RequesterPage() {
  const [item, setItem] = useState("Office Laptops");
  const [quantity, setQuantity] = useState(10);
  const [estimatedCost, setEstimatedCost] = useState(3500);
  const [urgency, setUrgency] = useState<Urgency>("medium");
  const [department, setDepartment] = useState("IT");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SubmitResponse | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await submitRequest({
        item,
        quantity,
        estimated_cost: estimatedCost,
        urgency,
        department,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">New Procurement Request</h1>
        <p className="mt-1 text-sm text-slate-600">
          Submit a request for budget check, vendor quote extraction, scoring, and
          approval routing. Final pricing comes from vendor quotes, not this form.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div>
          <label className="block text-sm font-medium text-slate-700">Item Name</label>
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={item}
            onChange={(e) => setItem(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Quantity</label>
          <input
            type="number"
            min={1}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">
            Estimated Budget ($)
          </label>
          <input
            type="number"
            min={1}
            step={0.01}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={estimatedCost}
            onChange={(e) => setEstimatedCost(Number(e.target.value))}
            required
          />
          <p className="mt-1 text-xs text-slate-500">
            Used for department budget check and approval routing only. Purchase
            price is determined from vendor quotes after submission.
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Routing: &lt; $5k auto-approve · $5k–$20k manager · ≥ $20k finance
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-700">Urgency</label>
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={urgency}
              onChange={(e) => setUrgency(e.target.value as Urgency)}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Department</label>
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
            >
              {DEPARTMENTS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Processing pipeline…" : "Submit Request"}
        </button>
      </form>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {result && (
        <div className="rounded-md border border-green-200 bg-green-50 p-4 text-sm text-green-900 space-y-2">
          <p className="font-medium">{result.message}</p>
          <p>Request ID: <code className="text-xs">{result.request_id}</code></p>
          <p>Status: {result.status}</p>
          {result.approval_tier && <p>Approval tier: {result.approval_tier}</p>}
          {result.request?.justification && (
            <p className="mt-2 text-slate-700">
              <span className="font-medium">Justification:</span> {result.request.justification}
            </p>
          )}
          {result.request?.vendor_scores && result.request.vendor_scores.length > 0 && (
            <div className="mt-2">
              <p className="font-medium">Top vendor scores:</p>
              <ul className="list-disc pl-5 mt-1">
                {result.request.vendor_scores.slice(0, 3).map((v, i) => (
                  <li key={i}>
                    {(v as { vendor_name: string; total_score: number }).vendor_name} —{" "}
                    {(v as { total_score: number }).total_score}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
