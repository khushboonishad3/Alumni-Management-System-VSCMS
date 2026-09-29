// CMS AlumniConnect API Client
const API = {
  getToken() {
    return localStorage.getItem("cms_auth_token") || null;
  },

  setToken(token) {
    if (token) {
      localStorage.setItem("cms_auth_token", token);
    } else {
      localStorage.removeItem("cms_auth_token");
    }
  },

  getUser() {
    const u = localStorage.getItem("cms_user");
    return u ? JSON.parse(u) : null;
  },

  setUser(user) {
    if (user) {
      localStorage.setItem("cms_user", JSON.stringify(user));
    } else {
      localStorage.removeItem("cms_user");
    }
  },

  async request(url, options = {}) {
    const token = this.getToken();
    const headers = options.headers || {};

    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);
      const isJson = (response.headers.get("content-type") || "").includes("application/json");
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        let errorMsg = "An unexpected error occurred.";
        if (typeof data === "object" && data.detail) {
          if (Array.isArray(data.detail)) {
            errorMsg = data.detail.map(d => `${d.loc ? d.loc.join('.') : ''}: ${d.msg}`).join(", ");
          } else {
            errorMsg = data.detail;
          }
        } else if (typeof data === "string") {
          errorMsg = data;
        }

        if (response.status === 401) {
          // Token expired or invalid
          console.warn("Session expired or unauthorized:", errorMsg);
        }
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      throw err;
    }
  },

  get(url) {
    return this.request(url, { method: "GET" });
  },

  post(url, body) {
    const isFormData = body instanceof FormData;
    return this.request(url, {
      method: "POST",
      body: isFormData ? body : JSON.stringify(body)
    });
  },

  put(url, body) {
    const isFormData = body instanceof FormData;
    return this.request(url, {
      method: "PUT",
      body: body ? (isFormData ? body : JSON.stringify(body)) : null
    });
  },

  delete(url) {
    return this.request(url, { method: "DELETE" });
  }
};
