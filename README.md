# Procurement Automation System

An end-to-end AI-powered procurement pipeline that automates vendor sourcing, budget validation, approval routing, PO generation, and invoice matching — with a human-in-the-loop checkpoint for high-value requests.

**Live Demo:** [YOUR_VERCEL_URL] &nbsp;|&nbsp; **API Docs:** [YOUR_RENDER_URL]/docs &nbsp;|&nbsp; **GitHub:** [github.com/HarshitB0409/procurement-automation](https://github.com/HarshitB0409/procurement-automation)

---

## What It Does

A requester submits a procurement request (item, quantity, estimated budget, department). The system then:

1. **Validates budget** — checks remaining budget for the department against Firestore
2. **Routes for approval** — auto-approves small requests, escalates large ones to Manager or Finance queue
3. **Extracts vendor quotes** — parses unstructured vendor text files using GPT-4o-mini into structured JSON
4. **Scores vendors** — ranks vendors by weighted formula: price (50%) + speed (30%) + SLA rating (20%)
5. **Generates justification** — GPT-4o-mini writes a human-readable audit paragraph explaining the winning vendor
6. **Human checkpoint** — approver reviews vendor scorecard and approves or rejects (high-value requests only)
7. **Generates PO** — creates a Purchase Order in Firestore and deducts from department budget
8. **Three-way match** — compares PO total == Goods Receipt total == Invoice total, flags exceptions

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) + Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | Firebase Firestore |
| LLM | OpenAI GPT-4o-mini |
| PDF / Text Parsing | PyMuPDF (fitz) |
| Deployment | Vercel (frontend) + Render (backend) |

---

## Pipeline Flow

```
Submit Request
      │
      ▼
Budget Check ──── FAIL ──▶ status: budget_failed
      │
     PASS
      │
      ▼
Extract Vendor Quotes (GPT-4o-mini)
      │
      ▼
Score Vendors (weighted formula)
      │
      ▼
Generate Justification (GPT-4o-mini)
      │
      ▼
Approval Routing
      │
      ├── auto_approved (<$5k) ──▶ Generate PO ──▶ Three-Way Match ──▶ COMPLETE
      │
      ├── pending_manager ($5k–$20k) ──▶ [Human Approves] ──▶ Generate PO ──▶ COMPLETE
      │                                └─ [Human Rejects] ──▶ status: rejected
      │
      └── pending_finance (≥$20k) ──▶ [Human Approves] ──▶ Generate PO ──▶ COMPLETE
                                     └─ [Human Rejects] ──▶ status: rejected
```

---

## Approval Rules

| Estimated Cost | Tier | Human Review |
|---|---|---|
| < $5,000 | auto_approved | Skipped — pipeline completes automatically |
| $5,000 – $19,999 | needs_manager | Manager must approve before PO |
| ≥ $20,000 | needs_finance | Finance must approve before PO |

Budget is only deducted on confirmed approval — never on submission or rejection.

---

## Project Structure

```
/
├── frontend/                  # Next.js app
│   ├── app/
│   │   ├── page.tsx           # Requester intake form
│   │   └── approver/
│   │       └── page.tsx       # Approver dashboard (manager + finance queues)
│   └── lib/
│       └── api.ts             # FastAPI client functions
│
├── backend/                   # FastAPI app
│   ├── main.py                # App entry, CORS, router registration
│   ├── pipeline.py            # Sequential orchestration
│   ├── firebase.py            # Firestore client
│   ├── models.py              # Pydantic schemas
│   ├── seed.py                # Seed Firestore collections
│   ├── routers/
│   │   ├── intake.py          # POST /submit-request
│   │   ├── extraction.py      # POST /extract-vendors
│   │   ├── scoring.py         # POST /score-vendors
│   │   ├── approval.py        # POST /approve, POST /reject
│   │   ├── po.py              # POST /generate-po, POST /three-way-match
│   │   └── requests.py        # GET /requests, GET /requests/{id}
│   └── services/
│       ├── approval_rules.py  # Threshold logic
│       ├── approval_service.py
│       ├── budget.py          # check_budget, deduct_budget
│       ├── extraction_service.py
│       ├── justification_service.py
│       ├── pdf_parser.py      # PyMuPDF + price derivation
│       ├── po_service.py
│       ├── request_store.py
│       └── scoring_service.py
│
└── mock_data/                 # Sample vendor quote files
    ├── vendor_quote_1.txt
    ├── vendor_quote_2.txt
    └── vendor_quote_3.txt
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Firebase project with Firestore enabled ([setup guide](https://firebase.google.com/docs/firestore/quickstart))
- OpenAI API key

### 1. Clone

```bash
git clone https://github.com/HarshitB0409/procurement-automation.git
cd procurement-automation
```

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env`:

```env
OPENAI_API_KEY=your_openai_key
FIREBASE_PROJECT_ID=your_firebase_project_id
GOOGLE_APPLICATION_CREDENTIALS=serviceAccountKey.json
USE_MOCK_DB=false
```

Place your Firebase service account JSON at `backend/serviceAccountKey.json`.

> **No Firebase?** Set `USE_MOCK_DB=true` to run fully in-memory with no credentials needed. Data resets on server restart.

```bash
python seed.py
uvicorn main:app --reload --port 8000
```

API docs available at [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
```

Edit `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

```bash
npm run dev
```

| URL | Page |
|---|---|
| http://localhost:3000 | Requester intake form |
| http://localhost:3000/approver | Approver dashboard |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/submit-request` | Submit procurement request, runs full pipeline |
| POST | `/extract-vendors` | Parse vendor quote files → structured JSON |
| POST | `/score-vendors` | Score and rank vendors by weighted formula |
| POST | `/approve` | Approve a pending request, deducts budget |
| POST | `/reject` | Reject a pending request, no budget change |
| POST | `/generate-po` | Generate Purchase Order in Firestore |
| POST | `/three-way-match` | Compare PO / Receipt / Invoice totals |
| GET | `/requests` | List all requests |
| GET | `/requests/{id}` | Get single request with full pipeline state |

---

## Seed Data

```bash
python seed.py
```

Creates the following in Firestore:

**Users**

| ID | Name | Role |
|---|---|---|
| user_requester_1 | Alice Requester | requester |
| user_manager_1 | Bob Manager | manager |
| user_finance_1 | Carol Finance | finance |

**Budgets**

| Department | Total |
|---|---|
| IT | $100,000 |
| HR | $50,000 |
| Operations | $75,000 |

**Vendors**

| Name | SLA Rating | Compliant |
|---|---|---|
| Acme Supplies Co. | 4.0 | Yes |
| TechDirect Inc. | 4.5 | Yes |
| Global IT Partners | 3.8 | Yes |

---

## Deployment

### Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → New Project → Import this repo
2. Set Root Directory to `frontend`
3. Add environment variable: `NEXT_PUBLIC_API_URL=https://YOUR_RENDER_URL`
4. Deploy

### Backend → Render

1. Go to [render.com](https://render.com) → New Web Service → Connect this repo
2. Set Root Directory to `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `OPENAI_API_KEY`
   - `FIREBASE_PROJECT_ID`
   - `USE_MOCK_DB=false`
   - `FIREBASE_CREDENTIALS_JSON` — paste entire contents of `serviceAccountKey.json`

> Render free tier spins down after 15 minutes of inactivity. Open the service URL once before demoing to warm it up.

---

## Running Tests

```bash
cd backend
python test_e2e.py
```

Covers auto-approve path (< $5k) and manager approval path ($8k) end to end.