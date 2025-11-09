

document.getElementById("signinForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!email || !password) {
        alert("Please fill in both fields.");
        return;
    }

    try {
        const res = await fetch(`/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ username: email, password }),
        });

        if (!res.ok) throw new Error("Invalid email or password");

        const data = await res.json();
        saveTokens(data);

        alert("Signed in successfully!");
        window.location.href = "/html/feed.html";
    } catch (err) {
        alert("Error: " + err.message);
    }
});


/* Code for login. This should be imported for most pages. */
// ---- Config ----
const LOGIN_URL = "/html/signin.html"; // adjust if your login route differs

// ---- Token helpers ----
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

// ---- Refresh flow ----
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

// ---- Authenticated fetch with single retry on 401 ----
async function fetchWithAuth(input, init = {}) {
    let { access, refresh } = getTokens();
    if (!access || !refresh) redirectToLogin();

    // First attempt with current access token
    const first = await fetch(input, withAuth(init, access));
    if (first.status !== 401) return first;

    // If unauthorized, try refreshing
    try {
        const newAccess = await refreshAccessToken(refresh);
        const second = await fetch(input, withAuth(init, newAccess));
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

// async function loadFeed() {
//   const out = document.getElementById("feedOut");
//   const { access, refresh } = getTokens();
//   if (!access || !refresh) return redirectToLogin();

//   try {
//     const res = await fetchWithAuth(`/feed`, { method: "GET" });
//     if (!res.ok) {
//       if (res.status === 401) redirectToLogin();
//       throw new Error(`HTTP ${res.status}`);
//     }
//     const data = await res.json();
//     out.textContent = JSON.stringify(data, null, 2);
//   } catch (err) {
//     out.textContent = `Error: ${err.message}`;
//   }
// }

// // Boot
// loadFeed();



/* Code in /html/login.html */
// async function loginAndSave(username, password) {
//   const res = await fetch(`/auth/login`, {
//     method: "POST",
//     headers: { "Content-Type": "application/x-www-form-urlencoded" },
//     body: new URLSearchParams({ username, password }),
//   });
//   if (!res.ok) throw new Error("Invalid credentials");
//   const data = await res.json();
//   saveTokens(data);
//   // redirect to your app shell after login
//   window.location.replace("/");
// }