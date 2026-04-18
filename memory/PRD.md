# enCARE Healthcare CRM - PRD

## Original Problem Statement
Build a Healthcare CRM module for enCARE MEDI REMINDER app. The CRM is an allied platform used by Healthcare Assistants to manage patients, monitor health vitals, track medicine adherence, and generate revenue by smartly suggesting medicine refills, healthcare products, lab tests, and services. Must NOT modify the main enCARE app.

## User Personas
1. **Healthcare Assistant** - Primary user who manages patients, makes calls, logs interactions
2. **Patients** - Individuals with chronic conditions needing care management
3. **Admin** - Manages assistant accounts and settings (future)

## Core Requirements (Static)
- Patient management with full profile, medicines, caregivers
- Automatic disease detection from medicines
- Health vitals tracking (BP, Sugar, Weight) with charts
- Product suggestions based on diseases
- Lab test booking and due date tracking
- Interaction logging (calls, messages, visits)
- Opportunity management for revenue generation
- Dashboard with Next Best Action guidance
- Data models strictly aligned with enCARE app structure

## What's Been Implemented

### Date: April 16, 2026 — API Sync Endpoints & Onboarding Profile (NEW)

#### API Sync Endpoints (Mock enCARE Data Pull)
- `GET /api/sync/encare-patients` — Lists available patients in simulated enCARE system with sync status
- `POST /api/sync/patient/{encare_user_id}` — Import/sync patient profile + medicines from enCARE (creates or updates)
- `POST /api/sync/medications/{encare_user_id}` — Re-sync medications for already-imported patient
- `POST /api/sync/vitals/{encare_user_id}` — Sync blood glucose + blood pressure readings from enCARE
- `GET /api/sync/status` — Global sync activity log
- `GET /api/sync/status/{patient_id}` — Patient-specific sync status with logs
- Mock data: 3 enCARE patients (ENC001: Arjun Mehta, ENC002: Lakshmi Iyer, ENC003: Mohammed Faiz)
- Sync logs stored in `sync_logs` MongoDB collection
- Patients tagged with `encare_user_id`, `last_synced_at`, `sync_source` fields

#### Onboarding Profile Update Page
- `GET /api/patients/{id}/onboarding` — Returns structured onboarding profile with all enCARE-aligned fields
- `PUT /api/patients/{id}/onboarding` — Full profile update (personal, address, medical, caregiver, invoice)
- Auto-updates caregivers array from relative fields
- Auto-manages "Elderly Care" disease for age >= 65
- Frontend: `/patients/:id/onboarding` route with multi-section form
- Sync status bar for enCARE-linked patients with one-click sync buttons
- "Edit Profile" button added to Patient Detail header

#### Sync Dashboard Page
- New `/sync` route with "enCARE Sync" nav item in sidebar
- Lists all available enCARE patients with sync status (Synced/Not Synced)
- "Import to CRM" button for new patients
- "Re-sync Meds" and "Sync Vitals" for already-synced patients
- Sync Activity Log showing all sync operations

### Date: April 17, 2026 — Interaction Purpose Field
- Added "Purpose" dropdown to Log Interaction dialog (10 options: Medicine Refill Reminder, Health Checkup Follow-up, Lab Test Reminder, etc.)
- Purpose saved in backend Interaction model and displayed as teal badge in Interaction History

### Date: April 17, 2026 — Marketing Consent Feature
- New "Marketing Consent" section in onboarding with 3 levels: Open, Moderate, Do Not Contact
- Consent badge visible on Patient Detail header and Patient List cards
- Products tab disabled for "Do Not Contact" patients; warning banner shown for "Moderate" patients
- Backend stores `marketing_consent` field via onboarding PUT endpoint

### Date: April 17, 2026 — Visit Date → Appointment History + Next Due Dates
- Onboarding last doctor/lab visit dates auto-create "done" appointment records in appointment history
- Backend calculates next due dates (90-day intervals) returned via GET /api/patients/{id}
- Patient Detail Medical Information card shows color-coded due date indicators (overdue=red, upcoming=blue/green)

### Date: April 17, 2026 — Medical Information Section Redesign
- Redesigned Onboarding Profile "Medical Information" as a healthcare executive checklist
- New fields: Main Disease, Consulting Doctor, Clinic/Hospital, Last Doctor Visit, Regular Lab, Last Lab Visit, Mobility Status, Other Critical Info
- Removed Diabetes Type and Adherence Rate from the section
- Auto-detected diseases remain read-only at top
- Medical Information summary card added to Patient Detail page (visible only when data exists)

### Date: April 17, 2026 — Bug Fix: Diseases not showing on Onboarding Profile
- Fixed: Medical Information section's "Detected Diseases" was blank because `diseases` from API response was never mapped to component state
- Added separate `diseases` state variable populated from onboarding API response

### Date: April 16, 2026 — Live Search on Patients Page
- Search now filters patients automatically as you type (debounced 300ms)
- No button click required; removed form submission wrapper

### Date: April 16, 2026 — Priority Reason Tooltip
- Hovering over patient priority badge shows tooltip with reason for classification

### Date: April 16, 2026 — Bug Fix: Quick Actions → Opportunities Navigation
- Fixed: Dashboard Quick Action cards used plural types but DB has singular

### Date: April 16, 2026 — Post-Visit Feedback Calls
- Feedback call entries auto-appear in Daily Task List for past bookings

### Date: April 16, 2026 — Doctor Booking Feature
- New "Doctor Booking" tab in Patient Detail

### Date: April 15, 2026 — Daily Task List Rework
- "Patients to Call Today" → "Daily Task List" with individual task entries

### Date: February 13, 2026 — Custom Lab Tests in Recommendations Fix
- Fixed P0 bug: Custom lab tests now appear in Patient's Recommended Lab Tests

### Date: February 12, 2026 — Lab Tests & Laboratories Enhancement
- Lab Tests page reorganized into 3 tabs

### Date: February 12, 2026 — Medicine Add/Edit/Delete Feature
- Medicine CRUD in PatientDetail Medicines tab

### Backend (FastAPI + MongoDB)
- Patient CRUD APIs with search/filter by disease, priority
- Split vitals: BloodGlucose, BloodPressure, BodyMetrics (separate collections)
- Medicine CRUD with disease auto-detection
- Lab test booking & management
- Opportunity generation with 5 types
- Sync endpoints with mock enCARE data
- Onboarding profile endpoints

### Frontend (React + Tailwind + Shadcn UI)
- Dashboard with stat cards, Quick Actions, Daily Task List
- Patients page with search, disease/priority filters
- Patient Detail with 6 tabs (Medicines, Vitals, Products, Lab Tests, Interactions, Doctor Booking)
- Onboarding Profile page (multi-section form with sync status)
- Sync Dashboard page (import/sync from enCARE)
- Opportunities page with type/status filters
- Lab Tests page with 3 tabs

### Design
- enCARE theme: Teal gradient header (#009688 → #4CAF50)
- Coral CTA gradient (#F44336 → #FF5722)
- Manrope + IBM Plex Sans fonts
- shadcn/ui components

## Architecture
```
Backend: FastAPI + Motor (MongoDB Async)
Frontend: React + Tailwind + shadcn/ui + Recharts
Database: MongoDB (patients, blood_glucose, blood_pressure, body_metrics, appointments, lab_bookings, opportunities, sync_logs, custom_lab_tests, lab_test_overrides, laboratories)
AI: Gemini via Emergent LLM Key (disease detection)
```

## Prioritized Backlog

### P0 (Critical - Done)
- Patient management with enCARE-aligned models
- Disease detection from medicines
- Vitals monitoring with split collections and charts
- Product & lab test suggestions
- Opportunity dashboard with 5 types
- Invoice tracking display
- API Sync Endpoints (mock enCARE data pull) ✅
- Onboarding Profile Update Page ✅

### P1 (High Priority - Next)
- Commission tracking per assistant
- Healthcare Assistant authentication/login
- Purchase order creation flow
- Real enCARE API integration (replace mock data)

### P2 (Medium Priority)
- WhatsApp/SMS integration for patient notifications
- Payment gateway (Razorpay) for orders
- Admin dashboard for multiple assistants
- Automated reminder scheduling

### P3 (Low Priority)
- Insurance management
- Bundle product creation
- Analytics and reporting dashboard

### Date: April 17, 2026 — UI Bug Fixes
- Fixed Log Interaction dialog overflow: added `max-h-[85vh]`, flex column layout with scrollable body, border-separated header & footer so title and buttons are always fully visible
- Fixed Onboarding Profile sticky bottom bar: replaced `sticky bottom-4` with a full-width sticky bar with `bg-white/95 backdrop-blur`, border-t separator, and proper z-index

## Next Tasks
1. Comprehensive E2E testing pass using testing_agent_v3_fork (deferred from previous session)
2. Add commission tracking per assistant
3. Add assistant authentication with JWT
4. Create purchase order flow for refills/products
5. Replace mock sync with real enCARE API integration
