# Job Application Assessment: AI Prompt Sequence

This document contains a structured sequence of prompts designed to leverage an AI assistant (like Gemini or ChatGPT) to build a production-grade FastAPI service. 

**Strategy:** "Senior Engineer Speed-Run" — Demonstrate architectural competence, security, and operational maturity while using AI to accelerate implementation.

---

## Phase 1: High-Velocity Boilerplate
**Goal:** Establish a production-ready foundation immediately.

> "I'm building a reference architecture for a FastAPI webhook service for a technical assessment. I need a production-grade directory structure setup immediately.
> 
> Generate a scaffold with:
> - `app/` folder with `main`, `config`, `models`, `storage`.
> - A `config.py` using `pydantic-settings` that strictly enforces 12-factor principles (fails without secrets).
> - A `requirements.txt` with `fastapi`, `uvicorn`, `prometheus-client`.
> 
> Keep it minimal but extensible. I'll fill in the logic next."

---

## Phase 2: Domain Modeling & Validation (Precision)
**Goal:** enforcing strict data contracts and database constraints.

> "The implementation needs to parse this exact JSON schema (WhatsApp-style). 
> 
> Generate the `Pydantic` models for `app/models.py`. 
> **Constraint:** Use regex to strictly validate E.164 phone numbers and `ISO-8601` timestamps. 
> Also, provide a SQLite initialization script that ensures the `message_id` is a Primary Key to strictly enforce idempotency at the database level."

---

## Phase 3: Core Logic & Security (The "Hard" Part)
**Goal:** Implement robust security controls for HMAC validation.

> "I need a robust dependency for HMAC-SHA256 signature verification in `app/main.py`.
> 
> Implementation details:
> 1. It must read the `raw` bytes of the request body (before JSON parsing).
> 2. Use `hmac.compare_digest` to prevent timing attacks.
> 3. Raise a clean `401 Unauthorized` if it fails.
> 
> This is a critical security control, so ensuring it runs *before* any other processing is efficient."

---

## Phase 4: Observability & Ops (Differentiation)
**Goal:** Demonstrate "Day 2" operational maturity.

> "To demonstrate operational maturity, I want to bake in observability from the start.
> 
> 1. Provide a `logging_utils.py` that formats logs as single-line JSON with `request_id` and latency.
> 2. Provide a `metrics.py` hook using `prometheus-client` to count HTTP requests and specific webhook outcomes (`created` vs `duplicate`).
> 
> I want the reviewer to see I'm thinking about production support."

---

## Phase 5: Testing Strategy (Quality Assurance)
**Goal:** Provide proof of correctness.

> "I need a comprehensive test suite to prove correctness to the reviewers.
> 
> Generating `tests/test_webhook.py` using `pytest`. Coverage must include:
> 1. Valid signature + fresh message -> 200 OK.
> 2. Valid signature + duplicate message -> 200 OK (Idempotency check).
> 3. Invalid signature -> 401 Unauthorized.
> 
> Use a `:memory:` SQLite database for the fixture so tests are fast and isolated."

---

## Phase 6: Packaging (The Deliverable)
**Goal:** Ensure the reviewer has a zero-friction experience running the code.

> "Final step: Containerization.
> 
> Create a multi-stage `Dockerfile` and a `docker-compose.yml`.
> **Crucial:** Include a `Makefile` with a `make up` target that builds and runs everything. 
> I want the 'How to Run' section in the `README.md` to be one line: `make up`. This reduces friction for the person grading the assignment."
