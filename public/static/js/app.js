// CMS Kanpur BCA/MCA Alumni Technical Platform - Application Orchestrator

const App = {
  currentUser: null,
  activeView: "home",
  activeConversationId: null,
  activeAlumniId: null,
  adminCharts: {},

  init() {
    this.bindEvents();
    if (window.location.pathname === "/auth" && !window.location.hash) {
      window.location.hash = "#auth";
    }
    this.checkAuth().then(() => {
      this.handleHashChange();
    });
    // Global notification polling every 30 seconds
    setInterval(() => {
      if (this.currentUser) this.fetchNotifications();
    }, 30000);
  },

  async checkAuth() {
    const token = API.getToken();
    if (!token) {
      this.currentUser = null;
      this.updateAuthUI();
      return;
    }

    try {
      const data = await API.get("/api/auth/me");
      if (data && typeof data === "object" && (data.user_id || data.email)) {
        this.currentUser = data;
        API.setUser(data);
        this.updateAuthUI();
        if (typeof this.fetchNotifications === "function") this.fetchNotifications();
        if (typeof this.checkAndShowProfilePrompt === "function") this.checkAndShowProfilePrompt();
      }
    } catch (err) {
      console.warn("Auth check failed:", err.message);
      if (err.message && (err.message.includes("401") || err.message.includes("unauthorized") || err.message.includes("credentials"))) {
        API.setToken(null);
        API.setUser(null);
        this.currentUser = null;
        this.updateAuthUI();
      }
    }
  },

  updateAuthUI() {
    const isAuth = !!this.currentUser;
    const body = document.body;
    const cmsNavbar = document.getElementById("cmsNavbar");
    const navbarToggler = document.querySelector(".navbar-toggler");
    const authActions = document.getElementById("auth-actions");
    const userMenu = document.getElementById("user-menu");
    const adminNav = document.getElementById("nav-admin-link");
    const topAuthLoggedOut = document.getElementById("top-auth-logged-out");
    const topAuthLoggedIn = document.getElementById("top-auth-logged-in");
    const topUserName = document.getElementById("top-user-name");
    const topUserRole = document.getElementById("top-user-role-badge");
    const userEmailEl = document.getElementById("user-dropdown-email");
    const dropdownAdminItem = document.getElementById("dropdown-admin-item");

    if (isAuth) {
      body.classList.remove("user-logged-out");
      body.classList.add("user-logged-in");
      if (cmsNavbar) cmsNavbar.classList.remove("d-none-auth");
      if (navbarToggler) navbarToggler.classList.remove("d-none-auth");
      if (authActions) authActions.classList.add("d-none");
      if (userMenu) userMenu.classList.remove("d-none");
      if (topAuthLoggedOut) topAuthLoggedOut.classList.add("d-none");
      if (topAuthLoggedIn) topAuthLoggedIn.classList.remove("d-none");

      const userNameEl = document.getElementById("user-display-name");
      const userRoleBadge = document.getElementById("user-role-badge");
      const userAvatar = document.getElementById("user-nav-avatar");

      const name = this.currentUser.profile?.full_name || this.currentUser.full_name || (this.currentUser.email ? this.currentUser.email.split("@")[0] : "User");
      if (userNameEl) userNameEl.innerText = name;
      if (topUserName) topUserName.innerText = name;
      if (userEmailEl) userEmailEl.innerText = this.currentUser.email || "";

      const roleBadgeClass = this.currentUser.role === "alumni" ? "bg-primary text-white" :
        this.currentUser.role === "student" ? "bg-info text-dark" : "bg-warning text-dark";

      if (userRoleBadge) {
        userRoleBadge.innerText = this.currentUser.role.toUpperCase();
        userRoleBadge.className = `badge ms-1 ${roleBadgeClass}`;
      }
      if (topUserRole) {
        topUserRole.innerText = this.currentUser.role.toUpperCase();
        topUserRole.className = `badge ${roleBadgeClass} fw-bold px-2 py-1`;
      }
      if (userAvatar) {
        userAvatar.innerText = name.charAt(0).toUpperCase();
      }

      // Admin navigation visibility
      const isAdmin = ["admin", "super_admin", "faculty"].includes(this.currentUser.role);
      if (adminNav) {
        if (isAdmin) adminNav.classList.remove("d-none");
        else adminNav.classList.add("d-none");
      }
      if (dropdownAdminItem) {
        if (isAdmin) dropdownAdminItem.classList.remove("d-none");
        else dropdownAdminItem.classList.add("d-none");
      }
    } else {
      body.classList.add("user-logged-out");
      body.classList.remove("user-logged-in");
      if (cmsNavbar) cmsNavbar.classList.add("d-none-auth");
      if (navbarToggler) navbarToggler.classList.add("d-none-auth");
      if (authActions) authActions.classList.add("d-none");
      if (userMenu) userMenu.classList.add("d-none");
      if (adminNav) adminNav.classList.add("d-none");
      if (topAuthLoggedOut) topAuthLoggedOut.classList.add("d-none");
      if (topAuthLoggedIn) topAuthLoggedIn.classList.add("d-none");
    }
  },

  bindEvents() {
    window.addEventListener("hashchange", () => this.handleHashChange());

    // Navigation links interception
    document.querySelectorAll(".nav-link[data-view], .dropdown-item[data-view]").forEach(link => {
      link.addEventListener("click", e => {
        const view = link.getAttribute("data-view");
        if (!this.currentUser && view !== "auth") {
          e.preventDefault();
          this.showToast("Institutional Access Required: Please sign in or register to access alumni directory and platform.", "warning");
          window.location.hash = "#auth";
          return;
        }
        window.location.hash = `#${view}`;
      });
    });

    // Global Search Debouncing
    const searchInput = document.getElementById("global-search-input");
    let debounceTimer;
    if (searchInput) {
      searchInput.addEventListener("input", e => {
        clearTimeout(debounceTimer);
        const query = e.target.value.trim();
        if (query.length < 2) {
          this.hideGlobalSearchResults();
          return;
        }
        debounceTimer = setTimeout(() => this.performGlobalSearch(query), 250);
      });

      // Close search box on outside click
      document.addEventListener("click", e => {
        const box = document.getElementById("global-search-results");
        if (box && !box.contains(e.target) && e.target !== searchInput) {
          this.hideGlobalSearchResults();
        }
      });
    }
  },

  handleHashChange() {
    let rawHash = window.location.hash.replace("#", "");

    // Gatekeeper: Without an account, you cannot access any information about the alumni!
    // The first page must be the login and register portal page (#auth).
    if (!this.currentUser) {
      if (rawHash !== "auth") {
        if (rawHash && rawHash !== "home") {
          this.showToast("Institutional Access Required: Please sign in or register to access alumni directory.", "warning");
        }
        window.location.hash = "#auth";
        this.activeView = "auth";
        this.showView("auth");
        return;
      }
    } else {
      // If logged in, visiting #auth or empty hash automatically opens #home
      if (!rawHash || rawHash === "auth") {
        rawHash = "home";
        window.location.hash = "#home";
      }
    }

    const parts = rawHash.split("/");
    const view = parts[0];
    const param = parts[1] || null;

    this.activeView = view;
    this.showView(view, param);
  },

  showView(viewName, param = null) {
    if (!this.currentUser && viewName !== "auth") {
      this.showToast("Please sign in or register to view alumni information.", "warning");
      viewName = "auth";
      window.location.hash = "#auth";
    }

    // Hide all view containers
    document.querySelectorAll(".view-section").forEach(sec => sec.classList.add("d-none"));

    // Update active nav link
    document.querySelectorAll(".nav-link[data-view]").forEach(l => {
      if (l.getAttribute("data-view") === viewName) {
        l.classList.add("active");
      } else {
        l.classList.remove("active");
      }
    });

    const navSignInBtn = document.getElementById("nav-signin-btn");
    if (viewName === "auth") {
      if (navSignInBtn) navSignInBtn.classList.add("nav-auth-active");
    } else {
      if (navSignInBtn) navSignInBtn.classList.remove("nav-auth-active");
    }

    const targetSec = document.getElementById(`view-${viewName}`);
    if (targetSec) {
      targetSec.classList.remove("d-none");
      window.scrollTo(0, 0);

      // Trigger view renderers
      switch (viewName) {
        case "auth":
          this.initAuthView();
          break;
        case "home":
          this.renderHome();
          break;
        case "alumni":
          if (param) {
            this.openAlumniModal(param);
          }
          this.renderAlumniDirectory();
          break;
        case "jobs":
          if (param) {
            this.openJobModal(param);
          }
          this.renderJobs();
          break;
        case "mentorship":
          this.renderMentorship();
          break;
        case "projects":
          this.renderProjects();
          break;
        case "resources":
          this.renderResources();
          break;
        case "events":
          this.renderEvents();
          break;
        case "messages":
          this.renderMessages(param);
          break;
        case "profile":
          this.renderProfile();
          break;
        case "admin":
          this.renderAdmin();
          break;
        default:
          this.renderHome();
      }
    }
  },

  // ================= NOTIFICATIONS =================

  async fetchNotifications() {
    if (!this.currentUser) return;
    try {
      const res = await API.get("/api/notifications");
      const badge = document.getElementById("notification-badge");
      const list = document.getElementById("notifications-list");

      if (badge) {
        if (res.unread_count > 0) {
          badge.innerText = res.unread_count;
          badge.classList.remove("d-none");
        } else {
          badge.classList.add("d-none");
        }
      }

      if (list) {
        if (res.items.length === 0) {
          list.innerHTML = `<div class="p-3 text-center text-muted small">No new notifications.</div>`;
          return;
        }
        list.innerHTML = res.items.map(n => `
          <div class="p-2 border-bottom ${n.is_read ? 'bg-white' : 'bg-light'}" onclick="App.markNotifRead(${n.id}, '${n.link || ''}')" style="cursor:pointer">
            <div class="d-flex justify-content-between">
              <strong class="small text-dark">${this.escape(n.title)}</strong>
              <small class="text-muted" style="font-size: 0.75rem">${this.timeAgo(n.created_at)}</small>
            </div>
            <div class="small text-muted mt-1">${this.escape(n.message)}</div>
          </div>
        `).join("");
      }
    } catch (e) {
      console.warn("Notifications error:", e);
    }
  },

  async markNotifRead(id, link) {
    try {
      await API.put(`/api/notifications/${id}/read`);
      this.fetchNotifications();
      if (link && link !== "#") {
        window.location.hash = `#${link.replace(/^\//, '')}`;
      }
    } catch (e) {}
  },

  async markAllNotifsRead() {
    try {
      await API.put("/api/notifications/read-all");
      this.fetchNotifications();
      this.showToast("All notifications marked as read.", "success");
    } catch (e) {}
  },

  // ================= GLOBAL SEARCH =================

  async performGlobalSearch(query) {
    const box = document.getElementById("global-search-results");
    if (!box) return;

    try {
      box.innerHTML = `<div class="p-3 text-center text-muted small"><span class="spinner-border spinner-border-sm me-2"></span>Searching CMS ecosystem...</div>`;
      box.classList.remove("d-none");

      const res = await API.get(`/api/search?q=${encodeURIComponent(query)}`);
      if (res.total_hits === 0) {
        box.innerHTML = `<div class="p-3 text-center text-muted small">No matches found for "<strong>${this.escape(query)}</strong>"</div>`;
        return;
      }

      let html = `<div class="p-2 bg-light border-bottom text-muted small fw-bold">SEARCH RESULTS (${res.total_hits})</div>`;

      // Alumni
      if (res.results.alumni?.length) {
        html += `<div class="px-3 pt-2 pb-1 text-uppercase text-primary fw-bold" style="font-size:0.75rem"><i class="bi bi-people me-1"></i> Alumni</div>`;
        res.results.alumni.forEach(a => {
          html += `
            <div class="search-item d-flex align-items-center justify-content-between" onclick="App.navigateToLink('${a.link}')">
              <div>
                <span class="fw-bold">${this.escape(a.title)}</span>
                ${a.verified ? '<i class="bi bi-patch-check-fill text-success ms-1" title="Verified"></i>' : ''}
                <div class="text-muted small">${this.escape(a.subtitle)}</div>
              </div>
              <span class="badge bg-primary-subtle text-primary border border-primary-subtle">Alumni</span>
            </div>`;
        });
      }

      // Jobs
      if (res.results.jobs?.length) {
        html += `<div class="px-3 pt-2 pb-1 text-uppercase text-success fw-bold" style="font-size:0.75rem"><i class="bi bi-briefcase me-1"></i> Jobs & Internships</div>`;
        res.results.jobs.forEach(j => {
          html += `
            <div class="search-item d-flex align-items-center justify-content-between" onclick="App.navigateToLink('${j.link}')">
              <div>
                <span class="fw-bold">${this.escape(j.title)}</span>
                <div class="text-muted small">${this.escape(j.subtitle)}</div>
              </div>
              <span class="badge bg-success-subtle text-success border border-success-subtle">Job</span>
            </div>`;
        });
      }

      // Projects
      if (res.results.projects?.length) {
        html += `<div class="px-3 pt-2 pb-1 text-uppercase text-warning fw-bold" style="font-size:0.75rem"><i class="bi bi-lightbulb me-1"></i> Industry Projects</div>`;
        res.results.projects.forEach(p => {
          html += `
            <div class="search-item d-flex align-items-center justify-content-between" onclick="App.navigateToLink('${p.link}')">
              <div>
                <span class="fw-bold">${this.escape(p.title)}</span>
                <div class="text-muted small">${this.escape(p.subtitle)}</div>
              </div>
              <span class="badge bg-warning-subtle text-warning border border-warning-subtle">Project</span>
            </div>`;
        });
      }

      box.innerHTML = html;
    } catch (e) {
      box.innerHTML = `<div class="p-3 text-danger small">Search query error.</div>`;
    }
  },

  hideGlobalSearchResults() {
    const box = document.getElementById("global-search-results");
    if (box) box.classList.add("d-none");
  },

  navigateToLink(link) {
    this.hideGlobalSearchResults();
    const clean = link.replace(/^\//, '');
    window.location.hash = `#${clean}`;
  },

  // ================= HOME VIEW =================

  async renderHome() {
    try {
      // 1. Featured Alumni
      const alumniRes = await API.get("/api/alumni?page_size=3");
      const featContainer = document.getElementById("home-featured-alumni");
      if (featContainer && alumniRes.items) {
        featContainer.innerHTML = alumniRes.items.map(a => `<div class="col-md-6 col-lg-4 mb-4">${this.createAlumniCard(a)}</div>`).join("");
      }

      // 2. Latest Opportunities
      const jobsRes = await API.get("/api/jobs?page_size=3");
      const jobsContainer = document.getElementById("home-latest-jobs");
      if (jobsContainer && jobsRes.items) {
        jobsContainer.innerHTML = jobsRes.items.map(j => `<div class="col-md-6 col-lg-4 mb-4">${this.createJobCard(j)}</div>`).join("");
      }

      // 3. Upcoming Events
      const eventsRes = await API.get("/api/events?page_size=2");
      const eventsContainer = document.getElementById("home-events");
      if (eventsContainer && eventsRes.length) {
        eventsContainer.innerHTML = eventsRes.slice(0, 2).map(e => this.createEventCard(e)).join("");
      }
    } catch (e) {
      console.error("Home render failed:", e);
    }
  },

  // ================= ALUMNI DIRECTORY =================

  async renderAlumniDirectory() {
    const container = document.getElementById("alumni-grid");
    if (!container) return;

    // Read current filter values
    const q = document.getElementById("filter-alumni-search")?.value || "";
    const course = document.getElementById("filter-alumni-course")?.value || "";
    const tech = document.getElementById("filter-alumni-tech")?.value || "";
    const company = document.getElementById("filter-alumni-company")?.value || "";
    const mentorship = document.getElementById("filter-alumni-mentor")?.checked ? "true" : "";
    const referral = document.getElementById("filter-alumni-referral")?.checked ? "true" : "";

    container.innerHTML = `<div class="col-12 py-5 text-center text-muted"><span class="spinner-border text-primary me-2"></span>Loading verified alumni roster...</div>`;

    try {
      let queryParams = new URLSearchParams();
      if (q) queryParams.append("q", q);
      if (course) queryParams.append("course", course);
      if (tech) queryParams.append("technology", tech);
      if (company) queryParams.append("company", company);
      if (mentorship) queryParams.append("mentorship", mentorship);
      if (referral) queryParams.append("referral", referral);

      const res = await API.get(`/api/alumni?${queryParams.toString()}`);
      const countEl = document.getElementById("alumni-count-badge");
      if (countEl) countEl.innerText = `${res.total} Alumni`;

      if (res.items.length === 0) {
        container.innerHTML = `
          <div class="col-12 py-5 text-center">
            <div class="display-6 text-muted mb-3"><i class="bi bi-search"></i></div>
            <h5 class="fw-bold">No Alumni Found</h5>
            <p class="text-muted">Try adjusting your technology or batch filters.</p>
            <button class="btn btn-outline-cms btn-sm" onclick="App.resetAlumniFilters()">Reset Filters</button>
          </div>`;
        return;
      }

      container.innerHTML = res.items.map(a => `<div class="col-md-6 col-lg-4 mb-4">${this.createAlumniCard(a)}</div>`).join("");
    } catch (e) {
      container.innerHTML = `<div class="col-12 py-4 text-center text-danger">Error loading alumni directory: ${e.message}</div>`;
    }
  },

  createAlumniCard(a) {
    const initials = a.full_name ? a.full_name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase() : "AL";
    const tagsHtml = (a.skills || []).slice(0, 4).map(s => `<span class="tech-tag">${this.escape(s)}</span>`).join("");
    
    return `
      <div class="card-modern alumni-card p-3">
        <div class="d-flex align-items-start gap-3">
          <div class="alumni-avatar">
            ${a.avatar_url ? `<img src="${a.avatar_url}" class="w-100 h-100 rounded-circle" alt="">` : initials}
          </div>
          <div class="flex-grow-1 overflow-hidden">
            <div class="d-flex align-items-center gap-1">
              <h6 class="fw-bold mb-0 text-truncate text-dark">${this.escape(a.full_name)}</h6>
              ${a.is_verified ? '<span class="verified-shield" title="Verified CMS Kanpur Alumnus"><i class="bi bi-shield-check"></i> Verified</span>' : '<span class="pending-shield"><i class="bi bi-clock"></i> Pending</span>'}
            </div>
            <div class="text-primary small fw-semibold text-truncate">${this.escape(a.current_job_title)}</div>
            <div class="text-muted small text-truncate"><i class="bi bi-building me-1"></i>${this.escape(a.current_company)}</div>
          </div>
        </div>

        <div class="mt-2 text-muted small d-flex justify-content-between">
          <span><i class="bi bi-mortarboard me-1"></i>${this.escape(a.course)} '${a.batch_year}</span>
          <span><i class="bi bi-geo-alt me-1"></i>${this.escape(a.current_city)}</span>
        </div>

        <div class="my-2" style="min-height: 48px">
          ${tagsHtml}
        </div>

        <div class="d-flex align-items-center gap-2 mb-3">
          ${a.is_referral_provider ? `
            <button type="button" class="badge-referral clickable-badge border-0" onclick="event.stopPropagation(); App.openRequestReferralModal(${a.user_id || a.id}, '${this.escape(a.current_company || '')}', '${this.escape(a.current_job_title || '')}')" title="Click to request internal job referral from ${this.escape(a.full_name)}">
              <i class="bi bi-send-check me-1"></i>Referral Ready
            </button>` : ''}
          ${a.is_mentor ? `
            <button type="button" class="badge-mentor clickable-badge border-0" onclick="event.stopPropagation(); App.openRequestMentorshipModal(${a.user_id || a.id}, '${this.escape(a.full_name)}')" title="Click to request 1-on-1 mentorship with ${this.escape(a.full_name)}">
              <i class="bi bi-person-video3 me-1"></i>Mentor
            </button>` : ''}
        </div>

        <div class="mt-auto pt-2 border-top d-flex align-items-center justify-content-between">
          <div class="d-flex gap-1">
            ${a.linkedin_url ? `<a href="${a.linkedin_url}" target="_blank" class="dev-link text-primary" title="LinkedIn"><i class="bi bi-linkedin"></i></a>` : ''}
            ${a.github_url ? `<a href="${a.github_url}" target="_blank" class="dev-link text-dark" title="GitHub"><i class="bi bi-github"></i></a>` : ''}
            ${a.leetcode_url ? `<a href="${a.leetcode_url}" target="_blank" class="dev-link text-warning" title="LeetCode"><i class="bi bi-code-slash"></i></a>` : ''}
          </div>
          <button class="btn btn-sm btn-outline-cms" onclick="App.openAlumniModal(${a.id})">
            View Profile <i class="bi bi-arrow-right ms-1"></i>
          </button>
        </div>
      </div>
    `;
  },

  resetAlumniFilters() {
    const s = document.getElementById("filter-alumni-search");
    const c = document.getElementById("filter-alumni-course");
    const t = document.getElementById("filter-alumni-tech");
    const m = document.getElementById("filter-alumni-mentor");
    const r = document.getElementById("filter-alumni-referral");
    if (s) s.value = "";
    if (c) c.value = "";
    if (t) t.value = "";
    if (m) m.checked = false;
    if (r) r.checked = false;
    this.renderAlumniDirectory();
  },

  async openAlumniModal(id) {
    this.activeAlumniId = id;
    const modalEl = document.getElementById("modal-alumni-detail");
    if (!modalEl) return;
    const modal = new bootstrap.Modal(modalEl);
    modal.show();

    const body = document.getElementById("alumni-modal-body");
    body.innerHTML = `<div class="p-5 text-center text-muted"><span class="spinner-border text-primary me-2"></span>Loading professional profile...</div>`;

    try {
      const a = await API.get(`/api/alumni/${id}`);
      const initials = a.full_name ? a.full_name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase() : "AL";

      body.innerHTML = `
        <div class="row">
          <div class="col-md-4 text-center border-end pe-md-4">
            <div class="mx-auto mb-3" style="width: 96px; height: 96px; border-radius: 50%; background: #EEF2FF; color: #4F46E5; display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: 800; border: 3px solid #C7D2FE;">
              ${a.avatar_url ? `<img src="${a.avatar_url}" class="w-100 h-100 rounded-circle" alt="">` : initials}
            </div>
            <h5 class="fw-bold mb-1">${this.escape(a.full_name)}</h5>
            <div class="text-primary fw-semibold small mb-2">${this.escape(a.current_job_title)}</div>
            <div class="text-muted small mb-3"><i class="bi bi-building me-1"></i>${this.escape(a.current_company)}</div>

            ${a.is_verified ? '<span class="verified-shield mb-3"><i class="bi bi-patch-check-fill"></i> Verified CMS Alumnus</span>' : '<span class="pending-shield mb-3">Pending Verification</span>'}

            <div class="p-3 bg-light rounded text-start small mb-3">
              <div><strong>Degree:</strong> ${this.escape(a.course)} (${a.batch_year} - ${a.graduation_year})</div>
              <div class="mt-1"><strong>Location:</strong> ${this.escape(a.current_city)}, ${this.escape(a.country)}</div>
              <div class="mt-1"><strong>Experience:</strong> ${a.years_of_experience} Years</div>
              ${a.email ? `<div class="mt-1"><strong>Email:</strong> ${this.escape(a.email)}</div>` : ''}
              ${a.phone ? `<div class="mt-1"><strong>Phone:</strong> ${this.escape(a.phone)}</div>` : ''}
            </div>

            <!-- Action buttons -->
            <div class="d-grid gap-2">
              ${a.is_referral_provider ? `
                <button class="btn btn-primary-cms btn-sm" onclick="App.openRequestReferralModal(${a.user_id}, '${this.escape(a.current_company)}', '${this.escape(a.full_name)}')">
                  <i class="bi bi-send-check me-1"></i> Request Referral
                </button>` : ''}
              ${a.is_mentor ? `
                <button class="btn btn-outline-cms btn-sm" onclick="App.openRequestMentorshipModal(${a.user_id}, '${this.escape(a.full_name)}')">
                  <i class="bi bi-person-video3 me-1"></i> Request Mentorship
                </button>` : ''}
              <button class="btn btn-light btn-sm text-secondary" onclick="App.startDirectMessage(${a.user_id}, '${this.escape(a.full_name)}')">
                <i class="bi bi-chat-dots me-1"></i> Send Message
              </button>
            </div>
          </div>

          <div class="col-md-8 ps-md-4">
            <h6 class="fw-bold text-dark border-bottom pb-2 mb-3">About & Background</h6>
            <p class="text-muted small">${this.escape(a.bio || "No summary provided.")}</p>

            <h6 class="fw-bold text-dark border-bottom pb-2 mb-3 mt-4">Technical Skills</h6>
            <div class="mb-4">
              ${(a.skills || []).map(s => `<span class="tech-tag primary">${this.escape(s)}</span>`).join("")}
            </div>

            <!-- Developer Profiles & Dynamic Links -->
            <h6 class="fw-bold text-dark border-bottom pb-2 mb-3">Professional & Developer Profiles</h6>
            <div class="d-flex flex-wrap gap-2 mb-4">
              ${(() => {
                let modalLinks = [];
                if (a.custom_links) {
                  try { modalLinks = JSON.parse(a.custom_links); } catch (_) {}
                }
                if (!modalLinks.length) {
                  if (a.github_url) modalLinks.push({ platform: "GitHub", url: a.github_url });
                  if (a.linkedin_url) modalLinks.push({ platform: "LinkedIn", url: a.linkedin_url });
                  if (a.leetcode_url) modalLinks.push({ platform: "LeetCode", url: a.leetcode_url });
                  if (a.portfolio_url) modalLinks.push({ platform: "Portfolio", url: a.portfolio_url });
                }

                if (!modalLinks.length) return '<div class="text-muted small">No external links provided.</div>';

                return modalLinks.map(link => {
                  const info = this.getPlatformInfo(link.platform, link.url);
                  return `
                    <a href="${this.escape(link.url)}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline-secondary d-inline-flex align-items-center gap-2 shadow-sm" style="border-radius: 8px;">
                      <span style="display: flex; align-items: center;">${info.icon}</span>
                      <span class="fw-bold text-dark">${this.escape(link.platform || info.name)}</span>
                      <i class="bi bi-box-arrow-up-right small text-muted" style="font-size: 0.72rem;"></i>
                    </a>
                  `;
                }).join("");
              })()}
            </div>

            <!-- Showcase Projects -->
            <h6 class="fw-bold text-dark border-bottom pb-2 mb-3">Showcase Projects</h6>
            <div class="mb-4">
              ${a.projects?.length ? a.projects.map(p => `
                <div class="p-3 bg-light rounded mb-2 border">
                  <div class="d-flex justify-content-between align-items-start">
                    <strong class="text-dark">${this.escape(p.title)}</strong>
                    ${p.github_url ? `<a href="${p.github_url}" target="_blank" class="btn btn-xs btn-outline-dark small"><i class="bi bi-github"></i> Code</a>` : ''}
                  </div>
                  <div class="text-muted small mt-1">${this.escape(p.description || '')}</div>
                  <div class="mt-2 text-primary font-monospace small"><i class="bi bi-stack me-1"></i>${this.escape(p.technologies)}</div>
                </div>
              `).join("") : '<div class="text-muted small">No showcased projects added yet.</div>'}
            </div>

            <!-- LinkedIn-style Career History Timeline -->
            <h6 class="fw-bold text-dark border-bottom pb-2 mb-3">Career & Work Experience</h6>
            <div class="d-flex flex-column gap-2">
              ${a.experiences?.length ? a.experiences.map(e => {
                const compLogoUrl = `https://www.google.com/s2/favicons?domain=${encodeURIComponent(e.company.toLowerCase().replace(/\s+/g, '') + '.com')}&sz=64`;
                return `
                  <div class="exp-linkedin-card d-flex gap-3 align-items-start p-3 rounded border">
                    <div class="company-logo-badge">
                      <img src="${compLogoUrl}" alt="" onerror="this.onerror=null; this.parentElement.innerText='${this.escape(e.company.charAt(0).toUpperCase())}';">
                    </div>
                    <div class="flex-grow-1">
                      <div class="fw-bold text-dark">${this.escape(e.job_title)} • <span class="text-primary">${this.escape(e.company)}</span></div>
                      <div class="text-muted small mt-1">
                        <i class="bi bi-calendar3 me-1"></i> ${this.escape(e.start_date)} - ${e.is_current ? '<span class="badge bg-success-subtle text-success">Present</span>' : this.escape(e.end_date || 'Present')}
                        ${e.location ? ` • <i class="bi bi-geo-alt me-1"></i> ${this.escape(e.location)}` : ''}
                      </div>
                      ${e.description ? `<p class="text-secondary small mt-2 mb-0" style="white-space: pre-line;">${this.escape(e.description)}</p>` : ''}
                    </div>
                  </div>
                `;
              }).join("") : '<div class="text-muted small">No career entries recorded.</div>'}
            </div>
          </div>
        </div>
      `;
    } catch (err) {
      body.innerHTML = `<div class="p-4 text-danger text-center">Failed to load profile details: ${err.message}</div>`;
    }
  },

  // ================= JOBS & REFERRALS =================

  async renderJobs() {
    const container = document.getElementById("jobs-grid");
    if (!container) return;

    container.innerHTML = `<div class="col-12 py-5 text-center text-muted"><span class="spinner-border text-primary me-2"></span>Loading placement & referral opportunities...</div>`;

    const jobType = document.getElementById("filter-job-type")?.value || "";
    const referralOnly = document.getElementById("filter-job-referral")?.checked ? "true" : "";
    const search = document.getElementById("filter-job-search")?.value || "";

    try {
      let queryParams = new URLSearchParams();
      if (jobType) queryParams.append("job_type", jobType);
      if (referralOnly) queryParams.append("referral_only", referralOnly);
      if (search) queryParams.append("q", search);

      const res = await API.get(`/api/jobs?${queryParams.toString()}`);
      if (res.items.length === 0) {
        container.innerHTML = `<div class="col-12 py-5 text-center text-muted"><h5>No opportunities match your filter.</h5></div>`;
        return;
      }

      container.innerHTML = res.items.map(j => `<div class="col-md-6 col-lg-4 mb-4">${this.createJobCard(j)}</div>`).join("");
    } catch (e) {
      container.innerHTML = `<div class="col-12 py-4 text-center text-danger">Error loading jobs: ${e.message}</div>`;
    }
  },

  createJobCard(j) {
    const isIntern = j.job_type === "internship";
    const typeBadge = isIntern ? '<span class="badge bg-warning text-dark"><i class="bi bi-clock-history me-1"></i>Internship</span>' :
                                '<span class="badge bg-primary"><i class="bi bi-briefcase me-1"></i>Full-time</span>';

    return `
      <div class="card-modern job-card clickable-job-card p-3 h-100 d-flex flex-column" onclick="App.openJobModal(${j.id})" title="Click to view full job description & requirements">
        <!-- Badges & Bookmark Row -->
        <div class="d-flex justify-content-between align-items-center mb-2">
          <div class="d-flex align-items-center gap-1 flex-wrap">
            ${typeBadge}
            ${j.is_referral_available ? '<span class="badge-referral"><i class="bi bi-send-check me-1"></i>Referral Available</span>' : ''}
          </div>
          <button class="btn btn-sm btn-link p-0 text-muted" onclick="event.stopPropagation(); App.toggleSaveJob(${j.id})" title="${j.is_saved ? 'Remove Bookmark' : 'Bookmark Job'}">
            <i class="bi ${j.is_saved ? 'bi-bookmark-fill text-primary' : 'bi-bookmark'}"></i>
          </button>
        </div>

        <!-- Job Title -->
        <h6 class="fw-bold mb-1 text-dark job-card-title" style="font-size: 1.02rem; line-height: 1.35;">${this.escape(j.title)}</h6>

        <!-- Company Info -->
        <div class="text-primary small fw-semibold mb-2 d-flex align-items-center gap-1">
          <i class="bi bi-building"></i>
          <span class="text-truncate">${this.escape(j.company)}</span>
        </div>

        <!-- Location & Salary Details -->
        <div class="text-muted small mb-2 d-flex flex-wrap align-items-center" style="gap: 0.65rem;">
          <span><i class="bi bi-geo-alt me-1 text-secondary"></i>${this.escape(j.location || 'Remote')} <span class="badge bg-light text-dark border ms-1 py-0 px-1" style="font-size: 0.7rem;">${this.escape(j.location_type || 'Full-time')}</span></span>
          ${j.salary_range ? `<span><i class="bi bi-cash-stack me-1 text-success"></i>${this.escape(j.salary_range)}</span>` : ''}
        </div>

        <!-- Skills Tags -->
        <div class="mb-2 d-flex flex-wrap gap-1" style="min-height: 28px;">
          ${(j.required_skills || []).slice(0, 3).map(s => `<span class="tech-tag">${this.escape(s)}</span>`).join("")}
        </div>

        <!-- Job Description -->
        <p class="text-muted small mb-3 flex-grow-1" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.45; min-height: 2.9em;">
          ${this.escape(j.description || '')}
        </p>

        <!-- Card Footer -->
        <div class="mt-auto pt-2 border-top d-flex justify-content-between align-items-center">
          <small class="text-muted text-truncate me-2" style="font-size: 0.75rem; max-width: 44%;">
            Posted by <strong>${this.escape(j.poster_name || 'Alumnus')}</strong>
          </small>
          <div class="d-flex gap-1 flex-shrink-0 align-items-center">
            <button class="btn btn-xs btn-outline-secondary" onclick="event.stopPropagation(); App.openJobModal(${j.id})">
              Details
            </button>
            ${j.is_referral_available ? `
              <button class="btn btn-xs btn-outline-primary" onclick="event.stopPropagation(); App.openRequestReferralModal(${j.poster_id}, '${this.escape(j.company)}', '${this.escape(j.title)}', ${j.id})">
                <i class="bi bi-send-check me-1"></i>Referral
              </button>` : ''}
            <button class="btn btn-xs btn-primary-cms" onclick="event.stopPropagation(); App.openApplyJobModal(${j.id}, '${this.escape(j.title)}', '${this.escape(j.company)}')">
              Apply
            </button>
          </div>
        </div>
      </div>
    `;
  },

  async openJobModal(id) {
    const modalEl = document.getElementById("modal-job-detail");
    if (!modalEl) return;
    const modal = new bootstrap.Modal(modalEl);
    modal.show();

    const body = document.getElementById("job-modal-body");
    body.innerHTML = `
      <div class="py-5 text-center text-muted">
        <span class="spinner-border text-primary me-2"></span>Loading job description & requirements...
      </div>`;

    try {
      const j = await API.get(`/api/jobs/${id}`);
      const isIntern = j.job_type === "internship";
      const typeBadge = isIntern
        ? '<span class="badge bg-warning text-dark"><i class="bi bi-clock-history me-1"></i>Internship</span>'
        : '<span class="badge bg-primary"><i class="bi bi-briefcase me-1"></i>Full-time</span>';

      const skillsHtml = (j.required_skills && j.required_skills.length)
        ? j.required_skills.map(s => `
            <span class="badge bg-primary-subtle text-primary border border-primary-subtle px-3 py-2 rounded-pill fw-semibold" style="font-size: 0.85rem;">
              <i class="bi bi-check2-circle me-1"></i>${this.escape(s)}
            </span>
          `).join(" ")
        : '<span class="text-muted small">No specific technical skills listed.</span>';

      const postDate = j.created_at ? new Date(j.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '';

      body.innerHTML = `
        <div>
          <!-- Header Area -->
          <div class="d-flex align-items-start gap-3 mb-3">
            <div class="rounded-3 bg-light text-primary d-flex align-items-center justify-content-center border flex-shrink-0" style="width: 58px; height: 58px; font-size: 1.7rem;">
              <i class="bi bi-building"></i>
            </div>
            <div class="flex-grow-1">
              <div class="d-flex align-items-center gap-2 flex-wrap mb-1">
                ${typeBadge}
                <span class="badge bg-light text-secondary border text-uppercase" style="font-size: 0.72rem;">${this.escape(j.location_type || 'Full-time')}</span>
                ${j.is_referral_available ? '<span class="badge-referral"><i class="bi bi-send-check me-1"></i>Referral Available</span>' : ''}
              </div>
              <h4 class="fw-bold text-dark mb-1">${this.escape(j.title)}</h4>
              <div class="text-primary fw-semibold fs-6">
                <i class="bi bi-building me-1"></i>${this.escape(j.company)}
              </div>
            </div>
          </div>

          <!-- Key Highlights Grid -->
          <div class="row g-2 mb-4">
            <div class="col-sm-6 col-md-3">
              <div class="job-modal-stat-card h-100">
                <div class="text-muted small fw-semibold mb-1"><i class="bi bi-geo-alt-fill text-danger me-1"></i>Location</div>
                <div class="fw-bold text-dark small text-truncate" title="${this.escape(j.location || 'Remote')}">${this.escape(j.location || 'Remote')}</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="job-modal-stat-card h-100">
                <div class="text-muted small fw-semibold mb-1"><i class="bi bi-cash-stack text-success me-1"></i>Compensation</div>
                <div class="fw-bold text-dark small text-truncate" title="${this.escape(j.salary_range || 'Competitive')}">${this.escape(j.salary_range || 'Competitive')}</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="job-modal-stat-card h-100">
                <div class="text-muted small fw-semibold mb-1"><i class="bi bi-person-workspace text-warning me-1"></i>Experience</div>
                <div class="fw-bold text-dark small text-truncate" title="${this.escape(j.experience_required || 'Open to all')}">${this.escape(j.experience_required || 'Fresher / All')}</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="job-modal-stat-card h-100">
                <div class="text-muted small fw-semibold mb-1"><i class="bi bi-person-check-fill text-primary me-1"></i>Posted By</div>
                <div class="fw-bold text-dark small text-truncate" title="${this.escape(j.poster_name || 'CMS Alumnus')}">${this.escape(j.poster_name || 'CMS Alumnus')}</div>
                ${postDate ? `<div class="text-muted" style="font-size: 0.7rem;">${postDate}</div>` : ''}
              </div>
            </div>
          </div>

          <!-- Skills & Requirements Section -->
          <div class="mb-4">
            <h6 class="fw-bold text-dark border-bottom pb-2 mb-3">
              <i class="bi bi-code-slash text-primary me-2"></i>Job Requirements & Technical Skills
            </h6>
            <div class="d-flex flex-wrap gap-2 mb-3">
              ${skillsHtml}
            </div>
            ${j.experience_required ? `
              <div class="p-3 bg-light rounded-3 border small">
                <strong class="text-dark"><i class="bi bi-award me-1 text-primary"></i>Experience Level & Eligibility:</strong>
                <span class="text-secondary ms-1">${this.escape(j.experience_required)}</span>
              </div>
            ` : ''}
          </div>

          <!-- Detailed Job Description Section -->
          <div class="mb-4">
            <h6 class="fw-bold text-dark border-bottom pb-2 mb-3">
              <i class="bi bi-file-earmark-text text-primary me-2"></i>Detailed Job Description & Responsibilities
            </h6>
            <div class="p-3 bg-light rounded-3 text-secondary small" style="white-space: pre-line; line-height: 1.7; font-size: 0.95rem;">
              ${this.escape(j.description || 'No detailed description provided.')}
            </div>
          </div>

          <!-- Referral Program Banner (if available) -->
          ${j.is_referral_available ? `
            <div class="card p-3 mb-4 border-0" style="background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%); border-left: 4px solid #7C3AED !important; border-radius: 12px;">
              <div class="d-flex align-items-center justify-content-between flex-wrap gap-2">
                <div>
                  <h6 class="fw-bold mb-1" style="color: #6D28D9;"><i class="bi bi-lightning-charge-fill me-1"></i> Fast-Track Alumni Referral</h6>
                  <p class="text-muted small mb-0">Alumnus <strong>${this.escape(j.poster_name)}</strong> is offering internal employee referral support for CMS students & graduates at <strong>${this.escape(j.company)}</strong>.</p>
                </div>
                <button class="btn btn-sm btn-primary-cms flex-shrink-0" onclick="bootstrap.Modal.getInstance(document.getElementById('modal-job-detail')).hide(); App.openRequestReferralModal(${j.poster_id}, '${this.escape(j.company)}', '${this.escape(j.title)}', ${j.id})">
                  <i class="bi bi-send-check me-1"></i>Request Referral
                </button>
              </div>
            </div>
          ` : ''}

          <!-- Modal Actions Footer -->
          <div class="pt-3 border-top d-flex justify-content-between align-items-center flex-wrap gap-2">
            <button class="btn btn-outline-secondary btn-sm" onclick="App.toggleSaveJob(${j.id})">
              <i class="bi ${j.is_saved ? 'bi-bookmark-fill text-primary' : 'bi-bookmark'} me-1"></i>
              ${j.is_saved ? 'Saved in Bookmarks' : 'Save Job'}
            </button>
            <div class="d-flex gap-2">
              ${j.external_apply_url ? `
                <a href="${j.external_apply_url}" target="_blank" class="btn btn-outline-primary btn-sm">
                  <i class="bi bi-box-arrow-up-right me-1"></i>Company Careers Site
                </a>
              ` : ''}
              ${j.is_referral_available ? `
                <button class="btn btn-outline-primary btn-sm" onclick="bootstrap.Modal.getInstance(document.getElementById('modal-job-detail')).hide(); App.openRequestReferralModal(${j.poster_id}, '${this.escape(j.company)}', '${this.escape(j.title)}', ${j.id})">
                  <i class="bi bi-send-check me-1"></i>Request Referral
                </button>
              ` : ''}
              <button class="btn btn-primary-cms btn-sm px-3" onclick="bootstrap.Modal.getInstance(document.getElementById('modal-job-detail')).hide(); App.openApplyJobModal(${j.id}, '${this.escape(j.title)}', '${this.escape(j.company)}')">
                <i class="bi bi-send me-1"></i>Apply for this Role
              </button>
            </div>
          </div>
        </div>
      `;
    } catch (e) {
      body.innerHTML = `
        <div class="py-5 text-center text-danger">
          <i class="bi bi-exclamation-triangle fs-1 d-block mb-2"></i>
          <h5>Error Loading Opportunity</h5>
          <p class="text-muted small">${this.escape(e.message)}</p>
        </div>
      `;
    }
  },

  async toggleSaveJob(id) {
    if (!this.requireLogin()) return;
    try {
      const res = await API.post(`/api/jobs/${id}/save`);
      this.showToast(res.message, "success");
      this.renderJobs();
    } catch (e) {
      this.showToast(e.message, "danger");
    }
  },

  openApplyJobModal(id, title, company) {
    if (!this.requireLogin()) return;
    document.getElementById("apply-job-id").value = id;
    document.getElementById("apply-job-title").innerText = `${title} at ${company}`;
    new bootstrap.Modal(document.getElementById("modal-apply-job")).show();
  },

  async submitJobApplication() {
    const id = document.getElementById("apply-job-id").value;
    const resume = document.getElementById("apply-job-resume").value;
    const note = document.getElementById("apply-job-note").value;

    try {
      const res = await API.post(`/api/jobs/${id}/apply`, {
        resume_url: resume || null,
        cover_note: note
      });
      bootstrap.Modal.getInstance(document.getElementById("modal-apply-job")).hide();
      this.showToast(res.message, "success");
    } catch (e) {
      this.showToast(e.message, "danger");
    }
  },

  openRequestReferralModal(alumniId, company, role, jobId = null) {
    if (!this.requireLogin()) return;
    document.getElementById("referral-alumni-id").value = alumniId;
    document.getElementById("referral-job-id").value = jobId || "";
    document.getElementById("referral-target-company").value = company || "";
    document.getElementById("referral-target-role").value = role || "";
    new bootstrap.Modal(document.getElementById("modal-request-referral")).show();
  },

  async submitReferralRequest() {
    const alumniId = document.getElementById("referral-alumni-id").value;
    const jobId = document.getElementById("referral-job-id").value || null;
    const company = document.getElementById("referral-target-company").value;
    const role = document.getElementById("referral-target-role").value;
    const resume = document.getElementById("referral-resume-link").value;
    const note = document.getElementById("referral-note").value;

    try {
      const res = await API.post("/api/referrals/request", {
        alumni_id: parseInt(alumniId),
        job_id: jobId ? parseInt(jobId) : null,
        target_company: company,
        target_role: role,
        resume_url: resume || null,
        note: note
      });
      bootstrap.Modal.getInstance(document.getElementById("modal-request-referral")).hide();
      this.showToast(res.message, "success");
    } catch (e) {
      this.showToast(e.message, "danger");
    }
  },

  // ================= MENTORSHIP & SESSIONS =================

  async renderMentorship() {
    const mentorsContainer = document.getElementById("mentors-list");
    if (!mentorsContainer) return;

    mentorsContainer.innerHTML = `<div class="col-12 py-5 text-center text-muted"><span class="spinner-border text-primary me-2"></span>Loading verified alumni mentors...</div>`;

    try {
      const mentors = await API.get("/api/mentorship/mentors");
      if (mentors.length === 0) {
        mentorsContainer.innerHTML = `<div class="col-12 py-4 text-center text-muted">No active mentors found.</div>`;
        return;
      }

      mentorsContainer.innerHTML = mentors.map(m => `
        <div class="col-md-6 col-lg-4 mb-4">
          <div class="card-modern p-3 h-100 d-flex flex-column">
            <div class="d-flex align-items-center gap-3 mb-3">
              <div class="alumni-avatar">
                ${m.avatar_url ? `<img src="${m.avatar_url}" class="w-100 h-100 rounded-circle" alt="">` : m.full_name.charAt(0)}
              </div>
              <div>
                <h6 class="fw-bold mb-0 text-dark">${this.escape(m.full_name)}</h6>
                <div class="text-primary small fw-semibold">${this.escape(m.job_title)}</div>
                <div class="text-muted small"><i class="bi bi-building me-1"></i>${this.escape(m.company)}</div>
              </div>
            </div>

            <div class="mb-2">
              <span class="text-muted small fw-bold">Mentorship Topics:</span>
              <div class="mt-1">
                ${m.topics.map(t => `<span class="tech-tag primary">${this.escape(t)}</span>`).join("")}
              </div>
            </div>

            <div class="p-2 bg-light rounded text-muted small mb-3" style="font-size: 0.8rem">
              <div><i class="bi bi-camera-video me-1 text-primary"></i> ${this.escape(m.meeting_format)}</div>
              <div class="mt-1"><i class="bi bi-clock me-1 text-primary"></i> ${this.escape(m.availability_details)}</div>
            </div>

            <div class="mt-auto d-flex gap-2">
              <button class="btn btn-sm btn-primary-cms flex-grow-1" onclick="App.openRequestMentorshipModal(${m.alumni_id}, '${this.escape(m.full_name)}')">
                <i class="bi bi-send me-1"></i> Request Mentorship
              </button>
              <button class="btn btn-sm btn-outline-cms" onclick="App.openMockInterviewModal(${m.alumni_id}, '${this.escape(m.full_name)}')">
                Mock Interview
              </button>
            </div>
          </div>
        </div>
      `).join("");
    } catch (e) {
      mentorsContainer.innerHTML = `<div class="col-12 py-4 text-center text-danger">Error: ${e.message}</div>`;
    }
  },

  openRequestMentorshipModal(mentorId, mentorName) {
    if (!this.requireLogin()) return;
    document.getElementById("mentorship-mentor-id").value = mentorId;
    document.getElementById("mentorship-mentor-name").innerText = mentorName;
    new bootstrap.Modal(document.getElementById("modal-request-mentorship")).show();
  },

  async submitMentorshipRequest() {
    const mentorId = document.getElementById("mentorship-mentor-id").value;
    const topic = document.getElementById("mentorship-topic").value;
    const message = document.getElementById("mentorship-message").value;

    try {
      const res = await API.post("/api/mentorship/requests", {
        mentor_id: parseInt(mentorId),
        topic,
        message
      });
      bootstrap.Modal.getInstance(document.getElementById("modal-request-mentorship")).hide();
      this.showToast(res.message, "success");
    } catch (e) {
      this.showToast(e.message, "danger");
    }
  },

  openMockInterviewModal(interviewerId, interviewerName) {
    if (!this.requireLogin()) return;
    document.getElementById("mock-interviewer-id").value = interviewerId;
    document.getElementById("mock-interviewer-name").innerText = interviewerName;
    new bootstrap.Modal(document.getElementById("modal-mock-interview")).show();
  },

  async submitMockInterview() {
    const id = document.getElementById("mock-interviewer-id").value;
    const type = document.getElementById("mock-interview-type").value;

    try {
      const res = await API.post("/api/mentorship/mock-interviews", {
        interviewer_id: parseInt(id),
        interview_type: type
      });
      bootstrap.Modal.getInstance(document.getElementById("modal-mock-interview")).hide();
      this.showToast(res.message, "success");
    } catch (e) {
      this.showToast(e.message, "danger");
    }
  },

  // ================= INDUSTRY PROJECTS & PROBLEM STATEMENTS =================

  async renderProjects() {
    const container = document.getElementById("projects-grid");
    if (!container) return;

    container.innerHTML = `<div class="col-12 py-5 text-center text-muted"><span class="spinner-border text-primary me-2"></span>Loading industry problems...</div>`;

    try {
      const projects = await API.get("/api/projects");
      if (projects.length === 0) {
        container.innerHTML = `<div class="col-12 py-4 text-center text-muted">No industry problem statements available.</div>`;
        return;
      }

      container.innerHTML = projects.map(p => `
        <div class="col-md-6 mb-4">
          <div class="card-modern p-4 h-100 d-flex flex-column">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <span class="badge bg-primary-subtle text-primary border border-primary-subtle">${this.escape(p.domain)}</span>
              <span class="badge bg-${p.difficulty === 'advanced' ? 'danger' : p.difficulty === 'intermediate' ? 'warning' : 'success'}-subtle text-${p.difficulty === 'advanced' ? 'danger' : p.difficulty === 'intermediate' ? 'warning' : 'success'} border">
                ${p.difficulty.toUpperCase()}
              </span>
            </div>

            <h5 class="fw-bold text-dark mb-2">${this.escape(p.title)}</h5>
            <div class="text-muted small mb-3"><i class="bi bi-person-workspace me-1"></i>Curated by <strong>${this.escape(p.creator_name)}</strong> (${this.escape(p.creator_company || 'Industry Leader')})</div>

            <p class="text-muted small mb-3">${this.escape(p.description)}</p>

            <div class="mb-3">
              <span class="text-muted small fw-bold d-block mb-1">Required Tech Stack:</span>
              ${p.required_technologies.map(t => `<span class="tech-tag primary">${this.escape(t)}</span>`).join("")}
            </div>

            <div class="p-2 bg-light rounded text-muted small mb-3 d-flex justify-content-between">
              <span><i class="bi bi-clock me-1"></i>Duration: ${p.duration_weeks} Weeks</span>
              <span><i class="bi bi-people me-1"></i>Team Size: Max ${p.max_students}</span>
              <span><i class="bi bi-file-earmark-code me-1"></i>${p.proposals_count} Proposals</span>
            </div>

            <div class="mt-auto d-flex justify-content-end">
              <button class="btn btn-primary-cms btn-sm" onclick="App.openSubmitProposalModal(${p.id}, '${this.escape(p.title)}')">
                <i class="bi bi-file-earmark-plus me-1"></i> Submit Solution Proposal
              </button>
            </div>
          </div>
        </div>
      `).join("");
    } catch (e) {
      container.innerHTML = `<div class="col-12 py-4 text-center text-danger">Error: ${e.message}</div>`;
    }
  },

  openSubmitProposalModal(id, title) {
    if (!this.requireLogin()) return;
    document.getElementById("proposal-project-id").value = id;
    document.getElementById("proposal-project-title").innerText = title;
    new bootstrap.Modal(document.getElementById("modal-submit-proposal")).show();
  },

  async submitProjectProposal() {
    const id = document.getElementById("proposal-project-id").value;
    const team = document.getElementById("proposal-team-members").value;
    const text = document.getElementById("proposal-text").value;

    try {
      const res = await API.post(`/api/projects/${id}/proposals`, {
        team_members: team,
        proposal_text: text
      });
      bootstrap.Modal.getInstance(document.getElementById("modal-submit-proposal")).hide();
      this.showToast(res.message, "success");
      this.renderProjects();
    } catch (e) {
      this.showToast(e.message, "danger");
    }
  },

  // ================= TECHNICAL RESOURCES =================

  async renderResources() {
    const container = document.getElementById("resources-grid");
    const catsContainer = document.getElementById("resource-categories-list");
    if (!container) return;

    try {
      // 1. Categories
      if (catsContainer) {
        const cats = await API.get("/api/resources/categories");
        catsContainer.innerHTML = `
          <button class="btn btn-sm btn-outline-cms active" onclick="App.filterResourceCategory(null, this)">All Categories</button>
          ${cats.map(c => `
            <button class="btn btn-sm btn-outline-cms" onclick="App.filterResourceCategory(${c.id}, this)">
              ${this.escape(c.name)} <span class="badge bg-secondary-subtle text-secondary ms-1">${c.count}</span>
            </button>
          `).join("")}
        `;
      }

      // 2. Resources
      const resList = await API.get("/api/resources");
      this.renderResourceCards(resList);
    } catch (e) {
      container.innerHTML = `<div class="col-12 py-4 text-danger text-center">Error loading resources: ${e.message}</div>`;
    }
  },

  async filterResourceCategory(catId, btnEl) {
    if (btnEl) {
      btnEl.parentElement.querySelectorAll("button").forEach(b => b.classList.remove("active", "btn-primary-cms"));
      btnEl.classList.add("active", "btn-primary-cms");
    }

    const url = catId ? `/api/resources?category_id=${catId}` : "/api/resources";
    try {
      const resList = await API.get(url);
      this.renderResourceCards(resList);
    } catch (e) {}
  },

  renderResourceCards(items) {
    const container = document.getElementById("resources-grid");
    if (!container) return;

    if (items.length === 0) {
      container.innerHTML = `<div class="col-12 py-4 text-center text-muted">No resources found in this category.</div>`;
      return;
    }

    container.innerHTML = items.map(r => `
      <div class="col-md-6 col-lg-4 mb-4">
        <div class="card-modern p-3 h-100 d-flex flex-column">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <span class="badge bg-primary-subtle text-primary border">${this.escape(r.category_name)}</span>
            <span class="badge bg-light text-muted border">${r.resource_type}</span>
          </div>

          <h6 class="fw-bold text-dark mb-1">${this.escape(r.title)}</h6>
          <p class="text-muted small mb-3">${this.escape(r.description || '')}</p>

          <div class="mb-3">
            ${r.tags.map(t => `<span class="tech-tag">${this.escape(t)}</span>`).join("")}
          </div>

          <div class="mt-auto pt-2 border-top d-flex justify-content-between align-items-center">
            <span class="text-muted small"><i class="bi bi-download me-1"></i>${r.downloads_count} downloads</span>
            <a href="${r.external_link || r.file_url || '#'}" target="_blank" class="btn btn-sm btn-outline-cms" onclick="App.trackDownload(${r.id})">
              <i class="bi bi-box-arrow-up-right me-1"></i> Access
            </a>
          </div>
        </div>
      </div>
    `).join("");
  },

  async trackDownload(id) {
    try {
      await API.post(`/api/resources/${id}/download`);
    } catch (e) {}
  },

  // ================= EVENTS & HACKATHONS =================

  async renderEvents() {
    const container = document.getElementById("events-grid");
    if (!container) return;

    container.innerHTML = `<div class="col-12 py-5 text-center text-muted"><span class="spinner-border text-primary me-2"></span>Loading CMS tech events & hackathons...</div>`;

    try {
      const events = await API.get("/api/events");
      if (events.length === 0) {
        container.innerHTML = `<div class="col-12 py-4 text-center text-muted">No upcoming events scheduled right now.</div>`;
        return;
      }

      container.innerHTML = events.map(e => `<div class="col-md-6 mb-4">${this.createEventCard(e)}</div>`).join("");
    } catch (e) {
      container.innerHTML = `<div class="col-12 py-4 text-center text-danger">Error: ${e.message}</div>`;
    }
  },

  createEventCard(e) {
    const isHackathon = e.event_type === "hackathon";
    const startDate = new Date(e.start_time).toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });

    return `
      <div class="card-modern p-4 h-100 d-flex flex-column">
        <div class="d-flex justify-content-between align-items-start mb-2">
          <span class="badge ${isHackathon ? 'bg-danger' : 'bg-primary'} text-uppercase">
            <i class="bi ${isHackathon ? 'bi-trophy-fill' : 'bi-camera-video-fill'} me-1"></i>${e.event_type.replace('_', ' ')}
          </span>
          <span class="text-muted small"><i class="bi bi-people me-1"></i>${e.registrations_count} / ${e.capacity} Registered</span>
        </div>

        <h5 class="fw-bold text-dark mb-2">${this.escape(e.title)}</h5>
        <div class="text-primary small mb-3"><i class="bi bi-calendar-event me-1"></i>${startDate}</div>

        <p class="text-muted small mb-3">${this.escape(e.description)}</p>

        <div class="p-2 bg-light rounded text-muted small mb-3">
          <div><i class="bi bi-geo-alt me-1 text-danger"></i>${this.escape(e.venue_or_link)}</div>
          ${e.speaker_info ? `<div class="mt-1"><i class="bi bi-mic me-1 text-primary"></i>${this.escape(e.speaker_info)}</div>` : ''}
        </div>

        <div class="mt-auto d-flex justify-content-between align-items-center">
          ${e.is_registered ? `<span class="badge bg-success-subtle text-success border border-success-subtle"><i class="bi bi-check-circle me-1"></i>Registered as ${e.my_role}</span>` : '<span class="text-muted small">Open for registration</span>'}

          ${e.is_registered ? `
            <button class="btn btn-sm btn-outline-danger" onclick="App.cancelEventRegistration(${e.id})">Unregister</button>` : `
            <button class="btn btn-sm btn-primary-cms" onclick="App.openEventRegisterModal(${e.id}, '${this.escape(e.title)}')">
              Register / RSVP
            </button>`}
        </div>
      </div>
    `;
  },

  openEventRegisterModal(id, title) {
    if (!this.requireLogin()) return;
    document.getElementById("event-reg-id").value = id;
    document.getElementById("event-reg-title").innerText = title;
    new bootstrap.Modal(document.getElementById("modal-event-register")).show();
  },

  async submitEventRegistration() {
    const id = document.getElementById("event-reg-id").value;
    const role = document.getElementById("event-reg-role").value;

    try {
      const res = await API.post(`/api/events/${id}/register`, { role_in_event: role });
      bootstrap.Modal.getInstance(document.getElementById("modal-event-register")).hide();
      this.showToast(res.message, "success");
      this.renderEvents();
    } catch (e) {
      this.showToast(e.message, "danger");
    }
  },

  async cancelEventRegistration(id) {
    try {
      const res = await API.delete(`/api/events/${id}/register`);
      this.showToast(res.message, "info");
      this.renderEvents();
    } catch (e) {
      this.showToast(e.message, "danger");
    }
  },

  // ================= MESSAGING =================

  async renderMessages(targetConvId = null) {
    if (!this.requireLogin()) return;

    const convList = document.getElementById("conversations-list");
    if (!convList) return;

    try {
      const convs = await API.get("/api/conversations");
      if (convs.length === 0) {
        convList.innerHTML = `<div class="p-3 text-center text-muted small">No conversations yet. Start a chat from any alumni profile!</div>`;
        return;
      }

      convList.innerHTML = convs.map(c => `
        <div class="p-3 border-bottom conversation-item ${c.id == this.activeConversationId ? 'bg-light' : ''}" onclick="App.loadChatThread(${c.id}, '${this.escape(c.other_user_name)}')" style="cursor:pointer">
          <div class="d-flex justify-content-between align-items-center">
            <strong class="text-dark small">${this.escape(c.other_user_name)}</strong>
            ${c.unread_count > 0 ? `<span class="badge bg-primary rounded-pill">${c.unread_count}</span>` : ''}
          </div>
          <div class="text-muted small text-truncate mt-1">${this.escape(c.last_message || 'Start chatting...')}</div>
        </div>
      `).join("");

      if (targetConvId) {
        this.loadChatThread(targetConvId);
      } else if (convs.length > 0 && !this.activeConversationId) {
        this.loadChatThread(convs[0].id, convs[0].other_user_name);
      }
    } catch (e) {
      convList.innerHTML = `<div class="p-3 text-danger small">Error loading conversations.</div>`;
    }
  },

  async loadChatThread(convId, otherUserName = "") {
    this.activeConversationId = convId;
    const titleEl = document.getElementById("chat-recipient-name");
    const container = document.getElementById("chat-messages-container");
    if (titleEl && otherUserName) titleEl.innerText = otherUserName;

    if (container) {
      container.innerHTML = `<div class="p-5 text-center text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Loading messages...</div>`;
      try {
        const msgs = await API.get(`/api/conversations/${convId}/messages`);
        if (msgs.length === 0) {
          container.innerHTML = `<div class="p-4 text-center text-muted small">No messages in this chat yet. Send the first message!</div>`;
          return;
        }

        container.innerHTML = msgs.map(m => `
          <div class="message-bubble ${m.is_me ? 'mine' : 'theirs'}">
            <div>${this.escape(m.content)}</div>
            <div class="text-end" style="font-size: 0.7rem; opacity: 0.8; margin-top: 2px;">
              ${new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        `).join("");
        container.scrollTop = container.scrollHeight;
      } catch (e) {
        container.innerHTML = `<div class="p-4 text-danger small">Error loading messages.</div>`;
      }
    }
  },

  async sendChatMessage() {
    const input = document.getElementById("chat-message-input");
    if (!input || !input.value.trim() || !this.activeConversationId) return;

    const content = input.value.trim();
    input.value = "";

    try {
      // Find recipient from current conversation
      const convs = await API.get("/api/conversations");
      const currentConv = convs.find(c => c.id == this.activeConversationId);
      if (!currentConv) return;

      await API.post("/api/messages", {
        recipient_id: currentConv.other_user_id,
        content
      });

      this.loadChatThread(this.activeConversationId, currentConv.other_user_name);
      this.renderMessages(this.activeConversationId);
    } catch (e) {
      this.showToast(e.message, "danger");
    }
  },

  async startDirectMessage(recipientId, recipientName) {
    if (!this.requireLogin()) return;
    try {
      const res = await API.post("/api/messages", {
        recipient_id: recipientId,
        content: "Hi, I connected with you on CMS AlumniConnect."
      });
      window.location.hash = `#messages/${res.conversation_id}`;
    } catch (e) {
      this.showToast(e.message, "danger");
    }
  },

  // ================= PROFILE MANAGEMENT =================

  // ================= DYNAMIC LINKS & LOGOS HELPER =================

  getPlatformInfo(platform, url = "") {
    const pLower = (platform || "").toLowerCase().trim();
    let domain = "";
    try {
      if (url && (url.startsWith("http://") || url.startsWith("https://"))) {
        domain = new URL(url).hostname.replace(/^www\./, "");
      }
    } catch (_) {}

    // Check specific known developer & social platforms
    if (pLower.includes("github") || domain.includes("github.com")) {
      return { name: "GitHub", icon: '<i class="bi bi-github fs-5 text-dark"></i>', color: "#24292F" };
    }
    if (pLower.includes("linkedin") || domain.includes("linkedin.com")) {
      return { name: "LinkedIn", icon: '<i class="bi bi-linkedin fs-5 text-primary"></i>', color: "#0A66C2" };
    }
    if (pLower.includes("leetcode") || domain.includes("leetcode.com")) {
      return { name: "LeetCode", icon: '<span class="fw-bold" style="color: #FFA116; font-size: 1.1rem;">[LC]</span>', color: "#FFA116" };
    }
    if (pLower.includes("codeforces") || domain.includes("codeforces.com")) {
      return { name: "Codeforces", icon: '<i class="bi bi-bar-chart-steps text-danger fs-5"></i>', color: "#1F8ACB" };
    }
    if (pLower.includes("kaggle") || domain.includes("kaggle.com")) {
      return { name: "Kaggle", icon: '<span class="fw-bold text-info" style="font-size: 1.1rem;">K</span>', color: "#20BEFF" };
    }
    if (pLower.includes("hackerrank") || domain.includes("hackerrank.com")) {
      return { name: "HackerRank", icon: '<span class="fw-bold text-success" style="font-size: 1.1rem;">H</span>', color: "#00EA64" };
    }
    if (pLower.includes("twitter") || pLower.includes("x.com") || domain.includes("twitter.com") || domain.includes("x.com")) {
      return { name: "X (Twitter)", icon: '<i class="bi bi-twitter-x fs-5 text-dark"></i>', color: "#000000" };
    }
    if (pLower.includes("youtube") || domain.includes("youtube.com")) {
      return { name: "YouTube", icon: '<i class="bi bi-youtube fs-5 text-danger"></i>', color: "#FF0000" };
    }
    if (pLower.includes("medium") || domain.includes("medium.com")) {
      return { name: "Medium", icon: '<i class="bi bi-medium fs-5 text-dark"></i>', color: "#000000" };
    }
    if (pLower.includes("stack") || domain.includes("stackoverflow.com")) {
      return { name: "Stack Overflow", icon: '<i class="bi bi-stack-overflow fs-5 text-warning"></i>', color: "#F48024" };
    }
    if (pLower.includes("portfolio") || pLower.includes("website") || pLower.includes("blog")) {
      if (domain) {
        return {
          name: platform || "Portfolio",
          icon: `<img src="https://www.google.com/s2/favicons?domain=${domain}&sz=64" alt="" style="width: 20px; height: 20px; object-fit: contain;">`,
          color: "#4F46E5"
        };
      }
      return { name: "Portfolio", icon: '<i class="bi bi-globe fs-5 text-info"></i>', color: "#4F46E5" };
    }

    // Default fallback: If we have a domain or URL, dynamically fetch the website's favicon!
    if (domain) {
      return {
        name: platform || domain,
        icon: `<img src="https://www.google.com/s2/favicons?domain=${domain}&sz=64" alt="" style="width: 20px; height: 20px; object-fit: contain;">`,
        color: "#64748B"
      };
    }

    return { name: platform || "Website", icon: '<i class="bi bi-link-45deg fs-5 text-secondary"></i>', color: "#64748B" };
  },

  calculateProfileCompleteness(user) {
    if (!user || !user.profile) return { percent: 0, missingItems: [] };
    const p = user.profile;
    const isAlumni = user.role === "alumni";
    const missing = [];
    let score = 0;

    // Full name (10%)
    if (p.full_name && p.full_name.trim().length > 2) score += 10;
    else missing.push("Full Name");

    // Bio / Summary (20%)
    if (p.bio && p.bio.trim().length > 10) score += 20;
    else missing.push("Professional Bio / Summary");

    // Profile Photo (15%)
    if (p.avatar_url) score += 15;
    else missing.push("Profile Photo (Click the initial letter to upload)");

    // Technical Skills (15%)
    if (p.skills && p.skills.trim().length > 3) score += 15;
    else missing.push("Technical Skills");

    // Links (15%)
    let hasLinks = false;
    if (p.custom_links) {
      try {
        const arr = JSON.parse(p.custom_links);
        if (Array.isArray(arr) && arr.length > 0) hasLinks = true;
      } catch (_) {}
    }
    if (!hasLinks && (p.github_url || p.linkedin_url || p.leetcode_url || p.portfolio_url)) {
      hasLinks = true;
    }
    if (hasLinks) score += 15;
    else missing.push("Developer & Portfolio Links (GitHub, LinkedIn, etc.)");

    // Role-specific check (25%)
    if (isAlumni) {
      const hasCompany = !!(p.current_company && p.current_company.trim());
      const hasExperiences = Array.isArray(p.experiences) && p.experiences.length > 0;
      if (hasCompany) score += 10;
      else missing.push("Current Company & Job Title");
      if (hasExperiences) score += 15;
      else missing.push("Work Experience History (LinkedIn-style)");
    } else {
      if (p.current_semester) score += 15;
      else missing.push("Current Semester");
      if (p.cgpa) score += 10;
      else missing.push("Academic CGPA");
    }

    return { percent: Math.min(score, 100), missingItems: missing };
  },

  checkAndShowProfilePrompt() {
    if (!this.currentUser) return;
    if (sessionStorage.getItem("vscms_profile_alert_dismissed") === "true") return;

    const { percent, missingItems } = this.calculateProfileCompleteness(this.currentUser);
    if (percent >= 85 || missingItems.length === 0) return;

    // Populate modal
    const percentEl = document.getElementById("popup-profile-percent");
    const barEl = document.getElementById("popup-profile-progress-bar");
    const listEl = document.getElementById("popup-incomplete-items");
    const modalEl = document.getElementById("modal-complete-profile");

    if (percentEl) percentEl.innerText = `${percent}% Complete`;
    if (barEl) {
      barEl.style.width = `${percent}%`;
      barEl.className = percent < 40 ? "progress-bar progress-bar-striped progress-bar-animated bg-danger" :
                        percent < 75 ? "progress-bar progress-bar-striped progress-bar-animated bg-warning" :
                        "progress-bar progress-bar-striped progress-bar-animated bg-success";
    }

    if (listEl) {
      listEl.innerHTML = `
        <div class="fw-bold small text-dark mb-2"><i class="bi bi-list-check me-1 text-primary"></i> Action items to complete your profile:</div>
        <ul class="mb-0 ps-3 small text-secondary">
          ${missingItems.map(item => `<li class="mb-1"><span class="badge bg-warning-subtle text-warning-emphasis me-1">Missing</span> ${this.escape(item)}</li>`).join("")}
        </ul>
      `;
    }

    if (modalEl) {
      const bsModal = new bootstrap.Modal(modalEl);
      bsModal.show();
    }
  },

  dismissProfileModal() {
    sessionStorage.setItem("vscms_profile_alert_dismissed", "true");
    const modalEl = document.getElementById("modal-complete-profile");
    if (modalEl) {
      const inst = bootstrap.Modal.getInstance(modalEl);
      if (inst) inst.hide();
    }
  },

  goToCompleteProfile() {
    this.dismissProfileModal();
    window.location.hash = "#profile";
  },

  // ================= PROFILE RENDERING =================

  async renderProfile() {
    if (!this.requireLogin()) return;
    const container = document.getElementById("profile-form-container");
    if (!container) return;

    try {
      const user = await API.get("/api/auth/me");
      this.currentUser = user;
      const isAlumni = user.role === "alumni";
      const p = user.profile || {};
      const { percent, missingItems } = this.calculateProfileCompleteness(user);

      // Parse custom links
      let userLinks = [];
      if (p.custom_links) {
        try {
          userLinks = JSON.parse(p.custom_links);
        } catch (_) {}
      }
      if (!userLinks.length) {
        if (p.github_url) userLinks.push({ platform: "GitHub", url: p.github_url });
        if (p.linkedin_url) userLinks.push({ platform: "LinkedIn", url: p.linkedin_url });
        if (p.leetcode_url) userLinks.push({ platform: "LeetCode", url: p.leetcode_url });
        if (p.portfolio_url) userLinks.push({ platform: "Portfolio", url: p.portfolio_url });
      }

      container.innerHTML = `
        <!-- Profile Strength Banner -->
        <div class="profile-strength-widget mb-4 shadow-sm">
          <div class="d-flex flex-wrap justify-content-between align-items-center gap-3">
            <div>
              <div class="d-flex align-items-center gap-2">
                <span class="badge ${percent >= 85 ? 'bg-success' : percent >= 50 ? 'bg-warning text-dark' : 'bg-danger'} fw-bold px-2 py-1">
                  ${percent}% COMPLETE
                </span>
                <strong class="text-dark">Profile Strength: ${percent >= 85 ? 'All-Star Professional' : percent >= 50 ? 'Intermediate' : 'Beginner'}</strong>
              </div>
              <p class="text-secondary small mb-0 mt-1">
                ${percent >= 85 ? 'Awesome! Your profile is complete and ready for networking, mentorship, and placement referrals.' :
                  `Complete the missing items (${missingItems.slice(0, 3).join(', ')}${missingItems.length > 3 ? '...' : ''}) to increase visibility to recruiters and alumni.`}
              </p>
            </div>
            <div style="min-width: 180px;">
              <div class="progress" style="height: 10px; border-radius: 6px; background-color: #E2E8F0;">
                <div class="progress-bar ${percent >= 85 ? 'bg-success' : percent >= 50 ? 'bg-warning' : 'bg-danger'}" role="progressbar" style="width: ${percent}%;"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="row">
          <!-- Left Column: Avatar & Verification -->
          <div class="col-lg-4 text-center border-end pe-lg-4 mb-4 mb-lg-0">
            <!-- Clickable Profile Photo with Camera Overlay -->
            <div class="mx-auto mb-2 position-relative avatar-clickable shadow-sm" onclick="document.getElementById('upload-avatar-file').click()" title="Click here on the letter/photo to upload or change profile photo" style="width: 110px; height: 110px; border-radius: 50%; background: #EEF2FF; color: #4F46E5; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; font-weight: 800; border: 3px solid #C7D2FE; overflow: hidden;">
              ${p.avatar_url ? `<img src="${p.avatar_url}" class="w-100 h-100 rounded-circle" style="object-fit: cover;" alt="">` : `<span class="avatar-letter">${p.full_name?.charAt(0) || 'U'}</span>`}
              <div class="avatar-overlay position-absolute top-0 start-0 w-100 h-100 d-flex flex-column align-items-center justify-content-center" style="background: rgba(15, 23, 42, 0.7); opacity: 0; transition: opacity 0.2s ease; border-radius: 50%;">
                <i class="bi bi-camera-fill text-white fs-4"></i>
                <span class="text-white small fw-bold" style="font-size: 0.7rem;">Change Photo</span>
              </div>
            </div>
            <button type="button" class="btn btn-link btn-sm text-decoration-none text-primary fw-bold p-0 mb-3" onclick="document.getElementById('upload-avatar-file').click()">
              <i class="bi bi-upload me-1"></i> Click letter to upload photo
            </button>
            <input type="file" id="upload-avatar-file" class="d-none" accept="image/*" onchange="App.handleAvatarUpload(event)">

            <h5 class="fw-bold mb-1 text-dark">${this.escape(p.full_name || user.email)}</h5>
            <div class="text-primary small fw-semibold mb-2">${user.role.toUpperCase()}</div>

            ${p.verification_status === "verified" ? `
              <div class="verified-shield mb-3"><i class="bi bi-shield-check"></i> Institutional Verification Approved</div>
            ` : `
              <div class="pending-shield mb-3"><i class="bi bi-clock-history"></i> Verification Status: ${p.verification_status?.toUpperCase() || 'PENDING'}</div>
            `}
            <p class="text-muted small">${this.escape(p.verification_notes || 'Awaiting administrator verification with CMS Kanpur records.')}</p>

            ${isAlumni ? `
              <div class="p-3 bg-light rounded text-start small mb-3 border">
                <div><strong>Current Role:</strong> ${this.escape(p.current_job_title || 'Not specified')}</div>
                <div class="mt-1"><strong>Company:</strong> ${this.escape(p.current_company || 'Not specified')}</div>
                <div class="mt-1"><strong>Degree:</strong> ${this.escape(p.course)} (${p.batch_year} - ${p.graduation_year})</div>
                <div class="mt-1"><strong>City:</strong> ${this.escape(p.current_city || 'Kanpur')}</div>
              </div>
            ` : `
              <div class="p-3 bg-light rounded text-start small mb-3 border">
                <div><strong>Course:</strong> ${this.escape(p.course)}</div>
                <div class="mt-1"><strong>Semester:</strong> ${p.current_semester || 4}th Sem</div>
                <div class="mt-1"><strong>CGPA:</strong> ${p.cgpa || 'N/A'}</div>
              </div>
            `}
          </div>

          <!-- Right Column: Profile Edit Form -->
          <div class="col-lg-8 ps-lg-4">
            <h5 class="fw-bold text-dark border-bottom pb-2 mb-3">Edit Profile Details</h5>
            <form onsubmit="App.saveProfileDetails(event)">
              <div class="row g-3">
                <div class="col-md-6">
                  <label class="form-label small fw-bold">Full Name <span class="text-danger">*</span></label>
                  <input type="text" id="prof-name" class="form-control" value="${this.escape(p.full_name || '')}" required>
                </div>
                <div class="col-md-6">
                  <label class="form-label small fw-bold">Course</label>
                  <input type="text" class="form-control bg-light" value="${this.escape(p.course || '')}" readonly disabled>
                </div>

                ${isAlumni ? `
                  <div class="col-md-6">
                    <label class="form-label small fw-bold">Current Company</label>
                    <input type="text" id="prof-company" class="form-control" value="${this.escape(p.current_company || '')}" placeholder="e.g. Microsoft, Amazon, Infosys">
                  </div>
                  <div class="col-md-6">
                    <label class="form-label small fw-bold">Job Title</label>
                    <input type="text" id="prof-job-title" class="form-control" value="${this.escape(p.current_job_title || '')}" placeholder="e.g. Senior Software Engineer">
                  </div>
                  <div class="col-md-6">
                    <label class="form-label small fw-bold">Current City</label>
                    <input type="text" id="prof-city" class="form-control" value="${this.escape(p.current_city || '')}" placeholder="e.g. Bengaluru, Hyderabad">
                  </div>
                  <div class="col-md-6">
                    <label class="form-label small fw-bold">Graduation Year</label>
                    <input type="number" id="prof-grad-year" class="form-control" min="1980" max="2045" value="${p.graduation_year || 2023}" placeholder="e.g. 2024 (any past/future year)">
                    <small class="text-muted" style="font-size: 0.72rem;">Accepts any past or upcoming graduation year.</small>
                  </div>
                ` : `
                  <div class="col-md-6">
                    <label class="form-label small fw-bold">Current Semester</label>
                    <input type="number" id="prof-semester" class="form-control" min="1" max="8" value="${p.current_semester || 4}">
                  </div>
                  <div class="col-md-6">
                    <label class="form-label small fw-bold">CGPA</label>
                    <input type="text" id="prof-cgpa" class="form-control" placeholder="e.g. 8.7" value="${p.cgpa || ''}">
                  </div>
                `}

                <div class="col-12">
                  <label class="form-label small fw-bold">About & Professional Bio</label>
                  <textarea id="prof-bio" class="form-control" rows="3" placeholder="Briefly describe your career journey, tech passion, and how you want to connect with CMS students/alumni...">${this.escape(p.bio || '')}</textarea>
                </div>

                <div class="col-12">
                  <label class="form-label small fw-bold">Technical Skills (comma-separated)</label>
                  <input type="text" id="prof-skills" class="form-control font-monospace" placeholder="e.g. Python, FastAPI, React, PostgreSQL, Docker, AWS" value="${this.escape(p.skills || '')}">
                </div>

                <!-- SECTION: DYNAMIC PORTFOLIO & SOCIAL LINKS WITH LIVE LOGO FETCH -->
                <div class="col-12 mt-4">
                  <div class="d-flex justify-content-between align-items-center border-bottom pb-2 mb-3">
                    <div>
                      <h6 class="fw-bold text-dark mb-0"><i class="bi bi-link-45deg text-primary me-1"></i> Professional & Developer Profiles</h6>
                      <small class="text-muted">Add your profiles (GitHub, LinkedIn, LeetCode, Codeforces, Portfolio, etc.). Website logos are automatically fetched!</small>
                    </div>
                    <button type="button" class="btn btn-outline-primary btn-sm fw-bold" onclick="App.addLinkRow()">
                      <i class="bi bi-plus-lg me-1"></i> Add Link
                    </button>
                  </div>

                  <div id="dynamic-links-container" class="d-flex flex-column gap-2">
                    ${userLinks.map((link, idx) => {
                      const info = this.getPlatformInfo(link.platform, link.url);
                      return `
                        <div class="link-row-item d-flex align-items-center gap-2 p-2 rounded border bg-light" data-link-row>
                          <div class="platform-logo-preview" data-preview-logo>
                            ${info.icon}
                          </div>
                          <div style="width: 180px;">
                            <input type="text" class="form-control form-control-sm fw-semibold" placeholder="Platform (e.g. GitHub)" value="${this.escape(link.platform || '')}" oninput="App.updateLinkLogoPreview(this)" list="platforms-datalist">
                          </div>
                          <div class="flex-grow-1">
                            <input type="url" class="form-control form-control-sm" placeholder="Profile URL (e.g. https://...)" value="${this.escape(link.url || '')}" oninput="App.updateLinkLogoPreview(this)">
                          </div>
                          <button type="button" class="btn btn-outline-danger btn-sm px-2" title="Remove Link" onclick="this.closest('[data-link-row]').remove()">
                            <i class="bi bi-trash"></i>
                          </button>
                        </div>
                      `;
                    }).join("")}
                  </div>

                  <datalist id="platforms-datalist">
                    <option value="GitHub">
                    <option value="LinkedIn">
                    <option value="LeetCode">
                    <option value="Codeforces">
                    <option value="HackerRank">
                    <option value="Kaggle">
                    <option value="Portfolio Website">
                    <option value="X (Twitter)">
                    <option value="Medium">
                    <option value="Stack Overflow">
                    <option value="YouTube">
                    <option value="Dribbble">
                    <option value="Behance">
                  </datalist>
                </div>

                ${isAlumni ? `
                  <div class="col-12 mt-3 p-3 bg-light rounded border">
                    <div class="form-check form-switch mb-2">
                      <input class="form-check-input" type="checkbox" id="prof-is-mentor" ${p.is_mentor ? 'checked' : ''}>
                      <label class="form-check-label small fw-bold" for="prof-is-mentor">Available to Mentor CMS Kanpur Students (1-on-1 Sessions)</label>
                    </div>
                    <div class="form-check form-switch">
                      <input class="form-check-input" type="checkbox" id="prof-is-referral" ${p.is_referral_provider ? 'checked' : ''}>
                      <label class="form-check-label small fw-bold" for="prof-is-referral">Available to Provide Job/Internship Referrals at My Company</label>
                    </div>
                  </div>
                ` : ''}

                <div class="col-12 mt-3">
                  <button type="submit" id="btn-save-profile" class="btn btn-vscms-maroon px-4 fw-bold">
                    <i class="bi bi-save me-1"></i> Save Profile Details
                  </button>
                </div>
              </div>
            </form>

            <!-- SECTION: LINKEDIN-STYLE WORK EXPERIENCE -->
            ${isAlumni ? `
              <div class="mt-5 pt-3 border-top">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <div>
                    <h5 class="fw-bold text-dark mb-0"><i class="bi bi-briefcase text-primary me-2"></i> Work Experience</h5>
                    <small class="text-muted">Display companies where you have been employed, your role, and tenure (LinkedIn-style).</small>
                  </div>
                  <button type="button" class="btn btn-outline-primary btn-sm fw-bold" onclick="App.openAddExperienceModal()">
                    <i class="bi bi-plus-lg me-1"></i> Add Experience
                  </button>
                </div>

                <div id="experience-list-container" class="d-flex flex-column gap-3">
                  ${(p.experiences && p.experiences.length > 0) ? p.experiences.map(exp => {
                    const compLogoUrl = `https://www.google.com/s2/favicons?domain=${encodeURIComponent(exp.company.toLowerCase().replace(/\s+/g, '') + '.com')}&sz=64`;
                    return `
                      <div class="exp-linkedin-card d-flex gap-3 align-items-start">
                        <div class="company-logo-badge">
                          <img src="${compLogoUrl}" alt="" onerror="this.onerror=null; this.parentElement.innerText='${this.escape(exp.company.charAt(0).toUpperCase())}';">
                        </div>
                        <div class="flex-grow-1">
                          <div class="d-flex justify-content-between align-items-start">
                            <div>
                              <h6 class="fw-bold text-dark mb-0">${this.escape(exp.job_title)}</h6>
                              <div class="text-primary fw-semibold small">${this.escape(exp.company)}</div>
                            </div>
                            <div class="d-flex gap-1">
                              <button type="button" class="btn btn-outline-secondary btn-sm py-0 px-2" title="Edit Experience" onclick="App.openAddExperienceModal(${exp.id})">
                                <i class="bi bi-pencil small"></i>
                              </button>
                              <button type="button" class="btn btn-outline-danger btn-sm py-0 px-2" title="Delete Experience" onclick="App.deleteExperience(${exp.id})">
                                <i class="bi bi-trash small"></i>
                              </button>
                            </div>
                          </div>
                          <div class="text-muted small mt-1">
                            <i class="bi bi-calendar3 me-1"></i> ${this.escape(exp.start_date)} - ${exp.is_current ? '<span class="badge bg-success-subtle text-success">Present</span>' : this.escape(exp.end_date || 'Present')}
                            ${exp.location ? ` • <i class="bi bi-geo-alt me-1"></i> ${this.escape(exp.location)}` : ''}
                          </div>
                          ${exp.description ? `<p class="text-secondary small mt-2 mb-0" style="white-space: pre-line;">${this.escape(exp.description)}</p>` : ''}
                        </div>
                      </div>
                    `;
                  }).join("") : `
                    <div class="text-center py-4 bg-light rounded-3 border">
                      <i class="bi bi-briefcase text-muted fs-3 mb-2 d-block"></i>
                      <div class="text-dark fw-bold small">No work experiences added yet</div>
                      <p class="text-muted small mb-3">Add companies you have worked at to boost your profile strength and credibility.</p>
                      <button type="button" class="btn btn-sm btn-outline-primary fw-bold" onclick="App.openAddExperienceModal()">
                        <i class="bi bi-plus-lg me-1"></i> Add First Experience
                      </button>
                    </div>
                  `}
                </div>
              </div>
            ` : ''}
          </div>
        </div>
      `;
    } catch (e) {
      container.innerHTML = `<div class="p-4 text-danger text-center">Error loading profile: ${e.message}</div>`;
    }
  },

  addLinkRow(platform = "", url = "") {
    const container = document.getElementById("dynamic-links-container");
    if (!container) return;

    const row = document.createElement("div");
    row.className = "link-row-item d-flex align-items-center gap-2 p-2 rounded border bg-light";
    row.setAttribute("data-link-row", "true");

    const info = this.getPlatformInfo(platform, url);
    row.innerHTML = `
      <div class="platform-logo-preview" data-preview-logo>
        ${info.icon}
      </div>
      <div style="width: 180px;">
        <input type="text" class="form-control form-control-sm fw-semibold" placeholder="Platform (e.g. GitHub)" value="${this.escape(platform)}" oninput="App.updateLinkLogoPreview(this)" list="platforms-datalist">
      </div>
      <div class="flex-grow-1">
        <input type="url" class="form-control form-control-sm" placeholder="Profile URL (e.g. https://...)" value="${this.escape(url)}" oninput="App.updateLinkLogoPreview(this)">
      </div>
      <button type="button" class="btn btn-outline-danger btn-sm px-2" title="Remove Link" onclick="this.closest('[data-link-row]').remove()">
        <i class="bi bi-trash"></i>
      </button>
    `;
    container.appendChild(row);
  },

  updateLinkLogoPreview(inputEl) {
    const row = inputEl.closest("[data-link-row]");
    if (!row) return;

    const inputs = row.querySelectorAll("input");
    const platform = inputs[0]?.value || "";
    const url = inputs[1]?.value || "";

    const preview = row.querySelector("[data-preview-logo]");
    if (preview) {
      const info = this.getPlatformInfo(platform, url);
      preview.innerHTML = info.icon;
    }
  },

  async saveProfileDetails(e) {
    e.preventDefault();
    const isAlumni = this.currentUser.role === "alumni";
    const endpoint = isAlumni ? "/api/alumni/profile" : "/api/students/profile";

    // Collect dynamic links
    const linkRows = document.querySelectorAll("#dynamic-links-container [data-link-row]");
    const links = [];
    let githubUrl = null;
    let linkedinUrl = null;
    let leetcodeUrl = null;
    let portfolioUrl = null;

    linkRows.forEach(row => {
      const inputs = row.querySelectorAll("input");
      const platform = inputs[0]?.value.trim() || "";
      const url = inputs[1]?.value.trim() || "";
      if (url) {
        links.push({ platform: platform || "Website", url });
        const pLower = platform.toLowerCase();
        if (pLower.includes("github") && !githubUrl) githubUrl = url;
        if (pLower.includes("linkedin") && !linkedinUrl) linkedinUrl = url;
        if (pLower.includes("leetcode") && !leetcodeUrl) leetcodeUrl = url;
        if ((pLower.includes("portfolio") || pLower.includes("website")) && !portfolioUrl) portfolioUrl = url;
      }
    });

    const payload = {
      full_name: document.getElementById("prof-name").value.trim(),
      bio: document.getElementById("prof-bio").value.trim(),
      skills: document.getElementById("prof-skills").value.trim(),
      custom_links: JSON.stringify(links),
      github_url: githubUrl,
      linkedin_url: linkedinUrl,
      leetcode_url: leetcodeUrl,
      portfolio_url: portfolioUrl
    };

    if (isAlumni) {
      payload.current_company = document.getElementById("prof-company")?.value.trim() || "";
      payload.current_job_title = document.getElementById("prof-job-title")?.value.trim() || "";
      payload.current_city = document.getElementById("prof-city")?.value.trim() || "";
      const gradYear = document.getElementById("prof-grad-year")?.value;
      if (gradYear) payload.graduation_year = parseInt(gradYear);
      payload.is_mentor = document.getElementById("prof-is-mentor")?.checked || false;
      payload.is_referral_provider = document.getElementById("prof-is-referral")?.checked || false;
    } else {
      payload.current_semester = parseInt(document.getElementById("prof-semester")?.value || 4);
      const cgpaVal = document.getElementById("prof-cgpa")?.value.trim();
      if (cgpaVal) payload.cgpa = parseFloat(cgpaVal);
    }

    const btn = document.getElementById("btn-save-profile");
    if (btn) btn.disabled = true;

    try {
      const res = await API.put(endpoint, payload);
      this.showToast(res.message, "success");
      await this.checkAuth();
      this.renderProfile();
    } catch (err) {
      this.showToast(err.message, "danger");
    } finally {
      if (btn) btn.disabled = false;
    }
  },

  async handleAvatarUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const fd = new FormData();
    fd.append("file", file);

    this.showToast("Uploading profile avatar...", "info");

    try {
      const res = await API.post("/api/upload/avatar", fd);
      this.showToast(res.message, "success");
      await this.checkAuth();
      this.renderProfile();
    } catch (err) {
      this.showToast(err.message, "danger");
    }
  },

  // ================= LINKEDIN-STYLE EXPERIENCE MANAGEMENT =================

  openAddExperienceModal(expId = null) {
    const modalEl = document.getElementById("modal-add-experience");
    if (!modalEl) return;

    document.getElementById("exp-edit-id").value = expId || "";
    document.getElementById("exp-modal-title").innerText = expId ? "Edit Work Experience" : "Add Work Experience";

    if (expId && this.currentUser?.profile?.experiences) {
      const exp = this.currentUser.profile.experiences.find(e => e.id === expId);
      if (exp) {
        document.getElementById("exp-company").value = exp.company || "";
        document.getElementById("exp-title").value = exp.job_title || "";
        document.getElementById("exp-location").value = exp.location || "";
        document.getElementById("exp-start-date").value = exp.start_date || "";
        document.getElementById("exp-end-date").value = exp.end_date || "";
        document.getElementById("exp-is-current").checked = !!exp.is_current;
        document.getElementById("exp-end-date").disabled = !!exp.is_current;
        document.getElementById("exp-description").value = exp.description || "";
        this.previewCompanyLogo(exp.company);
      }
    } else {
      document.getElementById("exp-company").value = "";
      document.getElementById("exp-title").value = "";
      document.getElementById("exp-location").value = "";
      document.getElementById("exp-start-date").value = "";
      document.getElementById("exp-end-date").value = "";
      document.getElementById("exp-is-current").checked = false;
      document.getElementById("exp-end-date").disabled = false;
      document.getElementById("exp-description").value = "";
      this.previewCompanyLogo("");
    }

    const modal = new bootstrap.Modal(modalEl);
    modal.show();
  },

  previewCompanyLogo(company) {
    const previewEl = document.getElementById("exp-company-logo-preview");
    if (!previewEl) return;
    const compClean = (company || "").trim();
    if (!compClean) {
      previewEl.innerHTML = '<i class="bi bi-building text-muted"></i>';
      return;
    }

    const domain = compClean.toLowerCase().replace(/[^a-z0-9]/g, "") + ".com";
    previewEl.innerHTML = `
      <img src="https://www.google.com/s2/favicons?domain=${domain}&sz=64" alt="" style="width: 22px; height: 22px; object-fit: contain;" onerror="this.onerror=null; this.parentElement.innerHTML='<span class=\\'fw-bold text-dark small\\'>${compClean.charAt(0).toUpperCase()}</span>'">
    `;
  },

  async submitExperience(e) {
    e.preventDefault();
    const expId = document.getElementById("exp-edit-id")?.value;
    const isCurrent = document.getElementById("exp-is-current")?.checked || false;

    const payload = {
      company: document.getElementById("exp-company").value.trim(),
      job_title: document.getElementById("exp-title").value.trim(),
      location: document.getElementById("exp-location").value.trim() || null,
      start_date: document.getElementById("exp-start-date").value.trim(),
      end_date: isCurrent ? "Present" : (document.getElementById("exp-end-date").value.trim() || null),
      is_current: isCurrent,
      description: document.getElementById("exp-description").value.trim() || null
    };

    const btn = document.getElementById("btn-save-experience");
    if (btn) btn.disabled = true;

    try {
      if (expId) {
        await API.put(`/api/alumni/experiences/${expId}`, payload);
        this.showToast("Career experience updated successfully!", "success");
      } else {
        await API.post("/api/alumni/experiences", payload);
        this.showToast("New career experience added successfully!", "success");
      }

      const modalEl = document.getElementById("modal-add-experience");
      if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
      }

      await this.checkAuth();
      this.renderProfile();
    } catch (err) {
      this.showToast(err.message, "danger");
    } finally {
      if (btn) btn.disabled = false;
    }
  },

  async deleteExperience(expId) {
    if (!confirm("Are you sure you want to remove this experience entry?")) return;

    try {
      await API.delete(`/api/alumni/experiences/${expId}`);
      this.showToast("Experience removed.", "info");
      await this.checkAuth();
      this.renderProfile();
    } catch (err) {
      this.showToast(err.message, "danger");
    }
  },

  // ================= ADMIN DASHBOARD =================

  async renderAdmin() {
    if (!this.currentUser || !["admin", "super_admin", "faculty"].includes(this.currentUser.role)) {
      window.location.hash = "#home";
      return;
    }

    try {
      const data = await API.get("/api/admin/dashboard");
      const m = data.metrics;

      // Update stat counters
      document.getElementById("admin-stat-students").innerText = m.total_students;
      document.getElementById("admin-stat-alumni").innerText = m.total_alumni;
      document.getElementById("admin-stat-verified").innerText = m.verified_alumni;
      document.getElementById("admin-stat-pending").innerText = m.pending_verifications;
      document.getElementById("admin-stat-jobs").innerText = m.jobs_posted;
      document.getElementById("admin-stat-referrals").innerText = m.total_referrals;

      // Render Charts with Chart.js
      this.initAdminCharts(data.charts);

      // Render Verification Queue
      this.renderVerificationQueue();

      // Render Audit Logs
      this.renderAuditLogs();

      // Render Users Table
      this.renderUsersTable();
    } catch (e) {
      console.error("Admin dashboard load failed:", e);
    }
  },

  initAdminCharts(chartsData) {
    if (typeof Chart === "undefined") return;

    // 1. Batch distribution
    const batchCtx = document.getElementById("chart-batch-distribution");
    if (batchCtx && chartsData.batch_distribution?.length) {
      if (this.adminCharts.batch) this.adminCharts.batch.destroy();
      this.adminCharts.batch = new Chart(batchCtx, {
        type: "bar",
        data: {
          labels: chartsData.batch_distribution.map(b => `Batch ${b.batch}`),
          datasets: [{
            label: "Alumni Count",
            data: chartsData.batch_distribution.map(b => b.count),
            backgroundColor: "#4F46E5",
            borderRadius: 6
          }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
      });
    }

    // 2. Company distribution
    const compCtx = document.getElementById("chart-company-distribution");
    if (compCtx && chartsData.company_distribution?.length) {
      if (this.adminCharts.company) this.adminCharts.company.destroy();
      this.adminCharts.company = new Chart(compCtx, {
        type: "doughnut",
        data: {
          labels: chartsData.company_distribution.map(c => c.company),
          datasets: [{
            data: chartsData.company_distribution.map(c => c.count),
            backgroundColor: ["#4F46E5", "#06B6D4", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#64748B", "#3B82F6"]
          }]
        },
        options: { responsive: true }
      });
    }

    // 3. Tech Skills distribution
    const techCtx = document.getElementById("chart-tech-distribution");
    if (techCtx && chartsData.technology_distribution?.length) {
      if (this.adminCharts.tech) this.adminCharts.tech.destroy();
      this.adminCharts.tech = new Chart(techCtx, {
        type: "bar",
        data: {
          labels: chartsData.technology_distribution.map(t => t.technology),
          datasets: [{
            label: "Developers",
            data: chartsData.technology_distribution.map(t => t.count),
            backgroundColor: "#0EA5E9",
            borderRadius: 6
          }]
        },
        options: { indexAxis: "y", responsive: true, plugins: { legend: { display: false } } }
      });
    }
  },

  async renderVerificationQueue() {
    const tableBody = document.getElementById("verification-queue-tbody");
    if (!tableBody) return;

    try {
      const items = await API.get("/api/admin/verifications");
      if (items.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted"><i class="bi bi-check-circle text-success me-1"></i>All student and alumni registrations are verified!</td></tr>`;
        return;
      }

      tableBody.innerHTML = items.map(item => `
        <tr>
          <td><strong class="text-dark">${this.escape(item.full_name)}</strong><br><small class="text-muted">${this.escape(item.email)}</small></td>
          <td><span class="badge ${item.type === 'alumni' ? 'bg-primary' : 'bg-info'} text-uppercase">${item.type}</span></td>
          <td>${this.escape(item.course)} ('${item.batch_year})</td>
          <td class="font-monospace small">${this.escape(item.roll_no)}<br><span class="text-muted">${this.escape(item.enrollment_no)}</span></td>
          <td>${item.current_company ? `<span class="small">${this.escape(item.current_company)}</span>` : '<span class="text-muted small">Student</span>'}</td>
          <td><span class="badge bg-warning text-dark"><i class="bi bi-clock me-1"></i>Pending</span></td>
          <td>
            <div class="btn-group btn-group-sm">
              <button class="btn btn-success btn-sm" onclick="App.processVerification(${item.profile_id}, '${item.type}', 'verified')">
                <i class="bi bi-check-lg"></i> Approve
              </button>
              <button class="btn btn-outline-danger btn-sm" onclick="App.processVerification(${item.profile_id}, '${item.type}', 'rejected')">
                <i class="bi bi-x-lg"></i> Reject
              </button>
            </div>
          </td>
        </tr>
      `).join("");
    } catch (e) {
      tableBody.innerHTML = `<tr><td colspan="7" class="text-danger text-center">Error loading queue.</td></tr>`;
    }
  },

  async processVerification(profileId, userType, statusVal) {
    try {
      const res = await API.put(`/api/admin/verifications/${profileId}?user_type=${userType}`, {
        status: statusVal,
        notes: `Processed by ${this.currentUser.email}`
      });
      this.showToast(res.message, "success");
      this.renderAdmin();
    } catch (e) {
      this.showToast(e.message, "danger");
    }
  },

  async renderUsersTable() {
    const tbody = document.getElementById("admin-users-tbody");
    if (!tbody) return;

    try {
      const res = await API.get("/api/admin/users?page_size=15");
      tbody.innerHTML = res.items.map(u => `
        <tr>
          <td>#${u.id}</td>
          <td><strong>${this.escape(u.full_name)}</strong><br><small class="text-muted">${this.escape(u.email)}</small></td>
          <td><span class="badge ${u.role === 'alumni' ? 'bg-primary' : u.role === 'student' ? 'bg-info' : 'bg-danger'}">${u.role.toUpperCase()}</span></td>
          <td>${this.escape(u.course)} ${u.batch ? `'${u.batch}` : ''}</td>
          <td>${u.is_verified ? '<span class="badge bg-success-subtle text-success border">Verified</span>' : '<span class="badge bg-warning-subtle text-warning border">Pending</span>'}</td>
          <td>${u.is_active ? '<span class="text-success"><i class="bi bi-check-circle-fill"></i> Active</span>' : '<span class="text-danger"><i class="bi bi-slash-circle-fill"></i> Suspended</span>'}</td>
          <td>
            <button class="btn btn-xs btn-outline-secondary" onclick="App.toggleUserStatus(${u.id}, ${!u.is_active})">
              ${u.is_active ? 'Suspend' : 'Activate'}
            </button>
          </td>
        </tr>
      `).join("");
    } catch (e) {}
  },

  async toggleUserStatus(userId, makeActive) {
    try {
      const res = await API.put(`/api/admin/users/${userId}/status?is_active=${makeActive}`);
      this.showToast(res.message, "info");
      this.renderUsersTable();
    } catch (e) {
      this.showToast(e.message, "danger");
    }
  },

  async renderAuditLogs() {
    const tbody = document.getElementById("admin-audit-tbody");
    if (!tbody) return;

    try {
      const res = await API.get("/api/admin/audit-logs?page_size=10");
      tbody.innerHTML = res.items.map(l => `
        <tr>
          <td class="font-monospace small">${this.escape(l.action)}</td>
          <td class="small">${this.escape(l.user_email)}</td>
          <td class="small text-muted">${this.escape(l.details || '')}</td>
          <td class="small text-muted">${new Date(l.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</td>
        </tr>
      `).join("");
    } catch (e) {}
  },

  async broadcastNewsletter(e) {
    e.preventDefault();
    const title = document.getElementById("nl-title").value;
    const content = document.getElementById("nl-content").value;

    try {
      const createRes = await API.post("/api/admin/newsletters", {
        title,
        content_html: content
      });
      const sendRes = await API.post(`/api/admin/newsletters/${createRes.id}/send`);
      this.showToast(sendRes.message, "success");
      document.getElementById("form-newsletter").reset();
    } catch (err) {
      this.showToast(err.message, "danger");
    }
  },

  // ================= AUTH MODALS & INSTITUTIONAL HANDLERS =================

  openLoginModal() {
    window.location.hash = "#auth";
    this.switchAuthTab("login");
  },

  openRegisterModal() {
    window.location.hash = "#auth";
    this.switchAuthTab("register");
  },

  initAuthView() {
    const navBtn = document.getElementById("nav-signin-btn");
    if (navBtn) navBtn.classList.add("nav-auth-active");
    if (!document.getElementById("auth-login-captcha-id")?.value) {
      this.fetchCaptcha();
    }
  },

  async fetchCaptcha() {
    const captchaBox = document.getElementById("auth-captcha-box");
    const captchaIdInput = document.getElementById("auth-login-captcha-id");
    const captchaCodeInput = document.getElementById("auth-login-captcha");
    if (!captchaBox) return;

    try {
      const res = await API.get("/api/auth/captcha");
      captchaBox.innerHTML = res.captcha_svg;
      if (captchaIdInput) captchaIdInput.value = res.captcha_id;
      if (captchaCodeInput) captchaCodeInput.value = "";
    } catch (err) {
      console.error("Failed to load captcha:", err);
      captchaBox.innerHTML = `<span class="text-danger small px-2">Error loading captcha</span>`;
    }
  },

  async refreshCaptcha() {
    const captchaBox = document.getElementById("auth-captcha-box");
    if (captchaBox) {
      captchaBox.innerHTML = `<div class="spinner-border spinner-border-sm text-secondary" role="status"></div>`;
    }
    await this.fetchCaptcha();
  },

  togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const isPass = input.type === "password";
    input.type = isPass ? "text" : "password";
    const icon = btn.querySelector("i");
    if (icon) {
      icon.className = isPass ? "bi bi-eye-slash" : "bi bi-eye";
    }
  },

  switchAuthTab(tab) {
    const tabLoginBtn = document.getElementById("tab-btn-login");
    const tabRegBtn = document.getElementById("tab-btn-register");
    const paneLogin = document.getElementById("auth-pane-login");
    const paneReg = document.getElementById("auth-pane-register");

    this.hideAuthAlert();
    this.hideRegAlert();

    if (tab === "login") {
      if (tabLoginBtn) { tabLoginBtn.classList.add("active"); tabLoginBtn.setAttribute("aria-selected", "true"); }
      if (tabRegBtn) { tabRegBtn.classList.remove("active"); tabRegBtn.setAttribute("aria-selected", "false"); }
      if (paneLogin) paneLogin.classList.remove("d-none");
      if (paneReg) paneReg.classList.add("d-none");
      if (!document.getElementById("auth-login-captcha-id")?.value) {
        this.fetchCaptcha();
      }
    } else {
      if (tabRegBtn) { tabRegBtn.classList.add("active"); tabRegBtn.setAttribute("aria-selected", "true"); }
      if (tabLoginBtn) { tabLoginBtn.classList.remove("active"); tabLoginBtn.setAttribute("aria-selected", "false"); }
      if (paneReg) paneReg.classList.remove("d-none");
      if (paneLogin) paneLogin.classList.add("d-none");
    }
  },

  switchRegType(type) {
    const btnStudent = document.getElementById("btn-regtype-student");
    const btnAlumni = document.getElementById("btn-regtype-alumni");
    const roleInput = document.getElementById("vscms-reg-role");
    const btnRegText = document.getElementById("btn-reg-text");
    const lblEmail = document.getElementById("lbl-primary-email");

    const alumniFields = document.querySelectorAll(".reg-alumni-only");
    const studentFields = document.querySelectorAll(".reg-student-only");

    if (type === "student") {
      if (btnStudent) {
        btnStudent.className = "btn btn-sm rounded-pill fw-bold px-4 py-2 btn-vscms-maroon";
      }
      if (btnAlumni) {
        btnAlumni.className = "btn btn-sm rounded-pill fw-bold px-4 py-2 btn-light text-secondary";
      }
      if (roleInput) roleInput.value = "student";
      alumniFields.forEach(el => el.classList.add("d-none"));
      studentFields.forEach(el => el.classList.remove("d-none"));
      if (btnRegText) btnRegText.innerHTML = '<i class="bi bi-mortarboard-fill me-1"></i> Register as Student';
      if (lblEmail) lblEmail.innerHTML = 'College Email <span class="text-danger">*</span>';
    } else {
      if (btnAlumni) {
        btnAlumni.className = "btn btn-sm rounded-pill fw-bold px-4 py-2 btn-vscms-maroon";
      }
      if (btnStudent) {
        btnStudent.className = "btn btn-sm rounded-pill fw-bold px-4 py-2 btn-light text-secondary";
      }
      if (roleInput) roleInput.value = "alumni";
      alumniFields.forEach(el => el.classList.remove("d-none"));
      studentFields.forEach(el => el.classList.add("d-none"));
      if (btnRegText) btnRegText.innerHTML = '<i class="bi bi-briefcase-fill me-1"></i> Register as Alumni';
      if (lblEmail) lblEmail.innerHTML = 'Email Address <span class="text-danger">*</span>';
    }
  },

  showAuthAlert(message, type = "danger") {
    const alertBox = document.getElementById("auth-login-alert");
    const alertMsg = document.getElementById("auth-login-alert-msg");
    const alertIcon = document.getElementById("auth-login-alert-icon");
    if (!alertBox || !alertMsg) return;

    alertBox.className = `alert alert-${type} mb-4 py-2 px-3 d-flex align-items-center gap-2`;
    alertMsg.innerText = message;
    if (alertIcon) {
      alertIcon.className = type === "success" ? "bi bi-check-circle-fill fs-5 flex-shrink-0 text-success" :
                            type === "warning" ? "bi bi-exclamation-triangle-fill fs-5 flex-shrink-0 text-warning" :
                            "bi bi-exclamation-circle-fill fs-5 flex-shrink-0 text-danger";
    }
    alertBox.classList.remove("d-none");
  },

  hideAuthAlert() {
    const alertBox = document.getElementById("auth-login-alert");
    if (alertBox) alertBox.classList.add("d-none");
  },

  showRegAlert(message, type = "danger") {
    const alertBox = document.getElementById("auth-reg-alert");
    const alertMsg = document.getElementById("auth-reg-alert-msg");
    if (!alertBox || !alertMsg) return;
    alertBox.className = `alert alert-${type} mb-3 py-2 px-3 d-flex align-items-center gap-2`;
    alertMsg.innerText = message;
    alertBox.classList.remove("d-none");
  },

  hideRegAlert() {
    const alertBox = document.getElementById("auth-reg-alert");
    if (alertBox) alertBox.classList.add("d-none");
  },

  async submitPageLogin(e) {
    e.preventDefault();
    const identifier = document.getElementById("auth-login-identifier")?.value.trim() || "";
    const password = document.getElementById("auth-login-password")?.value || "";
    const rememberMe = document.getElementById("auth-login-remember")?.checked || false;

    if (!identifier || !password) {
      this.showAuthAlert("Unable to sign in. Please check your email/username and password.", "danger");
      return;
    }

    const btn = document.getElementById("btn-login-submit");
    const spinner = document.getElementById("btn-login-spinner");
    const btnText = document.getElementById("btn-login-text");

    if (btn) btn.disabled = true;
    if (spinner) spinner.classList.remove("d-none");
    if (btnText) btnText.innerHTML = "Signing In...";
    this.hideAuthAlert();

    try {
      const res = await API.post("/api/auth/login", {
        email: identifier,
        password: password,
        remember_me: rememberMe
      });

      API.setToken(res.access_token);
      this.currentUser = {
        user_id: res.user_id,
        email: res.email,
        role: res.role,
        full_name: res.full_name,
        is_verified: res.is_verified,
        profile: { full_name: res.full_name }
      };
      API.setUser(this.currentUser);
      this.updateAuthUI();

      this.showAuthAlert(`Access Granted. Welcome back, ${res.full_name}! Redirecting to your dashboard...`, "success");

      const targetView = ["admin", "super_admin", "faculty"].includes(res.role) ? "admin" : "home";
      setTimeout(async () => {
        window.location.hash = `#${targetView}`;
        this.activeView = targetView;
        this.showView(targetView);
        if (btn) btn.disabled = false;
        if (spinner) spinner.classList.add("d-none");
        if (btnText) btnText.innerHTML = '<i class="bi bi-box-arrow-in-right me-1"></i> SIGN IN TO PORTAL';
        try {
          await this.checkAuth();
        } catch (e) {}
      }, 350);

    } catch (err) {
      if (btn) btn.disabled = false;
      if (spinner) spinner.classList.add("d-none");
      if (btnText) btnText.innerHTML = '<i class="bi bi-box-arrow-in-right me-1"></i> SIGN IN TO PORTAL';

      console.error("Login failure details:", err);
      const errMsg = (err.message || "").toLowerCase();
      if (errMsg.includes("401") || errMsg.includes("password") || errMsg.includes("invalid") || errMsg.includes("credentials") || errMsg.includes("sign in")) {
        this.showAuthAlert("Unable to sign in. Please check your email/username and password.", "danger");
      } else if (errMsg.includes("awaiting") || errMsg.includes("verification")) {
        this.showAuthAlert("Your account is awaiting VSCMS verification.", "warning");
      } else if (errMsg.includes("suspend") || errMsg.includes("inactive")) {
        this.showAuthAlert("This account has been temporarily suspended. Please contact the administrator.", "danger");
      } else {
        this.showAuthAlert(err.message || "Unable to connect to the portal. Please try again shortly.", "danger");
      }

      this.refreshCaptcha();
    }
  },

  async submitPageRegister(e) {
    e.preventDefault();
    const role = document.getElementById("vscms-reg-role")?.value || "student";
    const password = document.getElementById("reg-password")?.value || "";
    const confirmPassword = document.getElementById("reg-confirmpassword")?.value || "";

    if (password !== confirmPassword) {
      this.showRegAlert("Passwords do not match. Please ensure both password fields match.", "danger");
      return;
    }

    if (password.length < 6) {
      this.showRegAlert("Password must be at least 6 characters long.", "danger");
      return;
    }

    const payload = {
      role: role,
      full_name: document.getElementById("reg-fullname")?.value.trim(),
      course: document.getElementById("reg-course")?.value || "BCA",
      batch_year: parseInt(document.getElementById("reg-batch")?.value || "2024"),
      roll_no: document.getElementById("reg-rollno")?.value.trim(),
      enrollment_no: document.getElementById("reg-enrollment")?.value.trim(),
      email: document.getElementById("reg-email")?.value.trim().toLowerCase(),
      password: password,
      phone: document.getElementById("reg-phone")?.value.trim() || null
    };

    if (role === "student") {
      const personalEmail = document.getElementById("reg-personal-email")?.value.trim();
      if (personalEmail) payload.personal_email = personalEmail.toLowerCase();
    } else if (role === "alumni") {
      const gradYear = document.getElementById("reg-gradyear")?.value;
      if (gradYear) payload.graduation_year = parseInt(gradYear);
      payload.current_company = document.getElementById("reg-company")?.value.trim() || null;
      payload.current_job_title = document.getElementById("reg-jobrole")?.value.trim() || null;
    }

    const btn = document.getElementById("btn-reg-submit");
    const spinner = document.getElementById("btn-reg-spinner");

    if (btn) btn.disabled = true;
    if (spinner) spinner.classList.remove("d-none");
    this.hideRegAlert();

    try {
      const res = await API.post("/api/auth/register", payload);
      API.setToken(res.access_token);
      this.currentUser = {
        user_id: res.user_id,
        email: res.email,
        role: res.role,
        full_name: res.full_name,
        is_verified: res.is_verified,
        profile: { full_name: res.full_name }
      };
      API.setUser(this.currentUser);
      this.updateAuthUI();

      if (res.is_verified) {
        this.showToast(`Registration verified automatically with VSCMS roster! Welcome, ${res.full_name}!`, "success");
      } else {
        this.showToast(`Registration submitted! Verification status: Pending Institutional Verification.`, "warning");
      }

      window.location.hash = "#home";
      this.activeView = "home";
      this.showView("home");
      try {
        await this.checkAuth();
      } catch (e) {}

    } catch (err) {
      this.showRegAlert(err.message || "Registration failed. Please check your details.", "danger");
    } finally {
      if (btn) btn.disabled = false;
      if (spinner) spinner.classList.add("d-none");
    }
  },

  async demoLogin(role) {
    let credentials = {};
    if (role === "alumni") {
      credentials = { email: "aarav.sharma@microsoft.com", password: "Alumni@CMS2025" };
    } else if (role === "student") {
      credentials = { email: "priya.patel@cmskanpur.edu.in", password: "Student@CMS2025" };
    } else if (role === "admin") {
      credentials = { email: "admin@cmskanpur.edu.in", password: "Admin@CMS2025" };
    }

    this.showAuthAlert(`Signing in with verified ${role.toUpperCase()} credentials...`, "warning");

    try {
      const res = await API.post("/api/auth/login", credentials);
      API.setToken(res.access_token);
      this.currentUser = {
        user_id: res.user_id,
        email: res.email,
        role: res.role,
        full_name: res.full_name,
        is_verified: res.is_verified,
        profile: { full_name: res.full_name }
      };
      API.setUser(this.currentUser);
      this.updateAuthUI();
      this.showAuthAlert(`Access Granted for ${res.full_name} (${role.toUpperCase()})! Redirecting...`, "success");
      const targetView = ["admin", "super_admin", "faculty"].includes(res.role) ? "admin" : "home";
      setTimeout(async () => {
        window.location.hash = `#${targetView}`;
        this.activeView = targetView;
        this.showView(targetView);
        try {
          await this.checkAuth();
        } catch (e) {}
      }, 350);
    } catch (err) {
      this.showAuthAlert(err.message || "Demo login failed.", "danger");
    }
  },

  openForgotPasswordModal() {
    document.getElementById("forgot-step-1")?.classList.remove("d-none");
    document.getElementById("forgot-step-2")?.classList.add("d-none");
    const alert1 = document.getElementById("forgot-alert-1");
    if (alert1) alert1.classList.add("d-none");
    const alert2 = document.getElementById("forgot-alert-2");
    if (alert2) alert2.classList.add("d-none");
    const modalEl = document.getElementById("modal-forgot-password");
    if (modalEl) new bootstrap.Modal(modalEl).show();
  },

  async requestPasswordReset(e) {
    e.preventDefault();
    const email = document.getElementById("forgot-email")?.value.trim();
    if (!email) return;

    const btn = document.getElementById("btn-forgot-step1");
    if (btn) btn.disabled = true;

    try {
      const res = await API.post("/api/auth/forgot-password", { email });
      document.getElementById("forgot-step-1")?.classList.add("d-none");
      document.getElementById("forgot-step-2")?.classList.remove("d-none");
      if (res.simulated_reset_code) {
        const codeInput = document.getElementById("forgot-code");
        if (codeInput) codeInput.value = res.simulated_reset_code;
      }
    } catch (err) {
      const alert1 = document.getElementById("forgot-alert-1");
      if (alert1) {
        alert1.innerText = err.message || "Failed to process request.";
        alert1.classList.remove("d-none");
      }
    } finally {
      if (btn) btn.disabled = false;
    }
  },

  async confirmPasswordReset(e) {
    e.preventDefault();
    const email = document.getElementById("forgot-email")?.value.trim();
    const reset_code = document.getElementById("forgot-code")?.value.trim();
    const new_password = document.getElementById("forgot-new-password")?.value;

    const btn = document.getElementById("btn-forgot-step2");
    if (btn) btn.disabled = true;

    try {
      const res = await API.post("/api/auth/reset-password", { email, reset_code, new_password });
      const modalEl = document.getElementById("modal-forgot-password");
      if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
      }
      this.showToast(res.message || "Password successfully reset! You can now log in.", "success");
      this.switchAuthTab("login");
      const idInput = document.getElementById("auth-login-identifier");
      if (idInput) idInput.value = email;
    } catch (err) {
      const alert2 = document.getElementById("forgot-alert-2");
      if (alert2) {
        alert2.innerText = err.message || "Invalid or expired reset code.";
        alert2.classList.remove("d-none");
      }
    } finally {
      if (btn) btn.disabled = false;
    }
  },

  showPolicyModal(type) {
    const modalEl = document.getElementById("modal-policy");
    const bodyEl = document.getElementById("modal-policy-body");
    const titleEl = document.getElementById("modalPolicyLabel");
    if (!modalEl || !bodyEl) return;

    if (type === "privacy") {
      titleEl.innerText = "VSCMS Privacy Policy";
      bodyEl.innerHTML = `
        <h6 class="fw-bold text-dark mb-2">Data Privacy & Alumni Confidentiality</h6>
        <p>Dr. Virendra Swarup College of Management Studies (VSCMS) is committed to protecting student and alumni privacy. All registration details, roll numbers, and contact information are strictly utilized for verified collegiate networking, mentorship connections, and placement referrals.</p>
        <p>No alumni personal data is exposed to unauthorized or unauthenticated external parties.</p>
      `;
    } else if (type === "terms") {
      titleEl.innerText = "Terms of Service";
      bodyEl.innerHTML = `
        <h6 class="fw-bold text-dark mb-2">Terms of Portal Access</h6>
        <p>Access to the VSCMS BCA & MCA Alumni Portal is restricted to current students, verified alumni, and faculty members under AKTU Code 050. Users must maintain professional conduct across job referral channels and mentorship interactions.</p>
      `;
    } else if (type === "help") {
      titleEl.innerText = "Institutional Help & Support";
      bodyEl.innerHTML = `
        <h6 class="fw-bold text-dark mb-2">Portal Support Desk</h6>
        <p>For assistance with institutional registration, roster verification, or password resets, contact the CMS Computer Applications Department:</p>
        <ul>
          <li>Email: <strong>cmskanpur@hotmail.com</strong></li>
          <li>Helpline: <strong>+91 7570004005 / 8542030533</strong></li>
          <li>Location: McRobert Ganj, Kanpur, UP</li>
        </ul>
      `;
    } else if (type === "accessibility") {
      titleEl.innerText = "Accessibility Commitment";
      bodyEl.innerHTML = `
        <h6 class="fw-bold text-dark mb-2">Accessibility & Inclusivity</h6>
        <p>The VSCMS Alumni Portal is designed to adhere to WCAG 2.1 accessibility standards, featuring high-contrast typography, screen-reader friendly semantic layouts, and full keyboard navigation support.</p>
      `;
    }
    new bootstrap.Modal(modalEl).show();
  },

  async logout() {
    try {
      await API.post("/api/auth/logout");
    } catch (e) {}
    API.setToken(null);
    API.setUser(null);
    this.currentUser = null;
    this.updateAuthUI();
    this.showToast("You have been signed out. Please sign in to access alumni information.", "info");
    window.location.hash = "#auth";
  },

  requireLogin() {
    if (!this.currentUser) {
      this.showToast("Institutional Access Required: Please sign in or register to access alumni directory.", "warning");
      window.location.hash = "#auth";
      return false;
    }
    return true;
  },

  showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toastId = `toast-${Date.now()}`;
    const bgClass = type === "success" ? "bg-success" : type === "danger" ? "bg-danger" : type === "warning" ? "bg-warning text-dark" : "bg-dark";

    const toastHtml = `
      <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0 shadow" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-body">${message}</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
      </div>
    `;
    container.insertAdjacentHTML("beforeend", toastHtml);
    const toastEl = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
    toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
  },

  escape(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  },

  timeAgo(dateStr) {
    const d = new Date(dateStr);
    const now = new Date();
    const seconds = Math.floor((now - d) / 1000);
    if (seconds < 60) return "just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }
};

// Initialize application on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  App.init();
});
