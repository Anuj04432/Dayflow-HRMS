# Dayflow – Human Resource Management System

> **Every workday, perfectly aligned.**

Dayflow is an **Odoo-based Human Resource Management System (HRMS)** designed to digitize and streamline core HR operations such as:

* Employee onboarding and profile management
* Authentication and role-based access
* Attendance tracking
* Leave and time-off management
* HR approval workflows
* Payroll/salary visibility
* Admin/HR management

The project is being developed as a team of **4 members** for the Odoo Hackathon.

---

# 1. Project Goal

Build a functional HRMS inside Odoo where two main types of users interact with the system:

### Employee

Employees should be able to:

* Sign in
* View their profile
* View their attendance
* Check in / check out
* Apply for leave
* Track leave status
* View their salary/payroll information
* Edit permitted personal information

### Admin / HR Officer

HR/Admin users should be able to:

* Manage employees
* View employee profiles
* View attendance records
* View leave requests
* Approve/reject leave
* Manage salary information
* View payroll information
* Access HR dashboards

The original specification defines Admin/HR as users with management and approval privileges, while Employees have limited access to their own information.

---

# 2. Team Structure

The project is divided into four major ownership areas.

| Member   | Role                          | Primary Responsibility                                  |
| -------- | ----------------------------- | ------------------------------------------------------- |
| Member 1 | Odoo Backend / Tech Lead      | Core architecture, models, security, roles, integration |
| Member 2 | Attendance & Leave Developer  | Attendance, leave, approval workflows                   |
| Member 3 | Employee & Payroll Developer  | Employee profiles, salary, payroll                      |
| Member 4 | UI / Dashboard / QA Developer | Dashboards, menus, views, UI, testing                   |

Each member owns their assigned functionality but must follow the shared architecture and Git workflow.

---

# 3. IMPORTANT RULE FOR CODING AGENTS

Every coding agent MUST follow this README before making changes.

The agent must:

1. Understand the existing project before modifying it.
2. Work only within the assigned responsibility unless explicitly instructed otherwise.
3. Avoid unnecessarily modifying another member's module.
4. Reuse existing Odoo functionality whenever appropriate.
5. Avoid creating duplicate models or duplicate fields.
6. Follow the existing project structure.
7. Test changes before considering the task complete.
8. Never remove another member's functionality without explicit permission.
9. Never commit API keys, passwords, tokens, `.env` files or secrets.
10. Never directly push to `main`.

---

# 4. Shared Architecture

The system should conceptually follow this structure:

```text
                         DAYFLOW HRMS
                              |
                +-------------+-------------+
                |                           |
             Employee                  Admin / HR
                |                           |
       +--------+--------+        +---------+---------+
       |        |        |        |         |         |
    Profile Attendance Leave   Employees Attendance Leave
       |        |        |        |         |         |
       +--------+--------+        +---------+---------+
                |                           |
                +-------------+-------------+
                              |
                           Payroll
```

The exact implementation should use Odoo's existing HR capabilities wherever possible and customize/extend them only where required by Dayflow.

Do not rebuild existing Odoo functionality from scratch unless there is a clear reason.

---

# 5. Suggested Module Structure

The exact structure may evolve as the team implements the project, but maintain a clean separation of concerns.

```text
dayflow/
│
├── __init__.py
├── __manifest__.py
│
├── models/
│   ├── employee.py
│   ├── attendance.py
│   ├── leave.py
│   └── payroll.py
│
├── views/
│   ├── employee_views.xml
│   ├── attendance_views.xml
│   ├── leave_views.xml
│   ├── payroll_views.xml
│   └── dashboard_views.xml
│
├── security/
│   ├── security.xml
│   └── ir.model.access.csv
│
├── data/
│
├── demo/
│
└── README.md
```

The team may change this structure if the implementation requires it, but changes must be communicated to the other members.

---

# 6. MEMBER 1 — ODOO BACKEND / TECH LEAD

## Branch

```text
feature/core-security
```

## Main responsibility

Member 1 owns the **core Odoo architecture and security**.

This member is also responsible for coordinating integration between the other three members.

---

## Responsibilities

### A. Odoo Module Setup

Create and maintain:

```text
__manifest__.py
__init__.py
models/
security/
views/
```

Configure required dependencies.

Do not add unnecessary dependencies.

---

### B. Core Models

Define or extend the core employee/user relationships required by Dayflow.

Ensure that:

```text
User
  ↓
Employee
  ↓
Attendance
  ↓
Leave
  ↓
Payroll
```

relationships remain consistent.

Before creating a new model, check whether Odoo already provides an appropriate model.

---

### C. Authentication

The specification requires:

* Employee ID
* Email
* Password
* Employee/HR role
* Password security
* Email verification
* Login
* Error handling
* Dashboard redirection

The implementation should use Odoo's existing authentication/user mechanisms wherever possible instead of creating a separate authentication system.

---

### D. Role-Based Access

Create/maintain the main roles:

```text
Employee
HR / Admin
```

Employee permissions:

```text
Own profile
Own attendance
Own leave requests
Own salary information
```

HR/Admin permissions:

```text
All employees
All attendance
Leave approvals
Payroll/salary management
```

Security must be enforced at the Odoo access-control level, not only by hiding UI buttons.

---

### E. Access Control

Maintain:

```text
security/security.xml
security/ir.model.access.csv
```

Ensure that users cannot access records they should not see.

Example:

```text
Employee A
    ↓
Can see Employee A attendance

Employee A
    X
Cannot see Employee B attendance
```

---

### F. Integration

Member 1 is responsible for ensuring that:

* Attendance connects to employees
* Leave connects to employees
* Payroll connects to employees
* Dashboard uses the correct models
* Security rules apply consistently
* Module installation works

---

## Member 1 MUST NOT

Unless explicitly requested:

* Redesign Member 2's attendance logic
* Redesign Member 3's payroll logic
* Redesign Member 4's dashboard
* Delete another member's work

---

# 7. MEMBER 2 — ATTENDANCE & LEAVE

## Branch

```text
feature/attendance-leave
```

## Main responsibility

Member 2 owns:

```text
Attendance
Leave
Approval Workflow
```

---

# 7.1 Attendance

The system requires:

* Daily attendance
* Weekly attendance
* Check-in
* Check-out
* Present
* Absent
* Half-day
* Leave

Employees should only see their own attendance.

HR/Admin should be able to view attendance for all employees.

---

## Attendance flow

```text
Employee
    |
    | Check In
    ↓
Working
    |
    | Check Out
    ↓
Attendance Record
```

The implementation should preserve accurate timestamps and employee relationships.

---

# 7.2 Leave Management

Employees should be able to:

```text
Select Leave Type
       ↓
Select Date Range
       ↓
Add Remarks
       ↓
Submit
```

Leave types required by the specification:

```text
Paid
Sick
Unpaid
```

---

# 7.3 Leave Status

Implement:

```text
Pending
Approved
Rejected
```

Workflow:

```text
Employee
    ↓
Leave Request
    ↓
Pending
    |
    +------> Approved
    |
    +------> Rejected
```

---

# 7.4 HR Approval

HR/Admin should be able to:

* View leave requests
* Approve requests
* Reject requests
* Add comments

Changes should be reflected in employee records.

---

## Member 2 MUST NOT

Unless explicitly requested:

* Modify authentication
* Modify salary logic
* Redesign the dashboard
* Change security architecture

If Member 2 needs a security change, communicate with Member 1.

---

# 8. MEMBER 3 — EMPLOYEE PROFILE & PAYROLL

## Branch

```text
feature/employee-payroll
```

## Main responsibility

Member 3 owns:

```text
Employee Profile
Salary Structure
Payroll Visibility
```

---

# 8.1 Employee Profile

Employees should be able to view:

```text
Personal Details
Job Details
Salary Structure
Documents
Profile Picture
```

---

# 8.2 Employee Editing

Employees can edit only permitted fields:

```text
Address
Phone
Profile Picture
```

Employees must NOT be allowed to modify HR-controlled information such as salary or job information.

---

# 8.3 Admin Editing

Admin/HR should be able to edit employee information as required.

---

# 8.4 Payroll

Employees:

```text
View salary/payroll
        ↓
READ ONLY
```

Admin:

```text
View payroll
       ↓
Update salary structure
```

The payroll implementation should focus on the requirements specified for Dayflow.

Do not unnecessarily build a complete accounting/payroll system if the hackathon requirement only needs salary/payroll visibility and salary structure control.

---

## Member 3 MUST NOT

Unless explicitly requested:

* Modify attendance logic
* Modify leave approval logic
* Modify authentication
* Redesign the dashboard

Coordinate with Member 1 for employee/security relationships.

---

# 9. MEMBER 4 — UI / DASHBOARD / QA

## Branch

```text
feature/dashboard-ui
```

## Main responsibility

Member 4 owns:

```text
Dashboards
Menus
Views
Navigation
UI
Testing
Demo Flow
```

---

# 9.1 Employee Dashboard

The dashboard should provide quick access to:

```text
Profile
Attendance
Leave Requests
Logout
```

It should also show recent activity or alerts where appropriate.

---

# 9.2 Admin / HR Dashboard

The dashboard should provide access to:

```text
Employee List
Attendance Records
Leave Approvals
Employee Selection/Switching
Payroll
```

---

# 9.3 Odoo Views

Create appropriate:

```text
List Views
Form Views
Kanban Views
Search Views
Menus
Actions
Buttons
Filters
```

Do not create UI that depends on models or fields that do not exist.

---

# 9.4 QA Responsibility

Member 4 should test the complete application continuously.

### Employee test

```text
Login
 ↓
Dashboard
 ↓
Profile
 ↓
Attendance
 ↓
Check In
 ↓
Check Out
 ↓
Leave
 ↓
Apply
 ↓
View Leave Status
 ↓
View Salary
```

### HR test

```text
Login
 ↓
Dashboard
 ↓
Employees
 ↓
Attendance
 ↓
Leave Requests
 ↓
Approve/Reject
 ↓
Payroll
 ↓
Update Salary
```

---

# 9.5 Security Testing

Verify:

```text
Employee A cannot see Employee B's private data.

Employee cannot approve their own leave.

Employee cannot modify salary.

Employee cannot access HR-only screens.

HR can access employee records.

HR can approve/reject leave.

```

---

# 10. GitHub Workflow

## Branches

The repository should use:

```text
main
develop
```

and feature branches:

```text
feature/core-security
feature/attendance-leave
feature/employee-payroll
feature/dashboard-ui
```

---

# 11. Branch Rules

### `main`

`main` must always contain a stable/demo-ready version.

Nobody should directly push to `main`.

---

### `develop`

`develop` is the integration branch.

Feature branches merge into:

```text
feature/*
      ↓
develop
```

After testing:

```text
develop
   ↓
main
```

---

# 12. Daily Git Workflow

Before starting work:

```bash
git checkout develop
git pull origin develop

git checkout feature/<your-branch>
git merge develop
```

Then work normally.

After completing a logical task:

```bash
git status
git add .
git commit -m "Add attendance check-in"
git push origin feature/attendance-leave
```

Create a Pull Request:

```text
feature/attendance-leave
          ↓
       develop
```

Another team member reviews it.

After approval:

```text
Merge Pull Request
```

---

# 13. Commit Message Convention

Use clear commit messages.

Good:

```text
Add employee profile fields
Add attendance check-in
Add leave approval workflow
Add employee dashboard
Configure HR access rules
Fix leave status update
Fix employee attendance visibility
```

Avoid:

```text
update
changes
final
final2
test
abc
done
```

---

# 14. Pull Request Rules

Every PR should contain:

### Title

```text
Add attendance check-in/check-out
```

### Description

```text
## What was added
- Added employee check-in
- Added employee check-out
- Added attendance record

## Testing
- Tested employee check-in
- Tested employee check-out
- Tested attendance visibility

## Related module
Attendance
```

Before merging, verify:

```text
[ ] Code works
[ ] No unrelated files changed
[ ] No secrets committed
[ ] Odoo module installs
[ ] Existing functionality still works
[ ] Another member reviewed it
```

---

# 15. Merge Conflict Rules

If a conflict occurs:

DO NOT blindly choose:

```text
Accept Current
```

or:

```text
Accept Incoming
```

First understand what both changes do.

If the conflict involves another member's functionality:

```text
Stop
 ↓
Contact the owner
 ↓
Understand both changes
 ↓
Resolve together
 ↓
Test
```

---

# 16. Shared Coding Rules

All agents must follow these rules.

### Rule 1 — Inspect before modifying

Before changing a file:

```text
Read the file.
Understand the existing code.
Search for references.
Then modify.
```

---

### Rule 2 — Reuse Odoo

Before creating a new model:

```text
Check whether Odoo already provides the functionality.
```

Extend existing functionality where appropriate.

---

### Rule 3 — Keep modules separated

Attendance code should not contain payroll logic.

Payroll code should not contain leave logic.

Dashboard code should not contain business logic.

---

### Rule 4 — Avoid unnecessary dependencies

Do not install additional packages unless necessary.

---

### Rule 5 — No hardcoded secrets

Never commit:

```text
API keys
Passwords
Tokens
.env
Private credentials
```

---

### Rule 6 — Don't over-engineer

The goal is a functional hackathon MVP.

Prioritize:

```text
Working functionality
Security
Integration
Good UI
Reliable demo
```

over unnecessary complexity.

---

# 17. Integration Order

The team should integrate functionality in this order:

```text
1. Core Odoo module
        ↓
2. Employee + Users
        ↓
3. Security / Roles
        ↓
4. Employee Profile
        ↓
5. Attendance
        ↓
6. Leave
        ↓
7. Leave Approval
        ↓
8. Payroll / Salary
        ↓
9. Dashboards
        ↓
10. Testing
        ↓
11. UI Polish
        ↓
12. Final Demo
```

---

# 18. MVP Priority

If time becomes limited, implement these first:

## Priority 1 — MUST HAVE

```text
Authentication
Role-based access
Employee profile
Attendance
Check-in/check-out
Leave application
Leave approval
Salary visibility
Admin dashboard
Employee dashboard
```

These directly correspond to the core functional requirements in the specification.

---

## Priority 2 — SHOULD HAVE

```text
Daily/weekly attendance views
Better filters
Better employee management
Comments on leave requests
Improved dashboard cards
```

---

## Priority 3 — IF TIME ALLOWS

The specification mentions:

```text
Email notifications
Analytics
Reports
Salary slips
Attendance reports
```

These are listed as future enhancements, so they should not take priority over the core HRMS.

---

# 19. Final Hackathon Demo Flow

The final demo should tell one complete story rather than showing disconnected features.

```text
                  HR LOGIN
                     ↓
              Create Employee
                     ↓
              Employee Profile
                     ↓
              Set Salary
                     ↓
              Employee LOGIN
                     ↓
            Employee Dashboard
                     ↓
              Check Attendance
                     ↓
                Check In
                     ↓
              Apply for Leave
                     ↓
                  PENDING
                     ↓
              HR Dashboard
                     ↓
             Review Leave
                     ↓
                 APPROVE
                     ↓
              Employee Dashboard
                     ↓
             Leave = APPROVED
                     ↓
              View Salary
                     ↓
             HR Payroll View
```

This demonstrates the relationship between the major Dayflow modules.

---

# 20. Definition of Done

A feature is NOT complete merely because the code was written.

A feature is complete when:

```text
[ ] Code implemented
[ ] Odoo module loads
[ ] No Python/XML errors
[ ] Required permissions work
[ ] Employee behavior tested
[ ] HR behavior tested
[ ] Existing features still work
[ ] Git commit created
[ ] Branch pushed
[ ] Pull Request created
[ ] PR reviewed
[ ] Merged into develop
```

---

# 21. Coding Agent Instructions

When a team member asks an AI coding agent to implement something, the agent should follow this format mentally:

```text
1. Identify the assigned module.
2. Inspect the repository.
3. Read existing models/views/security.
4. Determine whether Odoo already provides the required functionality.
5. Reuse existing models where appropriate.
6. Implement only the requested functionality.
7. Preserve existing functionality.
8. Test the implementation.
9. Report modified files.
10. Report tests performed.
11. Do not modify unrelated modules.
```

Example:

```text
I am working on Member 2's Attendance & Leave module.

Before making changes:
- Inspect the existing Odoo module.
- Check employee/user relationships.
- Check existing security rules.
- Check whether attendance functionality already exists.
- Do not modify payroll or dashboard functionality.
- Implement the requested attendance feature.
- Test employee and HR access.
- Summarize changed files after implementation.
```

---

# 22. Communication Between Members

Use GitHub Issues or team communication for cross-module requirements.

Example:

```text
Member 2:
"I need employee_id and HR access rules for attendance."

Member 1:
"Employee relationship is available through <model/field>.
I will add the required security rule."

Member 2:
"Okay, I'll implement attendance using that relationship."
```

Do not silently change another member's architecture.

---

# 23. Team Ownership Summary

```text
┌─────────────────────────────────────────────────────────┐
│                    DAYFLOW HRMS                         │
├──────────────────────┬──────────────────────────────────┤
│ MEMBER 1             │ Core Odoo / Security             │
│                      │ Models / Roles / Integration      │
├──────────────────────┼──────────────────────────────────┤
│ MEMBER 2             │ Attendance / Leave               │
│                      │ Check-in / Check-out / Approval  │
├──────────────────────┼──────────────────────────────────┤
│ MEMBER 3             │ Employee / Payroll               │
│                      │ Profile / Salary / Payroll       │
├──────────────────────┼──────────────────────────────────┤
│ MEMBER 4             │ UI / Dashboard / QA              │
│                      │ Views / Menus / Testing / Demo   │
└──────────────────────┴──────────────────────────────────┘
```

---

# 24. Golden Rule

> **Build independently, integrate frequently, and never break another member's work.**

The goal is not for four people to build four separate applications.

The goal is:

```text
4 Developers
     ↓
1 Odoo Module
     ↓
1 Integrated HRMS
     ↓
1 Reliable Demo
     ↓
Dayflow
```

**Dayflow — Every workday, perfectly aligned.**
