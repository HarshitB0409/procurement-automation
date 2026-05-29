const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Urgency = "low" | "medium" | "high";

export interface SubmitRequestPayload {
  item: string;
  quantity: number;
  estimated_cost: number;
  urgency: Urgency;
  department: string;
  requester_id?: string;
}

export interface POLineItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface PurchaseOrder {
  number: string;
  vendor_name: string;
  line_items: POLineItem[];
  total: number;
  generated_at?: string;
}

export interface ThreeWayMatchResult {
  po_amount: number;
  invoice_amount: number;
  receipt_qty: number;
  ordered_qty: number;
  matched: boolean;
  notes: string;
}

export type ThreeWayMatchStatus = "MATCHED" | "EXCEPTION_FLAG";

export const COMPLETED_STATUSES = ["matched", "complete"] as const;

export interface ProcurementRequest {
  id: string;
  item: string;
  quantity: number;
  estimated_cost: number;
  /** Mirrors estimated_cost for display; not the vendor purchase price */
  cost: number;
  urgency: string;
  department: string;
  status: string;
  approval_tier?: string;
  requester_id: string;
  budget_check?: Record<string, unknown>;
  extracted_quotes?: Record<string, unknown>[];
  vendor_scores?: Record<string, unknown>[];
  justification?: string;
  selected_vendor_id?: string;
  po?: PurchaseOrder;
  three_way_match?: ThreeWayMatchResult;
}

export function isRequestComplete(req: ProcurementRequest): boolean {
  return COMPLETED_STATUSES.includes(
    req.status as (typeof COMPLETED_STATUSES)[number]
  );
}

export function getThreeWayMatchStatus(
  req: ProcurementRequest
): ThreeWayMatchStatus {
  if (req.three_way_match?.matched === false) return "EXCEPTION_FLAG";
  return "MATCHED";
}

export function parsePurchaseOrder(
  po: PurchaseOrder | Record<string, unknown> | undefined
): PurchaseOrder | null {
  if (!po || typeof po !== "object") return null;
  const p = po as PurchaseOrder;
  if (!p.number || !p.vendor_name) return null;
  return {
    number: String(p.number),
    vendor_name: String(p.vendor_name),
    total: Number(p.total ?? 0),
    generated_at: p.generated_at ? String(p.generated_at) : undefined,
    line_items: Array.isArray(p.line_items)
      ? p.line_items.map((li) => ({
          description: String((li as POLineItem).description ?? ""),
          quantity: Number((li as POLineItem).quantity ?? 0),
          unit_price: Number((li as POLineItem).unit_price ?? 0),
          total: Number((li as POLineItem).total ?? 0),
        }))
      : [],
  };
}

export interface SubmitResponse {
  request_id: string;
  status: string;
  approval_tier?: string;
  message: string;
  request?: ProcurementRequest;
}

function normalizeSubmitResponse(res: SubmitResponse): SubmitResponse {
  if (res.request) {
    return { ...res, request: normalizeProcurementRequest(res.request) };
  }
  return res;
}

function normalizeProcurementRequest(
  req: ProcurementRequest & { cost?: number }
): ProcurementRequest {
  const estimated = req.estimated_cost ?? req.cost ?? 0;
  return { ...req, estimated_cost: estimated, cost: estimated };
}

async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(
      typeof err.detail === "string"
        ? err.detail
        : JSON.stringify(err.detail ?? err)
    );
  }
  return res.json();
}

export function submitRequest(
  payload: SubmitRequestPayload
): Promise<SubmitResponse> {
  return apiFetch<SubmitResponse>("/submit-request", {
    method: "POST",
    body: JSON.stringify({
      requester_id: "user_requester_1",
      ...payload,
    }),
  }).then(normalizeSubmitResponse);
}

export function extractVendors(requestId: string) {
  return apiFetch("/extract-vendors", {
    method: "POST",
    body: JSON.stringify({ request_id: requestId, use_mock_files: true }),
  });
}

export function scoreVendors(requestId: string) {
  return apiFetch("/score-vendors", {
    method: "POST",
    body: JSON.stringify({ request_id: requestId }),
  });
}

export function approveRequest(requestId: string, approverId: string) {
  return apiFetch("/approve", {
    method: "POST",
    body: JSON.stringify({ request_id: requestId, approver_id: approverId }),
  });
}

export function rejectRequest(
  requestId: string,
  approverId: string,
  reason?: string
) {
  return apiFetch("/reject", {
    method: "POST",
    body: JSON.stringify({
      request_id: requestId,
      approver_id: approverId,
      reason,
    }),
  });
}

export function generatePO(requestId: string) {
  return apiFetch("/generate-po", {
    method: "POST",
    body: JSON.stringify({ request_id: requestId }),
  });
}

export function threeWayMatch(
  requestId: string,
  invoiceAmount?: number,
  receiptQty?: number
) {
  return apiFetch("/three-way-match", {
    method: "POST",
    body: JSON.stringify({
      request_id: requestId,
      invoice_amount: invoiceAmount,
      receipt_qty: receiptQty,
    }),
  });
}

export async function listRequests(params?: {
  status?: string;
  approval_tier?: string;
  approver_role?: "manager" | "finance";
}): Promise<ProcurementRequest[]> {
  const q = new URLSearchParams();
  if (params?.status) q.set("status", params.status);
  if (params?.approval_tier) q.set("approval_tier", params.approval_tier);
  if (params?.approver_role) q.set("approver_role", params.approver_role);
  const qs = q.toString();
  const data = await apiFetch<ProcurementRequest[]>(
    `/requests${qs ? `?${qs}` : ""}`
  );
  return data.map(normalizeProcurementRequest);
}

/** Requests with PO + three-way match finished (matched or complete). */
export async function listCompletedRequests(): Promise<ProcurementRequest[]> {
  const batches = await Promise.all(
    COMPLETED_STATUSES.map((status) => listRequests({ status }))
  );
  const byId = new Map<string, ProcurementRequest>();
  for (const batch of batches) {
    for (const req of batch) {
      if (isRequestComplete(req) && req.po) {
        byId.set(req.id, req);
      }
    }
  }
  return Array.from(byId.values());
}

export function getRequest(requestId: string): Promise<ProcurementRequest> {
  return apiFetch<ProcurementRequest>(`/requests/${requestId}`).then(
    normalizeProcurementRequest
  );
}
