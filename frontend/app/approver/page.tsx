"use client";

import { useCallback, useEffect, useState } from "react";
import {
  approveRequest,
  generatePO,
  getThreeWayMatchStatus,
  listCompletedRequests,
  listRequests,
  parsePurchaseOrder,
  rejectRequest,
  threeWayMatch,
  type ProcurementRequest,
  type ThreeWayMatchStatus,
} from "@/lib/api";

type ApproverRole = "manager" | "finance";

const APPROVERS: Record<ApproverRole, { id: string; label: string }> = {
  manager: { id: "user_manager_1", label: "Bob Manager" },
  finance: { id: "user_finance_1", label: "Carol Finance" },
};

function MatchStatusBadge({ status }: { status: ThreeWayMatchStatus }) {
  const isMatched = status === "MATCHED";
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${
        isMatched
          ? "bg-green-100 text-green-800"
          : "bg-amber-100 text-amber-800"
      }`}
    >
      {status}
    </span>
  );
}

function PODetailsPanel({ req }: { req: ProcurementRequest }) {
  const po = parsePurchaseOrder(req.po);
  const matchStatus = getThreeWayMatchStatus(req);

  if (!po) {
    return (
      <p className="mt-3 text-sm text-slate-500">PO data not available.</p>
    );
  }

  return (
    <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-800">
          Purchase Order
        </h3>
        <MatchStatusBadge status={matchStatus} />
      </div>
      <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-slate-500">PO ID</dt>
          <dd className="font-medium text-slate-900">{po.number}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Vendor</dt>
          <dd className="font-medium text-slate-900">{po.vendor_name}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Total amount</dt>
          <dd className="font-medium text-slate-900">
            ${po.total.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Three-way match</dt>
          <dd>
            <MatchStatusBadge status={matchStatus} />
          </dd>
        </div>
      </dl>
      {po.line_items.length > 0 && (
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="py-2 pr-4 font-medium">Description</th>
                <th className="py-2 pr-4 font-medium">Qty</th>
                <th className="py-2 pr-4 font-medium">Unit price</th>
                <th className="py-2 font-medium">Line total</th>
              </tr>
            </thead>
            <tbody>
              {po.line_items.map((line, i) => (
                <tr key={i} className="border-b border-slate-100">
                  <td className="py-2 pr-4 text-slate-900">{line.description}</td>
                  <td className="py-2 pr-4 text-slate-700">{line.quantity}</td>
                  <td className="py-2 pr-4 text-slate-700">
                    ${line.unit_price.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                    })}
                  </td>
                  <td className="py-2 text-slate-900">
                    ${line.total.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                    })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {req.three_way_match?.notes && (
        <p className="mt-3 text-xs text-slate-600">
          Match notes: {req.three_way_match.notes}
        </p>
      )}
    </div>
  );
}

export default function ApproverPage() {
  const [role, setRole] = useState<ApproverRole>("manager");
  const [requests, setRequests] = useState<ProcurementRequest[]>([]);
  const [completedRequests, setCompletedRequests] = useState<
    ProcurementRequest[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [pending, completed] = await Promise.all([
        listRequests({ approver_role: role }),
        listCompletedRequests(),
      ]);
      setRequests(pending);
      setCompletedRequests(completed);
    } catch {
      setRequests([]);
      setCompletedRequests([]);
    } finally {
      setLoading(false);
    }
  }, [role]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleApprove(requestId: string) {
    setActionId(requestId);
    setMessage(null);
    try {
      await approveRequest(requestId, APPROVERS[role].id);
      await generatePO(requestId);
      await threeWayMatch(requestId);
      setMessage(`Request ${requestId} approved, PO generated, and three-way matched.`);
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Action failed");
    } finally {
      setActionId(null);
    }
  }

  async function handleReject(requestId: string) {
    setActionId(requestId);
    setMessage(null);
    try {
      await rejectRequest(requestId, APPROVERS[role].id, "Rejected by approver");
      setMessage(`Request ${requestId} rejected.`);
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Reject failed");
    } finally {
      setActionId(null);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Approver Dashboard</h1>
        <p className="mt-1 text-sm text-slate-600">
          Review pending requests, approve or reject, then view completed POs and
          three-way match results.
        </p>
      </div>

      <div className="flex gap-2">
        {(["manager", "finance"] as ApproverRole[]).map((r) => (
          <button
            key={r}
            onClick={() => setRole(r)}
            className={`rounded-md px-4 py-2 text-sm font-medium ${
              role === r
                ? "bg-blue-600 text-white"
                : "bg-white border border-slate-300 text-slate-700 hover:bg-slate-50"
            }`}
          >
            {r === "manager" ? "Manager queue" : "Finance queue"}
          </button>
        ))}
      </div>

      <p className="text-sm text-slate-600">
        Signed in as: <strong>{APPROVERS[role].label}</strong>
      </p>

      {message && (
        <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
          {message}
        </div>
      )}

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">Pending approval</h2>
        {loading ? (
          <p className="text-sm text-slate-500">Loading requests…</p>
        ) : requests.length === 0 ? (
          <p className="text-sm text-slate-500">No pending requests in this queue.</p>
        ) : (
          <ul className="space-y-4">
            {requests.map((req) => (
              <li
                key={req.id}
                className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <h3 className="font-semibold text-slate-900">{req.item}</h3>
                    <p className="text-sm text-slate-600 mt-1">
                      {req.department} · Qty {req.quantity} · $
                      {req.cost.toLocaleString()} · {req.urgency} urgency
                    </p>
                    <p className="text-xs text-slate-500 mt-1">ID: {req.id}</p>
                    {req.justification && (
                      <p className="text-sm text-slate-700 mt-2">
                        {req.justification}
                      </p>
                    )}
                    {req.vendor_scores && req.vendor_scores.length > 0 && (
                      <p className="text-sm text-slate-600 mt-1">
                        Top vendor:{" "}
                        {(req.vendor_scores[0] as { vendor_name: string })
                          .vendor_name}{" "}
                        (score{" "}
                        {(req.vendor_scores[0] as { total_score: number })
                          .total_score}
                        )
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleApprove(req.id)}
                      disabled={actionId === req.id}
                      className="rounded-md bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => handleReject(req.id)}
                      disabled={actionId === req.id}
                      className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">
          Completed — PO &amp; three-way match
        </h2>
        {loading ? (
          <p className="text-sm text-slate-500">Loading completed requests…</p>
        ) : completedRequests.length === 0 ? (
          <p className="text-sm text-slate-500">
            No completed requests with PO details yet.
          </p>
        ) : (
          <ul className="space-y-4">
            {completedRequests.map((req) => (
              <li
                key={req.id}
                className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold text-slate-900">{req.item}</h3>
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 uppercase">
                      {req.status}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 mt-1">
                    {req.department} · Request {req.id}
                  </p>
                </div>
                <PODetailsPanel req={req} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
