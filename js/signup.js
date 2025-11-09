

document.getElementById("signupForm").addEventListener("submit", async function (e) {
    e.preventDefault();
    console.log("AHHHHH");

    const name = document.getElementById("fullname").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!name || !email || !password) {
        alert("Please fill in all required fields.");
        return;
    }

    const payload = {
        name,
        email,
        password,
    };

    try {
        const res = await fetch(`/create_student/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!res.ok) throw new Error("Failed to sign up");
        alert("Account created successfully!");
        window.location.href = "/html/signin.html";
    } catch (err) {
        alert("Error: " + err.message);
    }
});
