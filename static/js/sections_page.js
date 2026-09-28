/**
 * sections_page.js
 * Sections tab (Admin only): CRUD for sections and sub-sections.
 * Requires: dashboard_common.js
 */

let allSectionsCache = [];

async function loadSections() {
    const tbody = document.getElementById("sectionsTableBody");
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="7" class="table-empty">Loading sections...</td></tr>`;

    try {
        const response = await fetch(window.DASHBOARD_URLS.sectionsListApi || "/api/sections/", {
            credentials: "same-origin",
            headers: { "X-Requested-With": "XMLHttpRequest" },
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.message || "Failed to load sections");
        }

        const data = await response.json();
        allSectionsCache = Array.isArray(data) ? data : [];
        renderSectionsTable(allSectionsCache);
    } catch (error) {
        console.error(error);
        tbody.innerHTML = `<tr><td colspan="7" class="table-empty" style="color:#ef4444;">${escapeHtml(error.message)}</td></tr>`;
    }
}

function filterSectionsTable() {
    const q = (document.getElementById("sectionSearch")?.value || "").trim().toLowerCase();
    if (!q) return renderSectionsTable(allSectionsCache);

    renderSectionsTable(
        allSectionsCache.filter(
            (s) =>
                (s.name || "").toLowerCase().includes(q) ||
                (s.slug || "").toLowerCase().includes(q) ||
                (s.model_key || "").toLowerCase().includes(q)
        )
    );
}

function renderSectionsTable(list) {
    const tbody = document.getElementById("sectionsTableBody");
    if (!tbody) return;

    if (!list.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="table-empty">No sections found.</td></tr>`;
        return;
    }

    tbody.innerHTML = list
        .map((s) => {
            const typeBadge = s.is_system
                ? `<span style="padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;background:#e0e7ff;color:#3730a3;">System</span>`
                : `<span style="padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;background:#fce7f3;color:#9d174d;">Custom</span>`;

            const statusBadge = s.is_active
                ? `<span style="padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;background:#dcfce7;color:#166534;">Active</span>`
                : `<span style="padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;background:#fee2e2;color:#991b1b;">Hidden</span>`;

            const publicBadge = s.show_on_public ? "Yes" : "No";
            const safeName = (s.name || "").replace(/'/g, "\\'");
            const deleteBtn = s.is_system
                ? ""
                : `<button type="button" style="padding:4px 10px;font-size:12px;border-radius:6px;border:1.5px solid #fecaca;background:#fef2f2;color:#b91c1c;cursor:pointer;"
                        onclick="deleteSection(${s.id}, '${safeName}')">Delete</button>`;

            const subList =
                (s.subsections || [])
                    .map(
                        (sub) =>
                            `<div style="font-size:12px;margin:2px 0;">
                • ${escapeHtml(sub.name)}
                <button type="button" style="margin-left:6px;font-size:11px;border:none;background:transparent;color:#2563eb;cursor:pointer;"
                        onclick='openEditSubsectionModal(${JSON.stringify(sub)}, ${JSON.stringify({ id: s.id, name: s.name })})'>Edit</button>
                <button type="button" style="font-size:11px;border:none;background:transparent;color:#dc2626;cursor:pointer;"
                        onclick="deleteSubsection(${sub.id}, '${(sub.name || "").replace(/'/g, "\\'")}')">Del</button>
            </div>`
                    )
                    .join("") || "<span style='color:#94a3b8;font-size:12px;'>—</span>";

            return `<tr>
            <td>${s.display_order}</td>
            <td><strong>${escapeHtml(s.icon || "")} ${escapeHtml(s.name)}</strong></td>
            <td>${typeBadge}</td>
            <td>${statusBadge}</td>
            <td>${publicBadge}</td>
            <td>
                ${subList}
                ${
                    s.allow_subsections
                        ? `<button type="button" class="primary-button" style="padding:3px 8px;font-size:11px;margin-top:4px;"
                    onclick='openAddSubsectionModal(${JSON.stringify({ id: s.id, name: s.name })})'>+ Sub-section</button>`
                        : ""
                }
            </td>
            <td style="white-space:nowrap;">
                <button type="button" class="primary-button" style="padding:4px 10px;font-size:12px;margin-right:4px;"
                        onclick='openEditSectionModal(${JSON.stringify(s)})'>Edit</button>
                <button type="button" style="padding:4px 10px;font-size:12px;border-radius:6px;border:1.5px solid #cbd5e1;background:white;cursor:pointer;margin-right:4px;"
                        onclick="toggleSectionStatus(${s.id})">${s.is_active ? "Hide" : "Show"}</button>
                ${deleteBtn}
            </td>
        </tr>`;
        })
        .join("");
}

/* ---------- Section modal ---------- */
function openAddSectionModal() {
    document.getElementById("sectionModalTitle").textContent = "Add Section";
    document.getElementById("section_id").value = "";
    document.getElementById("section_name").value = "";
    document.getElementById("section_icon").value = "📁";
    document.getElementById("section_description").value = "";
    document.getElementById("section_display_order").value = "";
    document.getElementById("section_is_active").checked = true;
    document.getElementById("section_show_on_public").checked = true;
    document.getElementById("section_allow_subsections").checked = true;
    document.getElementById("saveSectionButton").textContent = "Create Section";
    document.getElementById("sectionModalOverlay").classList.add("active");
}

function openEditSectionModal(s) {
    document.getElementById("sectionModalTitle").textContent = "Edit Section";
    document.getElementById("section_id").value = s.id;
    document.getElementById("section_name").value = s.name || "";
    document.getElementById("section_icon").value = s.icon || "📁";
    document.getElementById("section_description").value = s.description || "";
    document.getElementById("section_display_order").value = s.display_order ?? "";
    document.getElementById("section_is_active").checked = !!s.is_active;
    document.getElementById("section_show_on_public").checked = !!s.show_on_public;
    document.getElementById("section_allow_subsections").checked = !!s.allow_subsections;
    document.getElementById("saveSectionButton").textContent = "Update Section";
    document.getElementById("sectionModalOverlay").classList.add("active");
}

function closeSectionModal() {
    document.getElementById("sectionModalOverlay")?.classList.remove("active");
}

async function saveSection(event) {
    event.preventDefault();
    const id = document.getElementById("section_id").value;
    const payload = {
        name: document.getElementById("section_name").value.trim(),
        icon: document.getElementById("section_icon").value.trim() || "📁",
        description: document.getElementById("section_description").value.trim(),
        is_active: document.getElementById("section_is_active").checked,
        show_on_public: document.getElementById("section_show_on_public").checked,
        allow_subsections: document.getElementById("section_allow_subsections").checked,
    };
    const order = document.getElementById("section_display_order").value;
    if (order !== "") payload.display_order = parseInt(order, 10);
    if (id) payload.id = parseInt(id, 10);

    const btn = document.getElementById("saveSectionButton");
    const original = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Saving...";

    try {
        const url = id
            ? window.DASHBOARD_URLS.updateSection || "/api/sections/update/"
            : window.DASHBOARD_URLS.createSection || "/api/sections/create/";

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            credentials: "same-origin",
            body: JSON.stringify(payload),
        });

        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.message || "Failed");

        closeSectionModal();
        alert(result.message || "Saved.");
        loadSections();
        if (typeof refreshAppSectionsFromAPI === "function") refreshAppSectionsFromAPI();
    } catch (e) {
        alert(e.message || "Failed to save section.");
    } finally {
        btn.disabled = false;
        btn.textContent = original;
    }
}

async function toggleSectionStatus(id) {
    try {
        const response = await fetch(
            window.DASHBOARD_URLS.toggleSectionStatus || "/api/sections/toggle-status/",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                credentials: "same-origin",
                body: JSON.stringify({ id }),
            }
        );
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.message || "Failed");
        loadSections();
        if (typeof refreshAppSectionsFromAPI === "function") refreshAppSectionsFromAPI();
    } catch (e) {
        alert(e.message || "Failed to toggle status.");
    }
}

async function deleteSection(id, name) {
    if (
        !confirm(
            `Delete section "${name}"?\nAll custom documents under it will also be deleted.\nSystem sections cannot be deleted.`
        )
    )
        return;

    try {
        const response = await fetch(window.DASHBOARD_URLS.deleteSection || "/api/sections/delete/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            credentials: "same-origin",
            body: JSON.stringify({ id }),
        });
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.message || "Failed");
        alert(result.message);
        loadSections();
        if (typeof refreshAppSectionsFromAPI === "function") refreshAppSectionsFromAPI();
    } catch (e) {
        alert(e.message || "Failed to delete section.");
    }
}

/* ---------- Sub-section modal ---------- */
function openAddSubsectionModal(section) {
    document.getElementById("subsectionModalTitle").textContent = "Add Sub-section";
    document.getElementById("subsection_id").value = "";
    document.getElementById("subsection_section_id").value = section.id;
    document.getElementById("subsection_section_name").value = section.name;
    document.getElementById("subsection_name").value = "";
    document.getElementById("subsection_display_order").value = "";
    document.getElementById("subsection_is_active").checked = true;
    document.getElementById("saveSubsectionButton").textContent = "Create Sub-section";
    document.getElementById("subsectionModalOverlay").classList.add("active");
}

function openEditSubsectionModal(sub, section) {
    document.getElementById("subsectionModalTitle").textContent = "Edit Sub-section";
    document.getElementById("subsection_id").value = sub.id;
    document.getElementById("subsection_section_id").value = section.id;
    document.getElementById("subsection_section_name").value = section.name;
    document.getElementById("subsection_name").value = sub.name || "";
    document.getElementById("subsection_display_order").value = sub.display_order ?? "";
    document.getElementById("subsection_is_active").checked = !!sub.is_active;
    document.getElementById("saveSubsectionButton").textContent = "Update Sub-section";
    document.getElementById("subsectionModalOverlay").classList.add("active");
}

function closeSubsectionModal() {
    document.getElementById("subsectionModalOverlay")?.classList.remove("active");
}

async function saveSubsection(event) {
    event.preventDefault();
    const id = document.getElementById("subsection_id").value;
    const payload = {
        name: document.getElementById("subsection_name").value.trim(),
        section_id: parseInt(document.getElementById("subsection_section_id").value, 10),
        is_active: document.getElementById("subsection_is_active").checked,
    };
    const order = document.getElementById("subsection_display_order").value;
    if (order !== "") payload.display_order = parseInt(order, 10);
    if (id) payload.id = parseInt(id, 10);

    const btn = document.getElementById("saveSubsectionButton");
    const original = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Saving...";

    try {
        const url = id
            ? window.DASHBOARD_URLS.updateSubsection || "/api/subsections/update/"
            : window.DASHBOARD_URLS.createSubsection || "/api/subsections/create/";

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            credentials: "same-origin",
            body: JSON.stringify(payload),
        });
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.message || "Failed");

        closeSubsectionModal();
        alert(result.message || "Saved.");
        loadSections();
        if (typeof refreshAppSectionsFromAPI === "function") refreshAppSectionsFromAPI();
    } catch (e) {
        alert(e.message || "Failed to save sub-section.");
    } finally {
        btn.disabled = false;
        btn.textContent = original;
    }
}

async function deleteSubsection(id, name) {
    if (!confirm(`Delete sub-section "${name}"?`)) return;

    try {
        const response = await fetch(
            window.DASHBOARD_URLS.deleteSubsection || "/api/subsections/delete/",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                credentials: "same-origin",
                body: JSON.stringify({ id }),
            }
        );
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.message || "Failed");
        loadSections();
        if (typeof refreshAppSectionsFromAPI === "function") refreshAppSectionsFromAPI();
    } catch (e) {
        alert(e.message || "Failed to delete sub-section.");
    }
}

document.addEventListener("DOMContentLoaded", function () {
    if (!window.IS_ADMIN) {
        alert("You do not have permission to manage Sections.");
        return;
    }
    loadSections();

    document.addEventListener("click", function (e) {
        if (e.target?.id === "sectionModalOverlay") closeSectionModal();
        if (e.target?.id === "subsectionModalOverlay") closeSubsectionModal();
    });
});

window.loadSections = loadSections;
window.filterSectionsTable = filterSectionsTable;
window.openAddSectionModal = openAddSectionModal;
window.openEditSectionModal = openEditSectionModal;
window.closeSectionModal = closeSectionModal;
window.saveSection = saveSection;
window.toggleSectionStatus = toggleSectionStatus;
window.deleteSection = deleteSection;
window.openAddSubsectionModal = openAddSubsectionModal;
window.openEditSubsectionModal = openEditSubsectionModal;
window.closeSubsectionModal = closeSubsectionModal;
window.saveSubsection = saveSubsection;
window.deleteSubsection = deleteSubsection;
