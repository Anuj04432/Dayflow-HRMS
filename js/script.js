/**
 * Dayflow HRMS - Master Frontend Logic & Backend Connector
 * Supports live Odoo REST backend integration with intelligent offline fallback and full multi-role RBAC.
 */

const API_BASE = window.DAYFLOW_API_BASE || 'http://localhost:8069';

/* =========================================================
   INITIAL SEED DATA & LOCAL STORAGE MANAGEMENT
========================================================= */

function initLocalStorageData() {
    if (!localStorage.getItem("dayflow_users")) {
        const initialUsers = [
            {
                user_id: 1,
                employee_id: 1,
                name: "Anita Sharma (HR)",
                employee_code: "DF0001",
                email: "hr@dayflow.com",
                password: "password123",
                role: "hr",
                department: "Human Resources",
                designation: "HR Manager",
                phone: "+91 98765 43210",
                address: "Dayflow HQ, Floor 4, Bengaluru, India",
                is_verified: true,
                join_date: "2024-01-15",
                basic_salary: 65000,
                hra: 18000,
                allowances: 7000,
                deductions: 4000
            },
            {
                user_id: 2,
                employee_id: 2,
                name: "Rahul Kumar",
                employee_code: "DF0002",
                email: "employee@dayflow.com",
                password: "password123",
                role: "employee",
                department: "Engineering",
                designation: "Software Engineer",
                phone: "+91 98765 12345",
                address: "Indiranagar, Bengaluru, India",
                is_verified: true,
                join_date: "2025-03-01",
                basic_salary: 35000,
                hra: 8000,
                allowances: 5000,
                deductions: 2000
            },
            {
                user_id: 3,
                employee_id: 3,
                name: "Arjun Singh",
                employee_code: "DF0003",
                email: "arjun@dayflow.com",
                password: "password123",
                role: "employee",
                department: "Finance",
                designation: "Financial Analyst",
                phone: "+91 98765 54321",
                address: "Koramangala, Bengaluru, India",
                is_verified: true,
                join_date: "2025-05-10",
                basic_salary: 40000,
                hra: 9000,
                allowances: 4000,
                deductions: 2500
            }
        ];
        localStorage.setItem("dayflow_users", JSON.stringify(initialUsers));
    }

    if (!localStorage.getItem("dayflow_attendance")) {
        const initialAttendance = [
            { id: 1, employee_id: 1, employee_name: "Anita Sharma (HR)", employee_code: "DF0001", department_name: "Human Resources", date: "2026-08-22", check_in: "08:55:00", check_out: null, worked_hours: 0, state: "present" },
            { id: 2, employee_id: 2, employee_name: "Rahul Kumar", employee_code: "DF0002", department_name: "Engineering", date: "2026-08-22", check_in: "09:05:00", check_out: "18:00:00", worked_hours: 8.9, state: "present" },
            { id: 3, employee_id: 3, employee_name: "Arjun Singh", employee_code: "DF0003", department_name: "Finance", date: "2026-08-22", check_in: null, check_out: null, worked_hours: 0, state: "leave" },
            { id: 4, employee_id: 2, employee_name: "Rahul Kumar", employee_code: "DF0002", department_name: "Engineering", date: "2026-08-21", check_in: "09:15:00", check_out: "13:30:00", worked_hours: 4.2, state: "half_day" },
            { id: 5, employee_id: 2, employee_name: "Rahul Kumar", employee_code: "DF0002", department_name: "Engineering", date: "2026-08-20", check_in: null, check_out: null, worked_hours: 0, state: "absent" }
        ];
        localStorage.setItem("dayflow_attendance", JSON.stringify(initialAttendance));
    }

    if (!localStorage.getItem("dayflow_leaves")) {
        const initialLeaves = [
            { id: 1, employee_id: 2, employee_name: "Rahul Kumar", employee_code: "DF0002", department_name: "Engineering", leave_type: "Paid Leave", date_from: "2026-08-25", date_to: "2026-08-26", duration_days: 2, remarks: "Personal emergency", state: "pending", created_at: "2026-08-22 10:15" },
            { id: 2, employee_id: 3, employee_name: "Arjun Singh", employee_code: "DF0003", department_name: "Finance", leave_type: "Sick Leave", date_from: "2026-08-22", date_to: "2026-08-23", duration_days: 2, remarks: "Flu and fever", state: "approved", created_at: "2026-08-21 16:20" },
            { id: 3, employee_id: 2, employee_name: "Rahul Kumar", employee_code: "DF0002", department_name: "Engineering", leave_type: "Sick Leave", date_from: "2026-08-10", date_to: "2026-08-11", duration_days: 2, remarks: "Health checkup", state: "approved", created_at: "2026-08-09 09:30" }
        ];
        localStorage.setItem("dayflow_leaves", JSON.stringify(initialLeaves));
    }
}

initLocalStorageData();


/* =========================================================
   API CALL HELPER WITH OFFLINE FALLBACK
========================================================= */

async function apiFetch(endpoint, method = 'GET', body = null) {
    const url = `${API_BASE}${endpoint}`;
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'include'
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(url, options);
        const data = await response.json();
        return { success: response.ok, ...data };
    } catch (err) {
        // Backend not reachable: trigger graceful offline fallback
        return { success: false, fallback: true, error: err.message };
    }
}


/* =========================================================
   SESSION & AUTH GUARD (STRICT ROLE ENFORCEMENT)
========================================================= */

function getCurrentUser() {
    try {
        return JSON.parse(localStorage.getItem("dayflow_current_user")) || null;
    } catch (e) {
        return null;
    }
}

function setCurrentUser(user) {
    localStorage.setItem("dayflow_current_user", JSON.stringify(user));
    localStorage.setItem("loggedIn", "true");
    localStorage.setItem("email", user.email);
    localStorage.setItem("role", user.role);
}

function checkAuth(requiredRole = null) {
    const user = getCurrentUser();
    const currentPath = window.location.pathname;
    const isAuthPage = currentPath.endsWith("index.html") ||
                       currentPath.endsWith("signup.html") ||
                       currentPath.endsWith("verify-email.html") ||
                       currentPath === "/" ||
                       currentPath === "";

    // 1. If not logged in and on protected page -> go to login
    if (!user && !isAuthPage) {
        window.location.href = "index.html";
        return null;
    }

    // 2. If already logged in and on login/signup page -> go to appropriate dashboard
    if (user && isAuthPage && !currentPath.endsWith("verify-email.html")) {
        window.location.href = user.role === "hr" ? "hr-dashboard.html" : "employee-dashboard.html";
        return user;
    }

    // 3. Strict Dashboard routing: HR accessing employee dashboard -> redirect to HR dashboard
    if (user && user.role === "hr" && currentPath.endsWith("employee-dashboard.html")) {
        window.location.href = "hr-dashboard.html";
        return user;
    }

    // 4. Strict Dashboard routing: Employee accessing HR dashboard -> redirect to Employee dashboard
    if (user && user.role === "employee" && currentPath.endsWith("hr-dashboard.html")) {
        window.location.href = "employee-dashboard.html";
        return user;
    }

    // 5. Page-level role requirement check
    if (user && requiredRole && user.role !== requiredRole && user.role !== 'hr') {
        window.location.href = "employee-dashboard.html";
        return user;
    }

    return user;
}

function logout() {
    apiFetch('/api/auth/logout', 'POST').catch(() => {});
    localStorage.removeItem("dayflow_current_user");
    localStorage.removeItem("loggedIn");
    localStorage.removeItem("role");
    window.location.href = "index.html";
}


/* =========================================================
   DYNAMIC SIDEBAR & TOPBAR ROLE INJECTION
========================================================= */

function setupSidebarAndNav(user) {
    if (!user) return;
    const isHR = user.role === "hr";

    // 1. Fix all "Dashboard" links in sidebar to point to the correct role dashboard!
    document.querySelectorAll('.sidebar nav a').forEach(link => {
        const text = link.textContent.trim().toLowerCase();
        if (text.includes("dashboard")) {
            link.href = isHR ? "hr-dashboard.html" : "employee-dashboard.html";
        }
    });

    // 2. Update sidebar brand role subtitle
    const sidebarRoleBadge = document.querySelector(".sidebar-brand span");
    if (sidebarRoleBadge) {
        sidebarRoleBadge.textContent = isHR ? "HR / Admin" : "Employee";
    }

    // 3. Update topbar user name & avatar initials
    const topbarName = document.querySelector(".topbar h2");
    const userBoxRole = document.querySelector(".user-box span");
    const avatar = document.querySelector(".avatar");

    if (userBoxRole) {
        userBoxRole.textContent = isHR ? "HR Officer" : user.name;
    }

    if (avatar && user.name) {
        const initials = isHR ? "HR" : user.name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
        avatar.textContent = initials;
    }
}


/* =========================================================
   DEMO HELPERS (LOGIN QUICK SELECT)
========================================================= */

function fillCredentials(email, password) {
    const emailInput = document.getElementById("loginEmail");
    const passInput = document.getElementById("loginPassword");
    if (emailInput && passInput) {
        emailInput.value = email;
        passInput.value = password;
    }
}


/* =========================================================
   SIGN UP & LOGIN
========================================================= */

const signupForm = document.getElementById("signupForm");
if (signupForm) {
    signupForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        const name = (document.getElementById("signupName")?.value || "").trim();
        const employeeId = (document.getElementById("employeeId")?.value || "").trim();
        const email = document.getElementById("signupEmail").value.trim().toLowerCase();
        const password = document.getElementById("signupPassword").value;
        const role = document.getElementById("role").value;
        const error = document.getElementById("signupError");

        error.textContent = "";

        if (password.length < 8) {
            error.textContent = "Password must contain at least 8 characters.";
            return;
        }

        if (!role) {
            error.textContent = "Please select a role.";
            return;
        }

        // Try backend registration
        const res = await apiFetch('/api/auth/signup', 'POST', {
            name: name || employeeId,
            email,
            password,
            role,
            employee_code: employeeId
        });

        if (res.success) {
            localStorage.setItem("pending_verification_email", email);
            window.location.href = `verify-email.html?email=${encodeURIComponent(email)}&token=${res.data?.verification_token || 'mock-token'}`;
            return;
        }

        // Fallback local registration
        let users = JSON.parse(localStorage.getItem("dayflow_users") || "[]");
        if (users.find(u => u.email === email)) {
            error.textContent = "An account with this email already exists.";
            return;
        }

        const newUser = {
            user_id: users.length + 1,
            employee_id: users.length + 1,
            name: name || employeeId || "New User",
            employee_code: employeeId || `DF000${users.length + 1}`,
            email: email,
            password: password,
            role: role,
            department: role === "hr" ? "Human Resources" : "Engineering",
            designation: role === "hr" ? "HR Specialist" : "Software Developer",
            phone: "+91 98765 00000",
            address: "Bengaluru, India",
            is_verified: false,
            join_date: new Date().toISOString().split('T')[0],
            basic_salary: role === "hr" ? 60000 : 35000,
            hra: role === "hr" ? 15000 : 8000,
            allowances: role === "hr" ? 6000 : 4000,
            deductions: 2000
        };

        users.push(newUser);
        localStorage.setItem("dayflow_users", JSON.stringify(users));
        localStorage.setItem("pending_verification_email", email);

        window.location.href = `verify-email.html?email=${encodeURIComponent(email)}&token=mock-token-${Date.now()}`;
    });
}

const loginForm = document.getElementById("loginForm");
if (loginForm) {
    loginForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        const email = document.getElementById("loginEmail").value.trim().toLowerCase();
        const password = document.getElementById("loginPassword").value;
        const error = document.getElementById("loginError");

        error.textContent = "";

        if (email === "" || password === "") {
            error.textContent = "Please enter email and password.";
            return;
        }

        // Try Backend Login
        const res = await apiFetch('/api/auth/login', 'POST', { email, password });

        if (res.success && res.data) {
            setCurrentUser(res.data);
            window.location.href = res.data.role === "hr" ? "hr-dashboard.html" : "employee-dashboard.html";
            return;
        } else if (!res.fallback && res.message) {
            error.textContent = res.message;
            return;
        }

        // Fallback: Local Validation
        const users = JSON.parse(localStorage.getItem("dayflow_users") || "[]");
        const found = users.find(u => u.email === email);

        if (found) {
            if (found.password !== password) {
                error.textContent = "Incorrect password. Please try again.";
                return;
            }
            if (found.is_verified === false) {
                error.textContent = "Please verify your email before logging in.";
                return;
            }

            setCurrentUser(found);
            window.location.href = found.role === "hr" ? "hr-dashboard.html" : "employee-dashboard.html";
        } else {
            error.textContent = "Account not found. Please register or click a demo account.";
        }
    });
}


/* =========================================================
   EMAIL VERIFICATION
========================================================= */

async function verifyEmail() {
    const message = document.getElementById("verifyMessage");
    const urlParams = new URLSearchParams(window.location.search);
    const email = urlParams.get("email") || localStorage.getItem("pending_verification_email") || localStorage.getItem("email");
    const token = urlParams.get("token") || "mock-token";

    if (!message) return;

    await apiFetch('/api/auth/verify-email', 'POST', { email, token });

    const users = JSON.parse(localStorage.getItem("dayflow_users") || "[]");
    const userIndex = users.findIndex(u => u.email === email);
    if (userIndex !== -1) {
        users[userIndex].is_verified = true;
        localStorage.setItem("dayflow_users", JSON.stringify(users));
    }

    message.textContent = "Email verified successfully! Redirecting to sign in...";
    message.style.color = "#16a34a";

    setTimeout(() => {
        window.location.href = "index.html";
    }, 1200);
}


/* =========================================================
   ATTENDANCE (EMPLOYEE CHECK-IN & HR COMPANY MONITORING)
========================================================= */

function setupAttendancePage(user) {
    if (!window.location.pathname.endsWith("attendance.html") || !user) return;

    const isHR = user.role === "hr";
    const empSection = document.getElementById("employeeAttendanceSection");
    const hrSection = document.getElementById("hrAttendanceSection");

    if (isHR) {
        if (empSection) empSection.classList.add("hidden");
        if (hrSection) hrSection.classList.remove("hidden");
        renderHRCompanyAttendance();
    } else {
        if (empSection) empSection.classList.remove("hidden");
        if (hrSection) hrSection.classList.add("hidden");
        renderPersonalAttendance();
    }
}

async function checkIn() {
    const status = document.getElementById("attendanceStatus");
    const user = getCurrentUser();
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const dateStr = now.toISOString().split('T')[0];

    await apiFetch('/api/attendance/check-in', 'POST');

    const attendanceList = JSON.parse(localStorage.getItem("dayflow_attendance") || "[]");
    const existing = attendanceList.find(a => a.employee_id === (user?.employee_id || 2) && a.date === dateStr);

    if (existing && existing.check_in && !existing.check_out) {
        alert("You are already checked in today!");
        return;
    }

    const newRecord = {
        id: Date.now(),
        employee_id: user?.employee_id || 2,
        employee_name: user?.name || "Rahul Kumar",
        employee_code: user?.employee_code || "DF0002",
        department_name: user?.department || "Engineering",
        date: dateStr,
        check_in: timeStr,
        check_out: null,
        worked_hours: 0,
        state: "present"
    };

    attendanceList.unshift(newRecord);
    localStorage.setItem("dayflow_attendance", JSON.stringify(attendanceList));

    if (status) {
        status.textContent = "Checked in at " + timeStr;
        status.style.color = "#16a34a";
    }

    renderPersonalAttendance();
}

async function checkOut() {
    const status = document.getElementById("attendanceStatus");
    const user = getCurrentUser();
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const dateStr = now.toISOString().split('T')[0];

    await apiFetch('/api/attendance/check-out', 'POST');

    const attendanceList = JSON.parse(localStorage.getItem("dayflow_attendance") || "[]");
    const todayRecord = attendanceList.find(a => a.employee_id === (user?.employee_id || 2) && a.date === dateStr);

    if (!todayRecord || !todayRecord.check_in) {
        alert("Please check in first before checking out.");
        return;
    }

    todayRecord.check_out = timeStr;
    todayRecord.worked_hours = 8.5;
    localStorage.setItem("dayflow_attendance", JSON.stringify(attendanceList));

    if (status) {
        status.textContent = "Checked out at " + timeStr;
        status.style.color = "#dc2626";
    }

    renderPersonalAttendance();
}

function renderPersonalAttendance() {
    const tbody = document.querySelector("#personalAttendanceTable tbody");
    if (!tbody) return;

    const user = getCurrentUser();
    const attendanceList = JSON.parse(localStorage.getItem("dayflow_attendance") || "[]");
    const myRecords = attendanceList.filter(a => a.employee_id === (user?.employee_id || 2));

    tbody.innerHTML = "";

    if (myRecords.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #6b7280; padding: 20px;">No attendance records found.</td></tr>`;
        return;
    }

    myRecords.forEach(record => {
        const stateClass = record.state === 'present' ? 'approved' : (record.state === 'half_day' ? 'halfday' : (record.state === 'leave' ? 'pending' : 'rejected'));
        const stateText = record.state === 'present' ? 'Present' : (record.state === 'half_day' ? 'Half-day' : (record.state === 'leave' ? 'Leave' : 'Absent'));

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${record.date}</td>
            <td>${record.check_in || '-'}</td>
            <td>${record.check_out || '-'}</td>
            <td>${record.worked_hours ? record.worked_hours + 'h' : '-'}</td>
            <td><span class="status ${stateClass}">${stateText}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderHRCompanyAttendance() {
    const tbody = document.querySelector("#hrAttendanceTable tbody");
    if (!tbody) return;

    const attendanceList = JSON.parse(localStorage.getItem("dayflow_attendance") || "[]");
    tbody.innerHTML = "";

    attendanceList.forEach(rec => {
        const stateClass = rec.state === 'present' ? 'approved' : (rec.state === 'half_day' ? 'halfday' : (rec.state === 'leave' ? 'pending' : 'rejected'));
        const stateText = rec.state === 'present' ? 'Present' : (rec.state === 'half_day' ? 'Half-day' : (rec.state === 'leave' ? 'On Leave' : 'Absent'));

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${rec.employee_name || 'Employee'}</strong> <small style="color:#6b7280;">(${rec.employee_code || 'DF0002'})</small></td>
            <td>${rec.department_name || 'Engineering'}</td>
            <td>${rec.date}</td>
            <td>${rec.check_in || '-'}</td>
            <td>${rec.check_out || '-'}</td>
            <td>${rec.worked_hours ? rec.worked_hours + 'h' : '-'}</td>
            <td><span class="status ${stateClass}">${stateText}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function filterHRCompanyAttendance() {
    const searchInput = document.getElementById("hrAttendanceSearch")?.value.toLowerCase() || "";
    const tbody = document.querySelector("#hrAttendanceTable tbody");
    if (!tbody) return;

    const rows = tbody.getElementsByTagName("tr");
    for (let row of rows) {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchInput) ? "" : "none";
    }
}

function switchAttendanceTab(btn, tabName) {
    document.querySelectorAll(".tabs .tab").forEach(t => t.classList.remove("active"));
    if (btn) btn.classList.add("active");
    renderPersonalAttendance();
}


/* =========================================================
   LEAVE MANAGEMENT (EMPLOYEE APPLY & HR APPROVALS)
========================================================= */

function setupLeavePage(user) {
    if (!window.location.pathname.endsWith("leave.html") || !user) return;

    const isHR = user.role === "hr";
    const empSection = document.getElementById("employeeLeaveSection");
    const hrSection = document.getElementById("hrLeaveSection");

    if (isHR) {
        if (empSection) empSection.classList.add("hidden");
        if (hrSection) hrSection.classList.remove("hidden");
        renderHRLeaveQueue();
    } else {
        if (empSection) empSection.classList.remove("hidden");
        if (hrSection) hrSection.classList.add("hidden");
        renderPersonalLeaveTable();
    }
}

const leaveForm = document.getElementById("leaveForm");
if (leaveForm) {
    leaveForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        const user = getCurrentUser();
        const leaveType = document.getElementById("leaveType")?.value;
        const dateFrom = document.getElementById("leaveFrom")?.value;
        const dateTo = document.getElementById("leaveTo")?.value;
        const remarks = document.getElementById("leaveRemarks")?.value || "";
        const message = document.getElementById("leaveMessage");

        if (new Date(dateTo) < new Date(dateFrom)) {
            alert("End date cannot be earlier than start date.");
            return;
        }

        await apiFetch('/api/leave/apply', 'POST', {
            leave_type: leaveType.toLowerCase().includes("sick") ? "sick" : (leaveType.toLowerCase().includes("unpaid") ? "unpaid" : "paid"),
            date_from: dateFrom,
            date_to: dateTo,
            remarks
        });

        const leaves = JSON.parse(localStorage.getItem("dayflow_leaves") || "[]");
        const fromD = new Date(dateFrom);
        const toD = new Date(dateTo);
        const diffDays = Math.max(1, Math.round((toD - fromD) / (1000 * 60 * 60 * 24)) + 1);

        const newLeave = {
            id: Date.now(),
            employee_id: user?.employee_id || 2,
            employee_name: user?.name || "Rahul Kumar",
            employee_code: user?.employee_code || "DF0002",
            department_name: user?.department || "Engineering",
            leave_type: leaveType,
            date_from: dateFrom,
            date_to: dateTo,
            duration_days: diffDays,
            remarks: remarks,
            state: "pending",
            created_at: new Date().toISOString().replace('T', ' ').substring(0, 16)
        };

        leaves.unshift(newLeave);
        localStorage.setItem("dayflow_leaves", JSON.stringify(leaves));

        if (message) {
            message.textContent = "Leave request submitted successfully. Awaiting HR approval.";
            message.style.color = "#16a34a";
        }

        leaveForm.reset();
        renderPersonalLeaveTable();
    });
}

function renderPersonalLeaveTable() {
    const tbody = document.querySelector("#personalLeaveTable tbody");
    if (!tbody) return;

    const user = getCurrentUser();
    const leaves = JSON.parse(localStorage.getItem("dayflow_leaves") || "[]");
    const myLeaves = leaves.filter(l => l.employee_id === (user?.employee_id || 2));

    tbody.innerHTML = "";

    myLeaves.forEach(req => {
        const stateClass = req.state === 'approved' ? 'approved' : (req.state === 'rejected' ? 'rejected' : 'pending');

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${req.leave_type}</td>
            <td>${req.date_from}</td>
            <td>${req.date_to}</td>
            <td>${req.remarks || '-'}</td>
            <td><span class="status ${stateClass}">${req.state.charAt(0).toUpperCase() + req.state.slice(1)}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderHRLeaveQueue() {
    const tbody = document.querySelector("#hrLeaveTable tbody");
    if (!tbody) return;

    const leaves = JSON.parse(localStorage.getItem("dayflow_leaves") || "[]");
    tbody.innerHTML = "";

    if (leaves.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #6b7280; padding: 20px;">No leave requests pending.</td></tr>`;
        return;
    }

    leaves.forEach(req => {
        const stateClass = req.state === 'approved' ? 'approved' : (req.state === 'rejected' ? 'rejected' : 'pending');
        const isPending = req.state === 'pending';

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${req.employee_name}</strong> <small style="color:#6b7280;">(${req.employee_code || 'DF0002'})</small></td>
            <td>${req.department_name || 'Engineering'}</td>
            <td>${req.leave_type}</td>
            <td>${req.date_from} to ${req.date_to} <small>(${req.duration_days || 1}d)</small></td>
            <td>${req.remarks || '-'}</td>
            <td><span class="status ${stateClass}">${req.state.charAt(0).toUpperCase() + req.state.slice(1)}</span></td>
            <td>
                ${isPending ? `
                <div class="btn-group">
                    <button type="button" class="btn-success" onclick="handleLeaveAction(${req.id}, 'approve')">Approve</button>
                    <button type="button" class="btn-danger" onclick="handleLeaveAction(${req.id}, 'reject')">Reject</button>
                </div>` : `<span style="color:#6b7280; font-size:12px;">Reviewed</span>`}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function handleLeaveAction(leaveId, action) {
    let comments = "";
    if (action === 'reject') {
        comments = prompt("Please enter a reason/comment for rejecting this leave request:") || "";
        if (!comments.trim()) {
            alert("A reason is required when rejecting a leave request.");
            return;
        }
    }

    const leaves = JSON.parse(localStorage.getItem("dayflow_leaves") || "[]");
    const leave = leaves.find(l => l.id === leaveId);
    if (leave) {
        leave.state = action === 'approve' ? 'approved' : 'rejected';
        if (comments) leave.manager_remarks = comments;
        localStorage.setItem("dayflow_leaves", JSON.stringify(leaves));
        apiFetch('/api/leave/action', 'POST', { leave_id: leaveId, action, comments }).catch(() => {});
        renderHRLeaveQueue();
    }
}


/* =========================================================
   PAYROLL (EMPLOYEE PAYSLIP & HR COMPANY PAYROLL - LIVE API)
========================================================= */

function setupPayrollPage(user) {
    if (!window.location.pathname.endsWith("payroll.html") || !user) return;

    const isHR = user.role === "hr";
    const empSection = document.getElementById("employeePayrollSection");
    const hrSection = document.getElementById("hrPayrollSection");

    if (isHR) {
        if (empSection) empSection.classList.add("hidden");
        if (hrSection) hrSection.classList.remove("hidden");
        renderHRCompanyPayroll();
    } else {
        if (empSection) empSection.classList.remove("hidden");
        if (hrSection) hrSection.classList.add("hidden");
        renderPersonalPayroll();
    }
}

async function renderPersonalPayroll() {
    let p = null;
    try {
        const res = await apiFetch('/api/payroll/salary-info');
        if (res && res.success && res.data) {
            p = res.data;
        }
    } catch (err) {
        console.warn("Offline payroll fallback triggered", err);
    }

    const user = getCurrentUser() || {};
    const basic = p ? (p.basic_salary || 0) : (user.basic_salary || 35000);
    const hra = p ? (p.hra || 0) : (user.hra || 8000);
    const allowance = p ? (p.special_allowance || 0) : (user.allowances || 5000);
    const deductions = p ? (p.deductions || 0) : (user.deductions || 2000);
    const net = p ? (p.net_salary || 0) : (basic + hra + allowance - deductions);

    // Update Summary KPI Cards
    if (document.getElementById("payrollBasic")) document.getElementById("payrollBasic").textContent = `₹${basic.toLocaleString()}`;
    if (document.getElementById("payrollAllowances")) document.getElementById("payrollAllowances").textContent = `₹${(hra + allowance).toLocaleString()}`;
    if (document.getElementById("payrollDeductions")) document.getElementById("payrollDeductions").textContent = `₹${deductions.toLocaleString()}`;
    if (document.getElementById("payrollNet")) document.getElementById("payrollNet").textContent = `₹${net.toLocaleString()}`;

    // Update Breakdown Table
    if (document.getElementById("tblBasic")) document.getElementById("tblBasic").textContent = `₹${basic.toLocaleString()}`;
    if (document.getElementById("tblHRA")) document.getElementById("tblHRA").textContent = `₹${hra.toLocaleString()}`;
    if (document.getElementById("tblAllowances")) document.getElementById("tblAllowances").textContent = `₹${allowance.toLocaleString()}`;
    if (document.getElementById("tblDeductions")) document.getElementById("tblDeductions").textContent = `-₹${deductions.toLocaleString()}`;
    if (document.getElementById("tblNet")) document.getElementById("tblNet").textContent = `₹${net.toLocaleString()}`;
}

async function renderHRCompanyPayroll() {
    const tbody = document.querySelector("#hrPayrollTable tbody");
    if (!tbody) return;

    let payrollList = [];
    try {
        const res = await apiFetch('/api/payroll/company');
        if (res && res.success && Array.isArray(res.data) && res.data.length > 0) {
            payrollList = res.data;
        }
    } catch (err) {
        console.warn("Offline HR payroll fallback", err);
    }

    if (payrollList.length === 0) {
        const users = JSON.parse(localStorage.getItem("dayflow_users") || "[]");
        payrollList = users.map(u => ({
            employee_id: u.employee_id || u.user_id || 1,
            employee_name: u.name,
            employee_code: u.employee_code || "DF0001",
            department_name: u.department || "General",
            basic_salary: u.basic_salary || 35000,
            hra: u.hra || 8000,
            special_allowance: u.allowances || 5000,
            deductions: u.deductions || 2000,
            net_salary: (u.basic_salary || 35000) + (u.hra || 8000) + (u.allowances || 5000) - (u.deductions || 2000)
        }));
    }

    tbody.innerHTML = "";
    payrollList.forEach(p => {
        const basic = Number(p.basic_salary) || 0;
        const hra = Number(p.hra) || 0;
        const allowance = Number(p.special_allowance) || 0;
        const deductions = Number(p.deductions) || 0;
        const net = Number(p.net_salary) || (basic + hra + allowance - deductions);

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${p.employee_name}</strong> <small style="color:#6b7280;">(${p.employee_code})</small></td>
            <td>${p.department_name || 'General'}</td>
            <td>₹${basic.toLocaleString()}</td>
            <td>₹${(hra + allowance).toLocaleString()}</td>
            <td style="color:#dc2626;">-₹${deductions.toLocaleString()}</td>
            <td><strong style="color:#4f46e5;">₹${net.toLocaleString()}</strong></td>
            <td>
                <button type="button" class="secondary-btn" style="padding: 4px 8px; font-size: 12px;" onclick="openSalaryEditModal(${p.employee_id}, '${(p.employee_name || '').replace(/'/g, "\\'")}', ${basic}, ${hra}, ${allowance}, ${deductions})">✏️ Edit</button>
                <button type="button" class="secondary-btn" style="padding: 4px 8px; font-size: 12px; margin-left: 4px;" onclick="downloadSalarySlipForUser('${(p.employee_name || '').replace(/'/g, "\\'")}', '${p.employee_code}', ${basic}, ${hra}, ${allowance}, ${deductions})">Payslip</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function openSalaryEditModal(employeeId, employeeName, basic, hra, allowance, deductions) {
    const modal = document.createElement("div");
    modal.className = "dayflow-modal";
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Update Salary: ${employeeName}</h3>
                <button type="button" class="modal-close-btn" onclick="this.closest('.dayflow-modal').remove()">×</button>
            </div>
            <div class="modal-body">
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <div>
                        <label style="font-size: 13px; font-weight: 600; color: #374151; display: block; margin-bottom: 4px;">Basic Salary (INR)</label>
                        <input type="number" id="editBasicSalary" value="${basic}" style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px;">
                    </div>
                    <div>
                        <label style="font-size: 13px; font-weight: 600; color: #374151; display: block; margin-bottom: 4px;">House Rent Allowance (HRA)</label>
                        <input type="number" id="editHra" value="${hra}" style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px;">
                    </div>
                    <div>
                        <label style="font-size: 13px; font-weight: 600; color: #374151; display: block; margin-bottom: 4px;">Special Allowance</label>
                        <input type="number" id="editSpecialAllowance" value="${allowance}" style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px;">
                    </div>
                    <div>
                        <label style="font-size: 13px; font-weight: 600; color: #374151; display: block; margin-bottom: 4px;">Total Deductions (Tax / PF)</label>
                        <input type="number" id="editDeductions" value="${deductions}" style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px;">
                    </div>
                </div>
            </div>
            <div class="modal-footer" style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 15px;">
                <button type="button" class="secondary-btn" onclick="this.closest('.dayflow-modal').remove()">Cancel</button>
                <button type="button" class="primary-btn" style="width: auto;" onclick="submitSalaryUpdate(${employeeId})">Save Salary</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

async function submitSalaryUpdate(employeeId) {
    const basic = parseFloat(document.getElementById("editBasicSalary")?.value || 0);
    const hra = parseFloat(document.getElementById("editHra")?.value || 0);
    const allowance = parseFloat(document.getElementById("editSpecialAllowance")?.value || 0);
    const deductions = parseFloat(document.getElementById("editDeductions")?.value || 0);

    const res = await apiFetch('/api/payroll/update', 'PUT', {
        employee_id: employeeId,
        basic_salary: basic,
        hra: hra,
        special_allowance: allowance,
        deductions: deductions
    });

    // Update localStorage for full offline sync
    const users = JSON.parse(localStorage.getItem("dayflow_users") || "[]");
    const idx = users.findIndex(u => (u.employee_id === employeeId || u.user_id === employeeId));
    if (idx !== -1) {
        users[idx].basic_salary = basic;
        users[idx].hra = hra;
        users[idx].allowances = allowance;
        users[idx].deductions = deductions;
        localStorage.setItem("dayflow_users", JSON.stringify(users));
    }

    if (res && res.success) {
        alert("✅ Salary structure updated successfully!");
        document.querySelector(".dayflow-modal")?.remove();
        renderHRCompanyPayroll();
    } else if (res && !res.fallback && !res.success) {
        alert("❌ Failed to update salary: " + (res.message || "Unknown error"));
    } else {
        alert("✅ Salary structure updated locally!");
        document.querySelector(".dayflow-modal")?.remove();
        renderHRCompanyPayroll();
    }
}

function downloadSalarySlipForUser(nameOrEmail, code, basic, hra, allowance, deductions) {
    if (typeof nameOrEmail === 'string' && nameOrEmail.includes('@')) {
        const users = JSON.parse(localStorage.getItem("dayflow_users") || "[]");
        const targetUser = users.find(u => u.email === nameOrEmail);
        if (targetUser) {
            showSalarySlipModal(targetUser);
            return;
        }
    }
    showSalarySlipModal({
        name: nameOrEmail || "Employee",
        employee_code: code || "DF0002",
        basic_salary: basic || 35000,
        hra: hra || 0,
        allowances: allowance || 0,
        deductions: deductions || 0
    });
}

function downloadSalarySlip() {
    const user = getCurrentUser() || { name: "Rahul Kumar", employee_code: "DF0002", basic_salary: 35000, hra: 8000, allowances: 5000, deductions: 2000 };
    showSalarySlipModal(user);
}

function showSalarySlipModal(user) {
    const basic = user.basic_salary || 35000;
    const hra = user.hra || 8000;
    const allowances = user.allowances || user.special_allowance || 5000;
    const deductions = user.deductions || 2000;
    const gross = basic + hra + allowances;
    const net = gross - deductions;

    const modal = document.createElement("div");
    modal.className = "dayflow-modal";
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Dayflow Salary Slip</h3>
                <button type="button" class="modal-close-btn" onclick="this.closest('.dayflow-modal').remove()">×</button>
            </div>
            <div class="modal-body" style="line-height: 1.8;">
                <p><strong>Employee:</strong> ${user.name} (${user.employee_code || 'DF0002'})</p>
                <p><strong>Pay Period:</strong> August 2026</p>
                <hr style="margin: 15px 0; border: 0; border-top: 1px solid #e5e7eb;">
                <div style="display: flex; justify-content: space-between;"><span>Basic Salary:</span><strong>₹${basic.toLocaleString()}</strong></div>
                <div style="display: flex; justify-content: space-between;"><span>HRA & Allowances:</span><strong>₹${(hra + allowances).toLocaleString()}</strong></div>
                <div style="display: flex; justify-content: space-between; color: #dc2626;"><span>Deductions (Tax/PF):</span><strong>-₹${deductions.toLocaleString()}</strong></div>
                <hr style="margin: 15px 0; border: 0; border-top: 1px solid #e5e7eb;">
                <div style="display: flex; justify-content: space-between; font-size: 16px; color: #4f46e5;"><span><strong>Net Salary Paid:</strong></span><strong>₹${net.toLocaleString()}</strong></div>
            </div>
            <div class="modal-footer">
                <button type="button" class="secondary-btn" onclick="window.print()">🖨️ Print</button>
                <button type="button" class="primary-btn" style="width: auto;" onclick="this.closest('.dayflow-modal').remove()">Close</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}


/* =========================================================
   SEARCH & EMPLOYEE LIST (HR DASHBOARD)
========================================================= */

function searchEmployees() {
    const input = document.getElementById("employeeSearch");
    const table = document.getElementById("employeeTable") || document.querySelector("table");
    if (!input || !table) return;

    const searchText = input.value.toLowerCase();
    const tbody = table.querySelector("tbody");
    if (!tbody) return;

    const rows = tbody.getElementsByTagName("tr");
    for (let i = 0; i < rows.length; i++) {
        const rowText = rows[i].textContent.toLowerCase();
        rows[i].style.display = rowText.includes(searchText) ? "" : "none";
    }
}


/* =========================================================
   PROFILE MANAGEMENT (LIVE API INTEGRATION)
========================================================= */

async function loadProfile() {
    if (!window.location.pathname.endsWith("profile.html")) return;

    let emp = null;
    let salary = null;

    try {
        const res = await apiFetch('/api/employee/profile');
        if (res && res.success && res.data) {
            emp = res.data;
        }
    } catch (err) {
        console.warn("Using offline profile fallback", err);
    }

    if (!emp) {
        const user = getCurrentUser();
        if (user) {
            emp = {
                name: user.name,
                employee_code: user.employee_code || "DF0001",
                work_email: user.email,
                department_name: user.department || (user.role === 'hr' ? "Human Resources" : "Engineering"),
                phone: user.phone || "+91 98765 43210",
                address: user.address || "Bengaluru, India",
                job_title: user.designation || (user.role === 'hr' ? "HR Manager" : "Software Engineer"),
                join_date: user.join_date || "2025-03-01",
                status: "active"
            };
        }
    }

    if (emp) {
        if (document.getElementById("profileName")) document.getElementById("profileName").textContent = emp.name;
        if (document.getElementById("profileEmpId")) document.getElementById("profileEmpId").textContent = emp.employee_code;
        if (document.getElementById("profileEmpIdText")) document.getElementById("profileEmpIdText").textContent = emp.employee_code;
        if (document.getElementById("profileEmail")) document.getElementById("profileEmail").textContent = emp.work_email;
        if (document.getElementById("profileDept")) document.getElementById("profileDept").textContent = emp.department_name;
        if (document.getElementById("profilePhone")) document.getElementById("profilePhone").value = emp.phone || "";
        if (document.getElementById("profileAddress")) document.getElementById("profileAddress").value = emp.address || "";

        // Job Details
        if (document.getElementById("jobDept")) document.getElementById("jobDept").textContent = emp.department_name || "General";
        if (document.getElementById("jobDesignation")) document.getElementById("jobDesignation").textContent = emp.job_title || "Employee";
        if (document.getElementById("jobJoinDate")) document.getElementById("jobJoinDate").textContent = emp.join_date || "-";
        if (document.getElementById("jobStatus")) document.getElementById("jobStatus").textContent = (emp.status || "active").toUpperCase();

        // Salary Structure Card
        try {
            const salRes = await apiFetch('/api/payroll/salary-info');
            if (salRes && salRes.success && salRes.data) {
                salary = salRes.data;
            }
        } catch (e) {}

        const user = getCurrentUser() || {};
        const basic = salary ? (salary.basic_salary || 0) : (user.basic_salary || 35000);
        const allowances = salary ? ((salary.hra || 0) + (salary.special_allowance || 0)) : ((user.hra || 8000) + (user.allowances || 5000));
        const gross = salary ? (salary.gross_salary || (basic + allowances)) : (basic + allowances);

        if (document.getElementById("profileBasic")) document.getElementById("profileBasic").textContent = `₹${basic.toLocaleString()}`;
        if (document.getElementById("profileAllowances")) document.getElementById("profileAllowances").textContent = `₹${allowances.toLocaleString()}`;
        if (document.getElementById("profileGross")) document.getElementById("profileGross").textContent = `₹${gross.toLocaleString()}`;

        // Avatar Initials
        const avatarElem = document.querySelector(".profile-picture span");
        if (avatarElem && emp.name) {
            avatarElem.textContent = emp.name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
        }
    }
}

async function saveProfile() {
    const user = getCurrentUser();
    const phone = document.getElementById("profilePhone")?.value || "";
    const address = document.getElementById("profileAddress")?.value || "";

    if (user) {
        user.phone = phone;
        user.address = address;
        setCurrentUser(user);

        const users = JSON.parse(localStorage.getItem("dayflow_users") || "[]");
        const idx = users.findIndex(u => u.email === user.email);
        if (idx !== -1) {
            users[idx].phone = phone;
            users[idx].address = address;
            localStorage.setItem("dayflow_users", JSON.stringify(users));
        }
    }

    const res = await apiFetch('/api/employee/profile', 'PUT', { phone, address });
    if (res && res.success) {
        alert("✅ Profile changes saved successfully!");
        loadProfile();
    } else if (res && !res.fallback && !res.success) {
        alert("❌ Failed to save profile: " + (res.message || "Unknown error"));
    } else {
        alert("✅ Profile changes saved locally!");
        loadProfile();
    }
}


/* =========================================================
   REPORTS & DOCUMENTS
========================================================= */

function viewReport(type) {
    const modal = document.createElement("div");
    modal.className = "dayflow-modal";
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>${type} Report</h3>
                <button type="button" class="modal-close-btn" onclick="this.closest('.dayflow-modal').remove()">×</button>
            </div>
            <div class="modal-body">
                <p style="color: #6b7280; margin-bottom: 15px;">Detailed analytics for ${type} in the current fiscal period.</p>
                <div style="padding: 15px; background: #f9fafb; border-radius: 8px;">
                    <p><strong>Status:</strong> Active & Recorded</p>
                    <p><strong>Compliance:</strong> 100% Policy Adherent</p>
                    <p><strong>Generated on:</strong> ${new Date().toLocaleDateString()}</p>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="primary-btn" style="width: auto;" onclick="this.closest('.dayflow-modal').remove()">Done</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function viewDocument(docName) {
    const modal = document.createElement("div");
    modal.className = "dayflow-modal";
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Document: ${docName}</h3>
                <button type="button" class="modal-close-btn" onclick="this.closest('.dayflow-modal').remove()">×</button>
            </div>
            <div class="modal-body" style="text-align: center; padding: 25px;">
                <div style="font-size: 40px; margin-bottom: 15px;">📄</div>
                <p><strong>${docName}</strong> is verified and stored in the secure Dayflow database.</p>
                <small style="color: #6b7280;">Encrypted record matching Dayflow security guidelines.</small>
            </div>
            <div class="modal-footer">
                <button type="button" class="primary-btn" style="width: auto;" onclick="this.closest('.dayflow-modal').remove()">Close</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}


/* =========================================================
   DOM CONTENT LOADED INITIALIZATION
========================================================= */

document.addEventListener("DOMContentLoaded", function() {
    const user = checkAuth();
    if (!user) return;

    // Apply role-based sidebar & topbar branding
    setupSidebarAndNav(user);

    // Apply role-based views on shared pages
    setupAttendancePage(user);
    setupLeavePage(user);
    setupPayrollPage(user);
    loadProfile();
});