const LOGIN_URL = "/html/signin.html";

// ---- Token Management ----
function getTokens() {
    return {
        access: localStorage.getItem("access_token"),
        refresh: localStorage.getItem("refresh_token"),
    };
}
function saveTokens(tokens) {
    if (tokens.access_token) localStorage.setItem("access_token", tokens.access_token);
    if (tokens.refresh_token) localStorage.setItem("refresh_token", tokens.refresh_token);
}
function clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
}
function redirectToLogin() {
    clearTokens();
    window.location.replace(LOGIN_URL);
}

// ---- Refresh ----
async function refreshAccessToken(refreshToken) {
    const res = await fetch(`/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ refresh_token: refreshToken }),
    });
    if (!res.ok) throw new Error("Failed to refresh token");
    const tokens = await res.json();
    saveTokens(tokens);
    return tokens.access_token;
}

// ---- Auth Fetch ----
async function fetchWithAuth(input, init = {}) {
    const { access, refresh } = getTokens();
    if (!access || !refresh) redirectToLogin();

    let res = await fetch(input, {
        ...init,
        headers: { ...(init.headers || {}), Authorization: `Bearer ${access}`, 'Content-Type': 'application/json' },
    });

    console.log(`fetchWithAuth called ${input}`)

    if (res.status !== 401) return res;

    try {
        const newAccess = await refreshAccessToken(refresh);
        res = await fetch(input, {
            ...init,
            headers: { ...(init.headers || {}), Authorization: `Bearer ${newAccess}`, 'Content-Type': 'application/json' },
        });
        console.log(`fetchWithAuth called with refresh ${input}`)
    } catch {
        redirectToLogin();
    }
    return res;
}
