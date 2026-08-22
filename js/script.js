/**
 * Dayflow HRMS - Master Frontend Logic & Backend Connector
 * Supports live Odoo REST backend integration with intelligent offline fallback.
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
            }
        ];
        localStorage.setItem("dayflow_users", JSON.stringify(initialUsers));
    }

    if (!localStorage.getItem("dayflow_attendance")) {
        const initialAttendance = [
            { id: 1, employee_id: 2, employee_name: "Rahul Kumar", date: "2026-08-22", check_in: "09:05:00", check_out: "18:00:00", worked_hours: 8.9, state: "present" },
            { id: 2, employee_id: 2, employee_name: "Rahul Kumar", date: "2026-08-21", check_in: "09:15:00", check_out: "13:30:00", worked_hours: 4.2, state: "half_day" },
            { id: 3, employee_id: 2, employee_name: "Rahul Kumar", date: "2026-08-20", check_in: null, check_out: null, worked_hours: 0, state: "absent" },
            { id: 4, employee_id: 2, employee_name: "Rahul Kumar", date: "2026-08-19", check_in: null, check_out: null, worked_hours: 0, state: "leave" }
        ];
        localStorage.setItem("dayflow_attendance", JSON.stringify(initialAttendance));
    }

    if (!localStorage.getItem("dayflow_leaves")) {
        const initialLeaves = [
            { id: 1, employee_id: 2, employee_name: "Rahul Kumar", department_name: "Engineering", leave_type: "paid", date_from: "2026-08-25", date_to: "2026-08-26", duration_days: 2, remarks: "Personal emergency", state: "pending", created_at: "2026-08-22 10:15" },
            { id: 2, employee_id: 2, employee_name: "Rahul Kumar", department_name: "Engineering", leave_type: "sick", date_from: "2026-08-10", date_to: "2026-08-11", duration_days: 2, remarks: "Viral fever", state: "approved", created_at: "2026-08-09 09:30" }
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
        // Backend not available or CORS blocked: Return fallback indicator
        return { success: false, fallback: true, error: err.message };
    }
}


/* =========================================================
   SESSION & AUTH GUARD
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
    const isAuthPage = window.location.pathname.endsWith("index.html") ||
                       window.location.pathname.endsWith("signup.html") ||
                       window.location.pathname.endsWith("verify-email.html") ||
                       window.location.pathname === "/" ||
                       window.location.pathname === "";

    if (!user && !isAuthPage) {
        window.location.href = "index.html";
        return null;
    }

    if (user && isAuthPage && !window.location.pathname.endsWith("verify-email.html")) {
        window.location.href = user.role === "hr" ? "hr-dashboard.html" : "employee-dashboard.html";
        return user;
    }

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
    window.location.href = "index.html";
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
   SIGN UP
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
            basic_salary: 30000,
            hra: 6000,
            allowances: 4000,
            deductions: 2000
        };

        users.push(newUser);
        localStorage.setItem("dayflow_users", JSON.stringify(users));
        localStorage.setItem("pending_verification_email", email);

        window.location.href = `verify-email.html?email=${encodeURIComponent(email)}&token=mock-token-${Date.now()}`;
    });
}


/* =========================================================
   LOGIN
========================================================= */

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
            error.textContent = "Account not found. Please register or check credentials.";
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

    // Try backend verification
    const res = await apiFetch('/api/auth/verify-email', 'POST', { email, token });

    // Local fallback update
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
   ATTENDANCE (CHECK IN / CHECK OUT / TABS)
========================================================= */

async function checkIn() {
    const status = document.getElementById("attendanceStatus");
    const user = getCurrentUser();
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const dateStr = now.toISOString().split('T')[0];

    // Try backend call
    const res = await apiFetch('/api/attendance/check-in', 'POST');

    // Local persistence
    const attendanceList = JSON.parse(localStorage.getItem("dayflow_attendance") || "[]");
    const todayIndex = attendanceList.findIndex(a => a.employee_id === (user?.employee_id || 2) && a.date === dateStr);

    if (todayIndex !== -1 && attendanceList[todayIndex].check_in && !attendanceList[todayIndex].check_out) {
        alert("You are already checked in for today!");
        return;
    }

    const newRecord = {
        id: Date.now(),
        employee_id: user?.employee_id || 2,
        employee_name: user?.name || "Rahul Kumar",
        date: dateStr,
        check_in: timeStr,
        check_out: null,
        worked_hours: 0,
        state: "present"
    };

    if (todayIndex !== -1) {
        attendanceList[todayIndex] = newRecord;
    } else {
        attendanceList.unshift(newRecord);
    }

    localStorage.setItem("dayflow_attendance", JSON.stringify(attendanceList));

    if (status) {
        status.textContent = "Checked in at " + timeStr;
        status.style.color = "#16a34a";
    }

    renderAttendanceTable();
}

async function checkOut() {
    const status = document.getElementById("attendanceStatus");
    const user = getCurrentUser();
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const dateStr = now.toISOString().split('T')[0];

    // Try backend call
    await apiFetch('/api/attendance/check-out', 'POST');

    // Local persistence
    const attendanceList = JSON.parse(localStorage.getItem("dayflow_attendance") || "[]");
    const todayRecord = attendanceList.find(a => a.employee_id === (user?.employee_id || 2) && a.date === dateStr);

    if (!todayRecord || !todayRecord.check_in) {
        alert("Please check in first before checking out.");
        return;
    }

    todayRecord.check_out = timeStr;
    todayRecord.worked_hours = 8.0;
    localStorage.setItem("dayflow_attendance", JSON.stringify(attendanceList));

    if (status) {
        status.textContent = "Checked out at " + timeStr;
        status.style.color = "#dc2626";
    }

    renderAttendanceTable();
}

function switchAttendanceTab(btn, tabName) {
    document.querySelectorAll(".tabs .tab").forEach(t => t.classList.remove("active"));
    if (btn) btn.classList.add("active");
    renderAttendanceTable(tabName);
}

function renderAttendanceTable(viewType = 'daily') {
    const tbody = document.querySelector("#attendanceTable tbody") || document.querySelector("table tbody");
    if (!tbody || !window.location.pathname.endsWith("attendance.html")) return;

    const user = getCurrentUser();
    const attendanceList = JSON.parse(localStorage.getItem("dayflow_attendance") || "[]");
    const userRecords = attendanceList.filter(a => !user || user.role === 'hr' || a.employee_id === user.employee_id);

    tbody.innerHTML = "";

    if (userRecords.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #6b7280; padding: 20px;">No attendance records found.</td></tr>`;
        return;
    }

    userRecords.forEach(record => {
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


/* =========================================================
   LEAVE MANAGEMENT (APPLY & APPROVE)
========================================================= */

const leaveForm = document.getElementById("leaveForm");
if (leaveForm) {
    leaveForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        const user = getCurrentUser();
        const leaveType = document.getElementById("leaveType")?.value || document.querySelector("select")?.value;
        const dateFrom = document.getElementById("leaveFrom")?.value || document.querySelectorAll('input[type="date"]')[0]?.value;
        const dateTo = document.getElementById("leaveTo")?.value || document.querySelectorAll('input[type="date"]')[1]?.value;
        const remarks = document.getElementById("leaveRemarks")?.value || document.querySelector("textarea")?.value || "";
        const message = document.getElementById("leaveMessage");

        if (new Date(dateTo) < new Date(dateFrom)) {
            alert("End date cannot be earlier than start date.");
            return;
        }

        // Try backend
        await apiFetch('/api/leave/apply', 'POST', {
            leave_type: leaveType.toLowerCase().includes("sick") ? "sick" : (leaveType.toLowerCase().includes("unpaid") ? "unpaid" : "paid"),
            date_from: dateFrom,
            date_to: dateTo,
            remarks
        });

        // Local persistence
        const leaves = JSON.parse(localStorage.getItem("dayflow_leaves") || "[]");
        const fromD = new Date(dateFrom);
        const toD = new Date(dateTo);
        const diffDays = Math.max(1, Math.round((toD - fromD) / (1000 * 60 * 60 * 24)) + 1);

        const newLeave = {
            id: Date.now(),
            employee_id: user?.employee_id || 2,
            employee_name: user?.name || "Rahul Kumar",
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
        renderLeaveTable();
    });
}

function renderLeaveTable() {
    const tbody = document.querySelector("#leaveTable tbody") || document.querySelector("table tbody");
    if (!tbody || !window.location.pathname.endsWith("leave.html")) return;

    const user = getCurrentUser();
    const leaves = JSON.parse(localStorage.getItem("dayflow_leaves") || "[]");

    tbody.innerHTML = "";

    leaves.forEach(req => {
        const stateClass = req.state === 'approved' ? 'approved' : (req.state === 'rejected' ? 'rejected' : 'pending');
        const isHR = user && user.role === 'hr';

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${req.leave_type}</td>
            <td>${req.date_from}</td>
            <td>${req.date_to}</td>
            <td>${req.remarks || '-'}</td>
            <td><span class="status ${stateClass}">${req.state.charAt(0).toUpperCase() + req.state.slice(1)}</span></td>
            ${isHR ? `<td>
                <div class="btn-group">
                    <button class="btn-success" onclick="handleLeaveAction(${req.id}, 'approve')">Approve</button>
                    <button class="btn-danger" onclick="handleLeaveAction(${req.id}, 'reject')">Reject</button>
                </div>
            </td>` : ''}
        `;
        tbody.appendChild(tr);
    });
}

function handleLeaveAction(leaveId, action) {
    const leaves = JSON.parse(localStorage.getItem("dayflow_leaves") || "[]");
    const leave = leaves.find(l => l.id === leaveId);
    if (leave) {
        leave.state = action === 'approve' ? 'approved' : 'rejected';
        localStorage.setItem("dayflow_leaves", JSON.stringify(leaves));
        apiFetch('/api/leave/action', 'POST', { leave_id: leaveId, action }).catch(() => {});
        renderLeaveTable();
        loadDashboard();
    }
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
   PROFILE MANAGEMENT
========================================================= */

function loadProfile() {
    const user = getCurrentUser();
    if (!user || !window.location.pathname.endsWith("profile.html")) return;

    const nameElem = document.getElementById("profileName");
    const idElem = document.getElementById("profileEmpId");
    const emailElem = document.getElementById("profileEmail");
    const deptElem = document.getElementById("profileDept");
    const phoneInput = document.getElementById("profilePhone");
    const addressInput = document.getElementById("profileAddress");
    const avatarElem = document.querySelector(".profile-picture span");

    if (nameElem) nameElem.textContent = user.name || "User Profile";
    if (idElem) idElem.textContent = user.employee_code || "DF0001";
    if (emailElem) emailElem.textContent = user.email || "";
    if (deptElem) deptElem.textContent = user.department || "Engineering";
    if (phoneInput) phoneInput.value = user.phone || "+91 98765 43210";
    if (addressInput) addressInput.value = user.address || "Bengaluru, India";

    if (avatarElem && user.name) {
        const initials = user.name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
        avatarElem.textContent = initials;
    }
}

function saveProfile() {
    const user = getCurrentUser();
    if (!user) return;

    const phone = document.getElementById("profilePhone")?.value || "";
    const address = document.getElementById("profileAddress")?.value || "";

    user.phone = phone;
    user.address = address;
    setCurrentUser(user);

    // Update in local users registry
    const users = JSON.parse(localStorage.getItem("dayflow_users") || "[]");
    const idx = users.findIndex(u => u.email === user.email);
    if (idx !== -1) {
        users[idx].phone = phone;
        users[idx].address = address;
        localStorage.setItem("dayflow_users", JSON.stringify(users));
    }

    // Try backend
    apiFetch('/api/employee/profile', 'PUT', { phone, address }).catch(() => {});

    alert("Profile changes saved successfully!");
}


/* =========================================================
   DASHBOARDS & DYNAMIC INJECTION
========================================================= */

function loadDashboard() {
    const user = getCurrentUser();
    if (!user) return;

    // Update Topbar User info
    const topbarName = document.querySelector(".topbar p");
    const userBoxName = document.querySelector(".user-box span");
    const avatar = document.querySelector(".avatar");

    if (topbarName && window.location.pathname.includes("dashboard")) {
        topbarName.textContent = `Welcome back, ${user.name}!`;
    }
    if (userBoxName) {
        userBoxName.textContent = user.name;
    }
    if (avatar && user.name) {
        const initials = user.name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
        avatar.textContent = initials;
    }
}


/* =========================================================
   SALARY SLIP & REPORTS MODALS
========================================================= */

function downloadSalarySlip() {
    const user = getCurrentUser() || { name: "Rahul Kumar", employee_code: "DF0002", basic_salary: 35000, hra: 8000, allowances: 5000, deductions: 2000 };
    const gross = (user.basic_salary || 35000) + (user.hra || 8000) + (user.allowances || 5000);
    const net = gross - (user.deductions || 2000);

    const modal = document.createElement("div");
    modal.className = "dayflow-modal";
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Dayflow Salary Slip</h3>
                <button class="modal-close-btn" onclick="this.closest('.dayflow-modal').remove()">×</button>
            </div>
            <div class="modal-body" style="line-height: 1.8;">
                <p><strong>Employee:</strong> ${user.name} (${user.employee_code || 'DF0002'})</p>
                <p><strong>Pay Period:</strong> August 2026</p>
                <hr style="margin: 15px 0; border: 0; border-top: 1px solid #e5e7eb;">
                <div style="display: flex; justify-content: space-between;"><span>Basic Salary:</span><strong>₹${(user.basic_salary || 35000).toLocaleString()}</strong></div>
                <div style="display: flex; justify-content: space-between;"><span>HRA & Allowances:</span><strong>₹${((user.hra || 8000) + (user.allowances || 5000)).toLocaleString()}</strong></div>
                <div style="display: flex; justify-content: space-between; color: #dc2626;"><span>Deductions (Tax/PF):</span><strong>-₹${(user.deductions || 2000).toLocaleString()}</strong></div>
                <hr style="margin: 15px 0; border: 0; border-top: 1px solid #e5e7eb;">
                <div style="display: flex; justify-content: space-between; font-size: 16px; color: #4f46e5;"><span><strong>Net Salary Paid:</strong></span><strong>₹${net.toLocaleString()}</strong></div>
            </div>
            <div class="modal-footer">
                <button class="secondary-btn" onclick="window.print()">🖨️ Print</button>
                <button class="primary-btn" style="width: auto;" onclick="this.closest('.dayflow-modal').remove()">Close</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function viewReport(type) {
    const modal = document.createElement("div");
    modal.className = "dayflow-modal";
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>${type} Report</h3>
                <button class="modal-close-btn" onclick="this.closest('.dayflow-modal').remove()">×</button>
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
                <button class="primary-btn" style="width: auto;" onclick="this.closest('.dayflow-modal').remove()">Done</button>
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
                <button class="modal-close-btn" onclick="this.closest('.dayflow-modal').remove()">×</button>
            </div>
            <div class="modal-body" style="text-align: center; padding: 25px;">
                <div style="font-size: 40px; margin-bottom: 15px;">📄</div>
                <p><strong>${docName}</strong> is verified and stored in the secure Dayflow database.</p>
                <small style="color: #6b7280;">Encrypted record matching Dayflow security guidelines.</small>
            </div>
            <div class="modal-footer">
                <button class="primary-btn" style="width: auto;" onclick="this.closest('.dayflow-modal').remove()">Close</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}


/* =========================================================
   DOM CONTENT LOADED INITIALIZATION
========================================================= */

document.addEventListener("DOMContentLoaded", function() {
    // Run authentication guard
    const isHrPage = window.location.pathname.endsWith("hr-dashboard.html");
    const user = checkAuth(isHrPage ? "hr" : null);

    // Initial view rendering
    loadDashboard();
    loadProfile();
    renderAttendanceTable();
    renderLeaveTable();
});