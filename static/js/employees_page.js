/**
 * employees_page.js
 * Employees tab (Admin only): pending approvals, list, add/edit, toggle status, delete.
 * Requires: dashboard_common.js
 */


let allEmployeesCache = [];

function resolveEmployeeUrl(key, fallbackPath) {
    if (window.DASHBOARD_URLS && window.DASHBOARD_URLS[key]) {
        return window.DASHBOARD_URLS[key];
    }
    if (typeof window.appUrl === "function") {
        return window.appUrl(fallbackPath);
    }
    return fallbackPath;
}

function roleBadge(role) {
    const r = (role || "").toUpperCase();
    if (r === "ADMIN") {
        return `<span style="padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;background:#e0e7ff;color:#3730a3;">Admin</span>`;
    }
    if (r === "CLIENT") {
        return `<span style="padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;background:#fef3c7;color:#92400e;">Client</span>`;
    }
    return `<span style="padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;background:#f1f5f9;color:#475569;">Employee</span>`;
}

function approvalStatusBadge(status) {
    const s = (status || "APPROVED").toUpperCase();
    if (s === "PENDING") {
        return `<span style="padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;background:#fef3c7;color:#92400e;">Pending</span>`;
    }
    if (s === "REJECTED") {
        return `<span style="padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;background:#fee2e2;color:#991b1b;">Rejected</span>`;
    }
    return `<span style="padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;background:#dcfce7;color:#166534;">Approved</span>`;
}

function statusBadge(isActive) {
    return isActive
        ? `<span style="padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;background:#dcfce7;color:#166534;">Active</span>`
        : `<span style="padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;background:#fee2e2;color:#991b1b;">Inactive</span>`;
}

function renderPendingApprovalsTable(list) {
    const tbody = document.getElementById("pendingApprovalsTableBody");
    if (!tbody) return;

    const pendingUsers = (list || []).filter(
        (u) => (u.approval_status || "").toUpperCase() === "PENDING"
    );

    if (!pendingUsers.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="table-empty">No pending registration requests.</td></tr>`;
        return;
    }

    tbody.innerHTML = pendingUsers
        .map((u) => {
            const empName = u.full_name || [u.first_name, u.last_name].filter(Boolean).join(" ") || u.username;
            const empId = u.employee_id || u.username || "—";
            const email = u.email || "—";
            const encodedUser = encodeURIComponent(JSON.stringify(u));

            return `<tr>
                <td><strong>${escapeHtml(empName)}</strong></td>
                <td>${escapeHtml(empId)}</td>
                <td>${escapeHtml(email)}</td>
                <td>${escapeHtml(u.username || "—")}</td>
                <td>${escapeHtml(u.date_joined || "—")}</td>
                <td>${approvalStatusBadge(u.approval_status)}</td>
                <td style="white-space:nowrap;">
                    <button type="button" class="primary-button" style="padding:4px 10px;font-size:12px;margin-right:4px;"
                            onclick="reviewApprovalRequest('${encodedUser}', 'approve')">Approve</button>
                    <button type="button" style="padding:4px 10px;font-size:12px;border-radius:6px;border:1.5px solid #fecaca;background:#fef2f2;color:#b91c1c;cursor:pointer;"
                            onclick="reviewApprovalRequest('${encodedUser}', 'reject')">Reject</button>
                </td>
            </tr>`;
        })
        .join("");
}

async function reviewApprovalRequest(encodedUser, decision) {
    const u = JSON.parse(decodeURIComponent(encodedUser));
    const empName = u.full_name || [u.first_name, u.last_name].filter(Boolean).join(" ") || u.username;
    const empId = u.employee_id || u.username || "—";
    const verb = decision === "approve" ? "approve" : "reject";

    const reviewPrompt =
        `Review Registration Request:\n` +
        `• Employee Name: ${empName}\n` +
        `• Employee ID: ${empId}\n` +
        `• Official Email: ${u.email || "—"}\n` +
        `• Username: ${u.username || "—"}\n` +
        `• Registration Date: ${u.date_joined || "—"}\n` +
        `• Current Status: ${u.approval_status || "PENDING"}\n\n` +
        `Do you want to ${verb.toUpperCase()} this account?`;

    if (!confirm(reviewPrompt)) return;

    const url =
        decision === "approve"
            ? resolveEmployeeUrl("approveEmployee", "/api/employees/approve/")
            : resolveEmployeeUrl("rejectEmployee", "/api/employees/reject/");

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
                "X-Requested-With": "XMLHttpRequest",
            },
            credentials: "same-origin",
            body: JSON.stringify({ id: u.id }),
        });

        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || `Failed to ${verb} account.`);
        }

        alert(result.message || `Account ${verb}d.`);
        loadEmployees();
    } catch (error) {
        console.error("reviewApprovalRequest error:", error);
        alert(error.message || `Failed to ${verb} account.`);
    }
}

async function loadEmployees() {
    const tbody = document.getElementById("employeesTableBody");
    const pendingTbody = document.getElementById("pendingApprovalsTableBody");
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="9" class="table-empty">Loading employees...</td></tr>`;
    if (pendingTbody) {
        pendingTbody.innerHTML = `<tr><td colspan="7" class="table-empty">Loading registration requests...</td></tr>`;
    }

    try {
        const response = await fetch(resolveEmployeeUrl("employeesList", "/api/employees/"), {
            credentials: "same-origin",
            headers: { "X-Requested-With": "XMLHttpRequest" },
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.message || "Failed to load employees");
        }

        const data = await response.json();
        allEmployeesCache = Array.isArray(data) ? data : data.results || [];
        renderPendingApprovalsTable(allEmployeesCache);
        renderEmployeesTable(allEmployeesCache);
    } catch (error) {
        console.error("loadEmployees error:", error);
        tbody.innerHTML = `<tr><td colspan="9" class="table-empty" style="color:#ef4444;">${escapeHtml(error.message)}</td></tr>`;
        if (pendingTbody) {
            pendingTbody.innerHTML = `<tr><td colspan="7" class="table-empty" style="color:#ef4444;">${escapeHtml(error.message)}</td></tr>`;
        }
    }
}

function filterEmployeesTable() {
    const q = (document.getElementById("employeeSearch")?.value || "").trim().toLowerCase();
    if (!q) return renderEmployeesTable(allEmployeesCache);

    renderEmployeesTable(
        allEmployeesCache.filter((u) => {
            const name = `${u.first_name || ""} ${u.last_name || ""}`.toLowerCase();
            return (
                (u.username || "").toLowerCase().includes(q) ||
                (u.employee_id || "").toLowerCase().includes(q) ||
                name.includes(q) ||
                (u.email || "").toLowerCase().includes(q) ||
                (u.approval_status || "").toLowerCase().includes(q)
            );
        })
    );
}

function renderEmployeesTable(list) {
    const tbody = document.getElementById("employeesTableBody");
    if (!tbody) return;

    if (!list.length) {
        tbody.innerHTML = `<tr><td colspan="9" class="table-empty">No employees found.</td></tr>`;
        return;
    }

    tbody.innerHTML = list
        .map((u) => {
            const fullName = [u.first_name, u.last_name].filter(Boolean).join(" ") || "—";
            const email = u.email || "—";
            const empId = u.employee_id || u.username || "";
            const encodedUser = encodeURIComponent(JSON.stringify(u));
            const encodedName = encodeURIComponent(u.username || "");

            return `<tr>
                <td><strong>${escapeHtml(empId)}</strong></td>
                <td>${escapeHtml(fullName)}</td>
                <td>${escapeHtml(email)}</td>
                <td>${roleBadge(u.role)}</td>
                <td>${approvalStatusBadge(u.approval_status)}</td>
                <td>${statusBadge(!!u.is_active)}</td>
                <td>${escapeHtml(u.date_joined || "—")}</td>
                <td>${escapeHtml(u.last_login || "Never")}</td>
                <td style="white-space:nowrap;">
                    <button type="button" class="primary-button" style="padding:4px 10px;font-size:12px;margin-right:4px;"
                            onclick="openEditEmployeeFromEncoded('${encodedUser}')">Edit</button>
                    <button type="button" style="padding:4px 10px;font-size:12px;border-radius:6px;border:1.5px solid #cbd5e1;background:white;cursor:pointer;margin-right:4px;"
                            onclick="toggleEmployeeStatus(${u.id}, decodeURIComponent('${encodedName}'))">
                        ${u.is_active ? "Deactivate" : "Activate"}
                    </button>
                    <button type="button" style="padding:4px 10px;font-size:12px;border-radius:6px;border:1.5px solid #fecaca;background:#fef2f2;color:#b91c1c;cursor:pointer;"
                            onclick="deleteEmployee(${u.id}, decodeURIComponent('${encodedName}'))">Delete</button>
                </td>
            </tr>`;
        })
        .join("");
}

function openAddEmployeeModal() {
    document.getElementById("employeeModalTitle").textContent = "Add User";
    document.getElementById("employee_id").value = "";
    document.getElementById("employee_username").value = "";
    document.getElementById("employee_username").readOnly = false;
    document.getElementById("employee_first_name").value = "";
    document.getElementById("employee_last_name").value = "";
    document.getElementById("employee_email").value = "";
    document.getElementById("employee_role").value = "EMPLOYEE";
    document.getElementById("employee_password").value = "";
    document.getElementById("employee_password").required = true;
    document.getElementById("passwordRequiredMark").style.display = "inline";
    document.getElementById("employee_is_active").checked = true;
    document.getElementById("saveEmployeeButton").textContent = "Create User";
    document.getElementById("usernameHelp").textContent = "Used for login. Cannot be changed after creation.";
    document.getElementById("employeeModalOverlay").classList.add("active");
}

function openEditEmployeeFromEncoded(encoded) {
    openEditEmployeeModal(JSON.parse(decodeURIComponent(encoded)));
}

function openEditEmployeeModal(user) {
    document.getElementById("employeeModalTitle").textContent = "Edit User";
    document.getElementById("employee_id").value = user.id;
    document.getElementById("employee_username").value = user.username || "";
    document.getElementById("employee_username").readOnly = true;
    document.getElementById("employee_first_name").value = user.first_name || "";
    document.getElementById("employee_last_name").value = user.last_name || "";
    document.getElementById("employee_email").value = user.email || "";
    document.getElementById("employee_role").value = user.role || "EMPLOYEE";
    document.getElementById("employee_password").value = "";
    document.getElementById("employee_password").required = false;
    document.getElementById("passwordRequiredMark").style.display = "none";
    document.getElementById("employee_is_active").checked = !!user.is_active;
    document.getElementById("saveEmployeeButton").textContent = "Update User";
    document.getElementById("usernameHelp").textContent = "Employee ID cannot be changed.";
    document.getElementById("employeeModalOverlay").classList.add("active");
}

function closeEmployeeModal() {
    document.getElementById("employeeModalOverlay")?.classList.remove("active");
}

async function saveEmployee(event) {
    event.preventDefault();

    const id = document.getElementById("employee_id").value;
    const payload = {
        username: document.getElementById("employee_username").value.trim(),
        first_name: document.getElementById("employee_first_name").value.trim(),
        last_name: document.getElementById("employee_last_name").value.trim(),
        email: document.getElementById("employee_email").value.trim(),
        role: document.getElementById("employee_role").value,
        is_active: document.getElementById("employee_is_active").checked,
    };

    const password = document.getElementById("employee_password").value;
    if (password) payload.password = password;
    if (id) payload.id = parseInt(id, 10);

    if (!id && (!password || password.length < 6)) {
        alert("Password is required (min. 6 characters) when creating a user.");
        return;
    }

    const btn = document.getElementById("saveEmployeeButton");
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Saving...";

    try {
        const url = id
            ? resolveEmployeeUrl("updateEmployee", "/api/employees/update/")
            : resolveEmployeeUrl("createEmployee", "/api/employees/create/");

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
                "X-Requested-With": "XMLHttpRequest",
            },
            credentials: "same-origin",
            body: JSON.stringify(payload),
        });

        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "Failed to save user.");
        }

        closeEmployeeModal();
        alert(result.message || "Saved successfully.");
        loadEmployees();
    } catch (error) {
        console.error("saveEmployee error:", error);
        alert(error.message || "Failed to save user.");
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

async function toggleEmployeeStatus(userId, username) {
    if (!confirm(`Change active status for "${username}"?`)) return;

    try {
        const response = await fetch(
            resolveEmployeeUrl("toggleEmployeeStatus", "/api/employees/toggle-status/"),
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken"),
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "same-origin",
                body: JSON.stringify({ id: userId }),
            }
        );

        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "Failed to update status.");
        }

        alert(result.message || "Status updated.");
        loadEmployees();
    } catch (error) {
        console.error("toggleEmployeeStatus error:", error);
        alert(error.message || "Failed to update status.");
    }
}

async function deleteEmployee(userId, username) {
    if (!confirm(`Delete user "${username}" permanently?\nThis cannot be undone.`)) return;

    try {
        const response = await fetch(resolveEmployeeUrl("deleteEmployee", "/api/employees/delete/"), {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
                "X-Requested-With": "XMLHttpRequest",
            },
            credentials: "same-origin",
            body: JSON.stringify({ id: userId }),
        });

        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "Failed to delete user.");
        }

        alert(result.message || "User deleted.");
        loadEmployees();
    } catch (error) {
        console.error("deleteEmployee error:", error);
        alert(error.message || "Failed to delete user.");
    }
}

document.addEventListener("DOMContentLoaded", function () {
    if (!window.IS_ADMIN) {
        alert("You do not have permission to manage Employees.");
        return;
    }
    loadEmployees();

    document.addEventListener("click", function (e) {
        const overlay = document.getElementById("employeeModalOverlay");
        if (overlay && e.target === overlay) closeEmployeeModal();
    });
});

window.loadEmployees = loadEmployees;
window.filterEmployeesTable = filterEmployeesTable;
window.openAddEmployeeModal = openAddEmployeeModal;
window.openEditEmployeeModal = openEditEmployeeModal;
window.openEditEmployeeFromEncoded = openEditEmployeeFromEncoded;
window.closeEmployeeModal = closeEmployeeModal;
window.saveEmployee = saveEmployee;
window.toggleEmployeeStatus = toggleEmployeeStatus;
window.deleteEmployee = deleteEmployee;
window.reviewApprovalRequest = reviewApprovalRequest;