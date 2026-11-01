const API_BASE_URL = "http://localhost:8000";


function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function getDishEmoji(name) {
    const text = String(name || "").toLowerCase();

    if (text.includes("pizza")) return "🍕";
    if (text.includes("burger")) return "🍔";
    if (text.includes("coffee")) return "☕";
    if (text.includes("tea")) return "🍵";
    if (text.includes("sandwich") || text.includes("melt")) return "🥪";
    if (text.includes("cake") || text.includes("cheesecake")) return "🍰";
    if (text.includes("chips") || text.includes("fries")) return "🍟";
    if (text.includes("chicken") || text.includes("dark")) return "🍗";
    if (text.includes("roll") || text.includes("sushi")) return "🍣";
    if (text.includes("katsu") || text.includes("teriyaki")) return "🍱";
    if (text.includes("taco")) return "🌮";
    if (text.includes("mocktail") || text.includes("cocktail")) return "🍹";
    if (text.includes("drink") || text.includes("cola")) return "🥤";

    return "🍽️";
}


function showState(state) {
    document.getElementById("loadingState").hidden = state !== "loading";
    document.getElementById("errorState").hidden = state !== "error";
    document.getElementById("emptyState").hidden = state !== "empty";
}


function renderRecommendations(recommendations) {
    const container = document.getElementById("recommendationsList");
    container.innerHTML = "";

    if (!recommendations || recommendations.length === 0) {
        showState("empty");
        return;
    }

    showState("recommendations");

    recommendations.forEach((rec, index) => {
        const card = document.createElement("article");
        card.className = "recommendation-card";

        const emoji = getDishEmoji(rec.dish_name);
        const score = Number(rec.score || 0).toFixed(2);

        const imageHtml = rec.image_url
            ? `<img
                    src="${escapeHtml(rec.image_url)}"
                    alt="${escapeHtml(rec.dish_name || 'Dish')}"
                    loading="lazy"
                    onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
               >
               <span class="recommendation-image-fallback" style="display:none;">
                   ${emoji}
               </span>`
            : emoji;

        card.innerHTML = `
            <div class="rank-badge">#${index + 1}</div>

            <div class="recommendation-image">
                ${imageHtml}
            </div>

            <div class="recommendation-name">
                ${escapeHtml(rec.dish_name || "Dish")}
            </div>

            <div class="recommendation-meta">
                <span class="score-label">Match score</span>
                <span class="score-value">★ ${score}</span>
            </div>

            <div class="recommendation-actions">
                <button
                    class="view-dish-button"
                    onclick="viewDish(${Number(rec.dish_id)})"
                >
                    View Dish
                </button>
            </div>
        `;

        container.appendChild(card);
    });
}


function viewDish(dishId) {
    window.location.href = `index.html`;
}


async function loadRecommendations() {
    showState("loading");

    const savedUser = localStorage.getItem("foodexpress_user");

    if (!savedUser) {
        window.location.href = "auth.html";
        return;
    }

    let currentUser;

    try {
        currentUser = JSON.parse(savedUser);
    } catch (error) {
        console.error("Invalid user data:", error);
        localStorage.removeItem("foodexpress_user");
        window.location.href = "auth.html";
        return;
    }

    if (!currentUser || !currentUser.id) {
        window.location.href = "auth.html";
        return;
    }

    document.getElementById("userGreeting").textContent =
        `Personalized picks for ${currentUser.name || currentUser.username}`;

    try {
        const response = await fetch(
            `${API_BASE_URL}/users/${Number(currentUser.id)}/recommendations?limit=20`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Failed to load recommendations");
        }

        renderRecommendations(data.recommendations || []);

    } catch (error) {
        console.error("Failed to load recommendations:", error);

        const errorState = document.getElementById("errorState");
        errorState.textContent =
            error.message || "Failed to load recommendations.";

        showState("error");
    }
}


document.addEventListener("DOMContentLoaded", loadRecommendations);