/**
 * employees_page.js
 * Employees tab (Admin only): list, add/edit, toggle status, delete.
 * Requires: dashboard_common.js
 */

let allEmployeesCache = [];

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

function statusBadge(isActive) {
    return isActive
        ? `<span style="padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;background:#dcfce7;color:#166534;">Active</span>`
        : `<span style="padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;background:#fee2e2;color:#991b1b;">Inactive</span>`;
}

async function loadEmployees() {
    const tbody = document.getElementById("employeesTableBody");
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="8" class="table-empty">Loading employees...</td></tr>`;

    try {
        const response = await fetch(window.DASHBOARD_URLS.employeesList || "/api/employees/", {
            credentials: "same-origin",
            headers: { "X-Requested-With": "XMLHttpRequest" },
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.message || "Failed to load employees");
        }

        const data = await response.json();
        allEmployeesCache = Array.isArray(data) ? data : data.results || [];
        renderEmployeesTable(allEmployeesCache);
    } catch (error) {
        console.error("loadEmployees error:", error);
        tbody.innerHTML = `<tr><td colspan="8" class="table-empty" style="color:#ef4444;">${escapeHtml(error.message)}</td></tr>`;
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
                name.includes(q) ||
                (u.email || "").toLowerCase().includes(q)
            );
        })
    );
}

function renderEmployeesTable(list) {
    const tbody = document.getElementById("employeesTableBody");
    if (!tbody) return;

    if (!list.length) {
        tbody.innerHTML = `<tr><td colspan="8" class="table-empty">No employees found.</td></tr>`;
        return;
    }

    tbody.innerHTML = list
        .map((u) => {
            const fullName = [u.first_name, u.last_name].filter(Boolean).join(" ") || "—";
            const email = u.email || "—";
            const safeUser = JSON.stringify(u).replace(/'/g, "&#39;");

            return `<tr>
                <td><strong>${escapeHtml(u.username || "")}</strong></td>
                <td>${escapeHtml(fullName)}</td>
                <td>${escapeHtml(email)}</td>
                <td>${roleBadge(u.role)}</td>
                <td>${statusBadge(!!u.is_active)}</td>
                <td>${escapeHtml(u.date_joined || "—")}</td>
                <td>${escapeHtml(u.last_login || "Never")}</td>
                <td style="white-space:nowrap;">
                    <button type="button" class="primary-button" style="padding:4px 10px;font-size:12px;margin-right:4px;"
                            onclick='openEditEmployeeModal(${safeUser})'>Edit</button>
                    <button type="button" style="padding:4px 10px;font-size:12px;border-radius:6px;border:1.5px solid #cbd5e1;background:white;cursor:pointer;margin-right:4px;"
                            onclick="toggleEmployeeStatus(${u.id}, '${escapeHtml(u.username || "")}')">
                        ${u.is_active ? "Deactivate" : "Activate"}
                    </button>
                    <button type="button" style="padding:4px 10px;font-size:12px;border-radius:6px;border:1.5px solid #fecaca;background:#fef2f2;color:#b91c1c;cursor:pointer;"
                            onclick="deleteEmployee(${u.id}, '${escapeHtml(u.username || "")}')">Delete</button>
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
        // Use create or update URL based on whether id exists
        const url = id
            ? (window.DASHBOARD_URLS.updateEmployee || "/api/employees/update/")
            : (window.DASHBOARD_URLS.createEmployee || "/api/employees/create/");

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
            window.DASHBOARD_URLS.toggleEmployeeStatus || "/api/employees/toggle-status/",
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
        const response = await fetch(window.DASHBOARD_URLS.deleteEmployee || "/api/employees/delete/", {
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
window.closeEmployeeModal = closeEmployeeModal;
window.saveEmployee = saveEmployee;
window.toggleEmployeeStatus = toggleEmployeeStatus;
window.deleteEmployee = deleteEmployee;
