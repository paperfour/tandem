const LOGIN_URL = "/html/login.html"

function getTokens() {
    const access = localStorage.getItem("access_token");
    const refresh = localStorage.getItem("refresh_token");
    return { access, refresh };
}

function saveTokens({ access_token, refresh_token }) {
    if (access_token) localStorage.setItem("access_token", access_token);
    if (refresh_token) localStorage.setItem("refresh_token", refresh_token);
}

function clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
}
function redirectToLogin() {
    clearTokens();
    window.location.replace(LOGIN_URL);
}

async function refreshAccessToken(refreshToken) {
    // FastAPI endpoint expects x-www-form-urlencoded with "refresh_token"
    const res = await fetch(`/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ refresh_token: refreshToken })
    });

    if (!res.ok) throw new Error("Refresh failed");
    const data = await res.json();
    // Expected: { access_token, refresh_token, token_type, expires_in }
    saveTokens(data);
    return data.access_token;
}

async function fetchWithAuth(endpoint, init = {}) {
    let { access, refresh } = getTokens();
    if (!access || !refresh) redirectToLogin();

    // First attempt with current access token
    const first = await fetch(endpoint, withAuth(init, access));
    if (first.status !== 401) return first;

    // If unauthorized, try refreshing
    try {
        const newAccess = await refreshAccessToken(refresh);
        const second = await fetch(endpoint, withAuth(init, newAccess));
        if (second.status === 401) throw new Error("Unauthorized after refresh");
        return second;
    } catch (e) {
        redirectToLogin();
        // Return a never-resolving promise to stop callers; or throw.
        return new Promise(() => { });
    }
}

function withAuth(init, token) {
    const headers = new Headers(init && init.headers ? init.headers : undefined);
    headers.set("Authorization", `Bearer ${token}`);
    return { ...init, headers };
}

// ---- Example usage: call a protected endpoint (/me) ----
async function loadProtectedData() {
    const out = document.getElementById("out");
    const { access, refresh } = getTokens();
    if (!access || !refresh) return redirectToLogin();

    try {
        const res = await fetchWithAuth(`/me`, { method: "GET" });
        if (!res.ok) {
            if (res.status === 401) redirectToLogin();
            throw new Error(`HTTP ${res.status}`);
        }
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
        out.textContent = `Error: ${err.message}`;
    }
}

let cur_user_res = await fetch("/get_current_user", {
    method: "GET",
    headers: {
        "Authorization": "Bearer <ACCESS_TOKEN>"
    }
})

let user_data = await cur_user_res.json()
let courses_res = await fetch(`/get_courses_for_student/${user_data.id}`)
let courses = await courses_res.json()

let appointments_to_show = []

for (let c of courses) {
    let appointments = await fetch(`/get_appointments_for_course/${c.id}`)
    appointments_to_show.concat(await appointments.json())
}

