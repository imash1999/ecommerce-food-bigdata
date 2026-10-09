const API_BASE_URL = "http://localhost:8000";

function showLogin() {
    document.getElementById("loginForm").classList.remove("hidden");
    document.getElementById("registerForm").classList.add("hidden");

    document.getElementById("loginTab").classList.add("active");
    document.getElementById("registerTab").classList.remove("active");

    clearMessages();
}

function showRegister() {
    document.getElementById("loginForm").classList.add("hidden");
    document.getElementById("registerForm").classList.remove("hidden");

    document.getElementById("loginTab").classList.remove("active");
    document.getElementById("registerTab").classList.add("active");

    clearMessages();
}

function clearMessages() {
    document.getElementById("loginMessage").textContent = "";
    document.getElementById("registerMessage").textContent = "";

    document.getElementById("loginMessage").className = "message";
    document.getElementById("registerMessage").className = "message";
}


function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);

    element.textContent = message;
    element.className = `message ${type}`;
}

document.getElementById("loginForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value;

    try {
        const response = await fetch(
            `${API_BASE_URL}/auth/login?` +
            new URLSearchParams({
                username: username,
                password: password
            }),
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            showMessage(
                "loginMessage",
                data.detail || "Login failed",
                "error"
            );
            return;
        }
        localStorage.setItem(
            "foodexpress_user",
            JSON.stringify(data.user)
        );

        showMessage(
            "loginMessage",
            "Login successful!",
            "success"
        );

        setTimeout(() => {
            window.location.href = "index.html";
        }, 700);

    } catch (error) {
        console.error(error);

        showMessage(
            "loginMessage",
            "Cannot connect to server.",
            "error"
        );
    }
});

document.getElementById("registerForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const name = document.getElementById("registerName").value.trim();
    const username = document.getElementById("registerUsername").value.trim();
    const email = document.getElementById("registerEmail").value.trim();
    const password = document.getElementById("registerPassword").value;

    try {
        const response = await fetch(
            `${API_BASE_URL}/auth/register?` +
            new URLSearchParams({
                name: name,
                username: username,
                email: email,
                password: password
            }),
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            showMessage(
                "registerMessage",
                data.detail || "Registration failed",
                "error"
            );
            return;
        }

        showMessage(
            "registerMessage",
            "Registration successful! You can now login.",
            "success"
        );

        document.getElementById("registerForm").reset();

        setTimeout(() => {
            showLogin();

            document.getElementById("loginUsername").value = username;
        }, 1000);

    } catch (error) {
        console.error(error);

        showMessage(
            "registerMessage",
            "Cannot connect to server.",
            "error"
        );
    }
});
