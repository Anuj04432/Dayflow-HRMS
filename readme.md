# Dayflow — Human Resource Management System

> **Every workday, perfectly aligned.**

Dayflow is a modern, full-stack **Human Resource Management System (HRMS)** built as an **Odoo Hackathon project**. It combines an enterprise-grade Odoo backend with a high-performance, mobile-responsive web portal. Dayflow digitizes, automates, and streamlines critical daily workforce operations — from authentication and biometric attendance to leave management, profile management, dynamic payroll calculation, and executive dashboard analytics.

---

## 📌 1. The Problem

Traditional workforce management is plagued by operational friction:
* **Fragmented Systems & Spreadsheets**: Attendance, time-off requests, and payroll records often exist in isolated spreadsheets, causing data mismatches and manual reconciliation overhead.
* **Lack of Employee Self-Service**: Employees struggle to check their attendance status, verify PTO balances, or access salary vouchers without contacting HR departments.
* **Delayed Approval Workflows**: Leave applications submitted over email or paper lack audit trails and require manual status updates in daily attendance records.
* **Opaque Salary Structures**: Static, hardcoded payroll systems lack live gross-to-net salary recalculations and instant payslip generation.
* **Absence of Real-Time Workforce Visibility**: HR managers lack instant metrics on daily active headcount, today's absences, pending approvals, and company-wide compensation expenditure.

---

## 💡 2. The Solution

**Dayflow HRMS** delivers an integrated, role-based platform connecting Employees and HR Administrators:
1. **Interactive Self-Service Portals**: Dedicated, personalized dashboards for Employees and HR Officers.
2. **Automated Attendance Lifecycle**: Instant digital check-in/check-out with daily timestamp logs, worked hours computation, and weekly schedule breakdowns.
3. **Synchronized Leave Approvals**: Multi-type time-off requests (`Paid`, `Sick`, `Unpaid`) with conflict detection, HR review queue, and **automatic attendance synchronization** upon approval.
4. **Transparent & Dynamic Payroll**: Real-time salary structure breakdown ($Gross = Basic + HRA + Allowances$, $Net = Gross - Deductions$), printable payslip generation, and HR salary adjustment controls.
5. **Fast & Secure Communication**: Low-latency REST JSON APIs, multi-threaded server architecture, and 6-digit numeric Email OTP account verification.

---

## 🚀 3. Key Features (Actually Implemented)

### 🔐 1. Authentication & Security
* **Role-Based Access Control (RBAC)**: Strict permission boundaries separating regular **Employees** from **HR Administrators**.
* **6-Digit Email OTP Verification**: Cryptographically secure numeric OTP generation with a 10-minute validity window, 45-second rate-limiting cooldown, and brute-force lockout protection (5 attempts).
* **Dual-Mode Delivery**: Live SMTP delivery (Gmail, Outlook, custom SMTP) with automatic on-screen developer mode fallbacks.
* **Session Management**: Secure user sessions with protected routes and automatic redirection.

### 👤 2. Employee Profile & Self-Service
* **Workforce Directory**: Searchable company directory with department filters.
* **Detailed Profile View**: Comprehensive view of personal details, job title, department, work email, and contact info.
* **Interactive Profile Editing**: Permitted field modification (`phone`, `address`, and live base64 profile picture upload) for employees, with full administrative editing privileges for HR.

### 🕒 3. Time & Attendance Management
* **One-Click Check-In / Check-Out**: Real-time clocking with automatic daily worked hours calculation.
* **Interactive Tab Switcher (Daily vs. Weekly)**:
  - **Daily View**: Historical logs of check-in/out timestamps and status badges (`PRESENT`, `LEAVE`, `HALF_DAY`, `ABSENT`).
  - **Weekly View**: 7-day calendar schedule (Monday through Sunday) with daily breakdowns, weekend classification, and **Total Weekly Worked Hours** summation.
* **HR Company Attendance Monitor**: Live company-wide attendance tracking with search and department filtering.

### 📅 4. Leave & Time-Off Management
* **Leave Application Engine**: Time-off submission supporting Paid Time Off (PTO), Sick Leave, and Unpaid Leave.
* **Date & Conflict Validation**: Automated validation preventing reverse date ranges and overlapping active requests.
* **HR Approval Queue**: Dedicated review portal with one-click **Approve** and **Reject** actions (with mandatory rejection remarks).
* **Attendance Auto-Sync**: Approved leaves covering the current date automatically update today's attendance state to `LEAVE`.

### 💰 5. Dynamic Payroll & Salary Management
* **Automated Salary Calculation**:
  $$\text{Gross Salary} = \text{Basic Salary} + \text{HRA} + \text{Special Allowance}$$
  $$\text{Net Salary} = \max(0, \text{Gross Salary} - \text{Statutory Deductions})$$
* **No Hardcoded Data**: Automatic database-first provisioning ensuring every registered employee has an active payroll record.
* **One-Click Printable Payslip**: Instant printable/downloadable salary voucher with earnings and deductions breakdown.
* **HR Company Payroll Overview**: Company-wide payroll table with total expenditure KPIs and modal salary structure editor.

### 📊 6. Dashboards, Analytics & Reports
* **HR Executive Dashboard**: Real-time KPI counters (Total Workforce, Present Today, On Leave, Absent, Pending Approvals, Monthly Payroll) + 4 interactive Chart.js visualization panels.
* **Employee Dashboard**: Personal KPI summaries, weekly hours worked trend line chart, and monthly attendance distribution gauge.
* **System Alerts & Notifications**: Dynamic notification center for leave status updates, payroll dispatches, and attendance alerts.
* **Attendance Reports**: Visual progress meters displaying company attendance ratios and policy compliance.

---

## 👥 4. How Dayflow Helps

### 👤 For Employees
* **Instant Attendance Clocking**: Check in and check out in 1 click without paper registers.
* **Weekly Schedule Visibility**: Track total hours worked across the current week at a glance.
* **Hassle-Free Time-Off**: Apply for leaves, provide reasons, and track real-time approval status and HR remarks.
* **Transparent Compensation**: Inspect personal salary breakdowns and download official payslips anytime.
* **Self-Service Profile Maintenance**: Update contact phone numbers, addresses, and avatar photos directly.

### 👑 For HR Officers & Administrators
* **Centralized Workforce Management**: Complete control over employee records, roles, and department assignments.
* **Real-Time Attendance Monitoring**: Instant visibility into who is clocked in, on leave, or absent today.
* **Streamlined Approval Workflows**: Review, approve, or reject employee leave requests with custom feedback.
* **Dynamic Compensation Management**: Adjust salary structures, calculate net salaries automatically, and monitor total monthly payroll costs.
* **Executive Decision Making**: Interactive charts and data visualizations provide instant operational insights.

---

## 🏗️ 5. System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND PRESENTATION LAYER                     │
│  HTML5 + Modern CSS Mesh Gradients + Vanilla ES6+ JavaScript + Chart.js │
│  (Employee & HR Dashboards, Attendance, Leave, Payroll, Profile, Auth) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST JSON (CORS Enabled)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        REST API & CONTROLLER LAYER                     │
│               dayflow/controllers/ & Multi-Threaded Dev Server         │
│  ├── /api/auth/*        (OTP Generation, Verification, Signup, Login)  │
│  ├── /api/employee/*    (Profile Retrieval, Permitted Updates, List)   │
│  ├── /api/attendance/*  (Check-In/Out, Daily/Weekly Logs, Company Log) │
│  ├── /api/leave/*       (Apply, Pending Queue, Approve/Reject Action)  │
│  ├── /api/payroll/*     (Salary Info, Company Overview, Salary Update) │
│  └── /api/dashboard/*   (Aggregated KPIs, Notifications, Reports)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ ORM Calls / Model Operations
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      ODOO BUSINESS MODELS & SECURITY                   │
│                               dayflow/models/                          │
│  ├── dayflow.employee    (Personal, Job & Administrative Records)      │
│  ├── dayflow.attendance  (Daily/Weekly Time Logs & Worked Hours)       │
│  ├── dayflow.leave       (Time-Off Requests & State Machine)           │
│  ├── dayflow.payroll     (Salary Breakdown & Auto Calculation)         │
│  └── res.users           (RBAC Roles, Security Rules & Access Lists)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ SQL Queries / ACID Transactions
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                             DATABASE LAYER                             │
│                  PostgreSQL (Production) / In-Memory (Dev)             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 6. Project Structure

```text
Dayflow-HRMS/
│
├── css/
│   └── style.css                   # Master stylesheet (Mesh gradients, responsive cards, modals, themes)
│
├── js/
│   ├── chart.min.js                # Locally bundled Chart.js (Zero-latency offline data visualization)
│   └── script.js                   # Core frontend controller (REST API client, state, auth, DOM binding)
│
├── frontend/
│   ├── index.html                  # Sign-in portal with 3D SaaS hero illustration & demo autofill
│   ├── signup.html                 # 2-Step registration portal with 6-digit email OTP verification
│   ├── verify-email.html           # Standalone OTP verification & account activation screen
│   ├── employee-dashboard.html     # Employee KPI cards, weekly worked hours trend & attendance doughnut
│   ├── hr-dashboard.html           # HR executive portal with workforce metrics & 4 analytic charts
│   ├── attendance.html             # Daily check-in/out & interactive daily/weekly attendance logs
│   ├── leave.html                  # Leave application form & HR approval/rejection queue
│   ├── payroll.html                # Personal salary voucher & HR company-wide compensation manager
│   ├── profile.html                # Employee profile card & interactive "Edit Profile" modal
│   ├── notifications.html          # Dynamic system alerts (Approvals, dispatches, reminders)
│   └── reports.html                # Attendance ratio meters & exportable analytics
│
├── dayflow/                        # Official Odoo HRMS Addon Module
│   ├── __init__.py                 # Module initialization
│   ├── __manifest__.py             # Odoo manifest metadata, dependencies, and view declarations
│   ├── controllers/                # REST API endpoints & request handlers
│   │   ├── __init__.py
│   │   ├── common.py               # JSON response helpers, CORS handling & auth context
│   │   ├── auth.py                 # Authentication, OTP generation & email verification
│   │   ├── employee.py             # Employee profiles, permitted editing & workforce directory
│   │   ├── attendance.py           # Attendance check-in/out & daily/weekly logs
│   │   ├── leave.py                # Leave applications, validations & HR approval actions
│   │   ├── payroll.py              # Salary structure calculations & company payroll
│   │   └── dashboard.py            # Aggregated KPI metrics, alerts & report statistics
│   ├── models/                     # Odoo ORM data models
│   │   ├── __init__.py
│   │   ├── hr_employee.py          # Employee entity with RBAC-controlled permitted updates
│   │   ├── hr_attendance.py        # Attendance records with automated worked hours computation
│   │   ├── hr_leave.py             # Leave entity with state machine & attendance sync hooks
│   │   ├── hr_payroll.py           # Payroll entity with automatic Gross/Net salary compute
│   │   └── res_users.py            # Extended user model with verification tokens & roles
│   ├── security/                   # Access rights and security definitions
│   │   ├── security.xml            # User groups (Employee vs. HR Officer) & record rules
│   │   └── ir.model.access.csv     # Model-level ACL permission matrix
│   ├── data/
│   │   └── ir_sequence_data.xml    # Automatic employee code generator (DF0001, DF0002, ...)
│   ├── views/
│   │   └── menu_views.xml          # Odoo backend menus, actions, and tree/form views
│   └── tests/                      # Python automated unit test suite (38 test cases)
│       ├── __init__.py
│       ├── test_auth.py            # Auth & OTP unit tests
│       ├── test_employee.py        # Employee profile & RBAC unit tests
│       ├── test_attendance.py      # Attendance calculation unit tests
│       ├── test_leave.py           # Leave workflow & state transition unit tests
│       └── test_payroll.py         # Payroll auto-calculation unit tests
│
├── run_dev.py                      # 1-Command Full-Stack multi-threaded dev server (Ports 8000 & 8069)
├── test_backend.py                 # Standalone backend test runner & API mock specification server
├── pyproject.toml                  # Python package configuration & project metadata
└── README.md                       # Comprehensive project documentation
```

---

## 💻 7. Technology Stack

| Layer | Technologies & Tools |
| :--- | :--- |
| **Backend Framework** | **Odoo 17 / 18**, Python 3.10+ |
| **Database** | **PostgreSQL** (Production) / Multi-Threaded In-Memory Store (Dev) |
| **Web API** | RESTful JSON APIs, HTTP CORS, Cryptographic OTP Generator |
| **Frontend UI** | HTML5, Modern CSS (Ambient Mesh Gradients, Responsive Flexbox/Grid), Vanilla JavaScript (ES6+) |
| **Data Visualization** | **Chart.js** (Locally bundled in `js/chart.min.js` for 0ms network latency) |
| **Server Runtime** | Python `ThreadingHTTPServer` (Multi-threaded non-blocking concurrent request handling) |
| **Testing** | Python `unittest` framework & custom HTTP API integration suite |

---

## ⚡ 8. Quick Start & Setup Instructions

### 🚀 Option A: 1-Command Fast Development Mode (Recommended)
You can run the entire Dayflow HRMS application locally without requiring a heavy Odoo/PostgreSQL installation:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Anuj04432/Dayflow-HRMS.git
   cd Dayflow-HRMS
   ```

2. **Start the Full-Stack Multi-Threaded Server**:
   ```bash
   python run_dev.py
   ```
   * *Backend API Server*: `http://127.0.0.1:8069`
   * *Frontend Web Portal*: `http://127.0.0.1:8000`

3. **Open in Your Browser**:
   👉 **[http://localhost:8000/frontend/index.html](http://localhost:8000/frontend/index.html)**

4. **Sign In with Pre-Configured Demo Accounts**:
   * 👑 **HR Officer / Administrator**: `hr@dayflow.com` / `password123`
   * 👤 **Regular Employee**: `employee@dayflow.com` / `password123`

---

### 🏢 Option B: Full Odoo Enterprise/Community Installation

1. **Prerequisites**:
   * Python 3.10+
   * PostgreSQL server running
   * Odoo 17.0 or 18.0 installed

2. **Link the `dayflow` Addon**:
   Copy or symlink the `dayflow/` directory into your Odoo `custom_addons` directory:
   ```bash
   # Add dayflow to your addons_path in odoo.conf
   addons_path = /path/to/odoo/addons,/path/to/Dayflow-HRMS
   ```

3. **Install the Module in Odoo**:
   ```bash
   odoo-bin -c odoo.conf -d dayflow_db -i dayflow
   ```

4. **Access the Application**:
   * Odoo Native Interface: `http://localhost:8069/web`
   * Dayflow Dedicated Frontend: `http://localhost:8000/frontend/index.html`

---

### 🧪 9. Running Automated Test Suites

Dayflow HRMS includes two automated testing suites:

```bash
# 1. Run all 38 Odoo/Model Unit Tests:
python -m unittest discover -s dayflow/tests

# 2. Run all 13 Backend Specification & Acceptance Criteria Tests:
python test_backend.py
```

#### ✅ Test Verification Checklist
* `38 / 38` Unit tests pass (`OK`).
* `13 / 13` Integration tests pass (`100%`).

---

## 📊 10. Current Implementation Status

| Module / Feature | Status | Implementation Details |
| :--- | :---: | :--- |
| **Authentication & RBAC** | ✅ Implemented | Roles (Employee/HR), session handling, route protection. |
| **Email OTP Verification** | ✅ Implemented | 6-digit numeric OTP, 10-min expiry, 45s cooldown, SMTP & dev mode fallback. |
| **Employee Directory** | ✅ Implemented | Searchable workforce directory with department filtering. |
| **Profile Management** | ✅ Implemented | View profiles & interactive "Edit Profile" modal with photo upload. |
| **Attendance Clocking** | ✅ Implemented | Daily check-in/out with automated worked hours calculation. |
| **Weekly Attendance View** | ✅ Implemented | 7-day Monday–Sunday schedule, weekend flags, total weekly hours. |
| **Leave Applications** | ✅ Implemented | PTO, Sick, Unpaid leaves with date & overlap validations. |
| **Leave Approval Queue** | ✅ Implemented | HR review portal with approve/reject actions & comments. |
| **Attendance-Leave Sync**| ✅ Implemented | Approved leaves automatically update daily attendance to `LEAVE`. |
| **Dynamic Payroll** | ✅ Implemented | Real-time Gross/Net calculation, HR editor, printable salary slips. |
| **HR Analytics Dashboard**| ✅ Implemented | Live workforce KPIs + 4 Chart.js visualization panels. |
| **Employee Dashboard** | ✅ Implemented | Weekly worked hours line chart + attendance doughnut gauge. |
| **Notifications & Reports**| ✅ Implemented | System alerts with "Mark All as Read" & attendance progress ratios. |
| **Mobile Responsiveness** | ✅ Implemented | 100% adaptive layouts for smartphones, tablets, and desktops. |

---

## 🏆 11. Hackathon Context

**Dayflow HRMS** was conceived and engineered for the **Odoo HRMS Hackathon**. The primary objective was to demonstrate how Odoo's robust backend data models and security framework can be coupled with a custom, ultra-fast, modern web interface to provide a seamless user experience for both employees and HR leaders.

---

## 🤝 12. Team Ownership & Responsibilities

The project was structured across 4 specialized technical ownership areas:

| Member / Role | Focus Area | Key Deliverables |
| :--- | :--- | :--- |
| **Member 1: Tech Lead & Core Backend** | Core Architecture & Security | Odoo module configuration, base models, RBAC rules, ACLs, and API framework. |
| **Member 2: Attendance & Leave Lead** | Attendance & Leave Systems | Daily/weekly attendance engine, leave state machine, and approval synchronization. |
| **Member 3: Employee & Payroll Lead** | Profile & Payroll Systems | Employee records, permitted profile updates, salary compute engine, and payslip generation. |
| **Member 4: UI, Dashboard & QA Lead** | Frontend UI & Testing | Dashboards, responsive mesh UI, Chart.js integrations, and automated test runners. |

---

## 🔮 13. Future Improvements

* **Biometric Hardware Integration**: Direct webhook sync with physical ZKTeco and RFID fingerprint clocking devices.
* **Automated Statutory Tax Engine**: Dynamic tax slab calculations (e.g. TDS, PF, ESI) customized by jurisdiction.
* **Push & SMS Alerts**: Browser push notifications and SMS OTP delivery integration via Twilio.
* **AI Workforce Insights**: Predictive analytics for employee burnout, unplanned absence forecasting, and leave trend analysis.

---

<div align="center">
  <b>Dayflow HRMS — Every workday, perfectly aligned.</b><br>
  <sub>Engineered with ❤️ for the Odoo Hackathon</sub>
</div>
