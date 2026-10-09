const API_BASE_URL = "http://localhost:8000";

let restaurants = [];
let currentCategory = "all";

async function loadRestaurants() {

    showLoading();

    try {

        const response = await fetch(
            `${API_BASE_URL}/restaurants?limit=100`
        );

        if (!response.ok) {
            throw new Error(
                `HTTP error: ${response.status}`
            );
        }

        const result = await response.json();

        restaurants = result.data || [];

        renderRestaurants(restaurants);

    } catch (error) {

        console.error(
            "Failed to load restaurants:",
            error
        );

        showError();

    }
}

function renderRestaurants(data) {

    const container =
        document.getElementById("restaurants");

    const loading =
        document.getElementById("loading");

    const error =
        document.getElementById("error");

    const resultInfo =
        document.getElementById("resultInfo");


    loading.style.display = "none";
    error.style.display = "none";


    container.innerHTML = "";


    if (!data.length) {

        container.innerHTML = `
            <div class="error-message">
                <strong>No restaurants found.</strong>
                <p>Try another search.</p>
            </div>
        `;

        resultInfo.textContent = "0 restaurants";

        return;
    }


    resultInfo.textContent =
        `${data.length} restaurants`;


    data.forEach(restaurant => {

        const card =
            createRestaurantCard(restaurant);

        container.appendChild(card);

    });
}

function createRestaurantCard(restaurant) {

    const card =
        document.createElement("article");

    card.className = "restaurant-card";


    const rating =
        restaurant.rating !== null &&
        restaurant.rating !== undefined
            ? Number(restaurant.rating).toFixed(1)
            : "New";


    const ratingCount =
        restaurant.rating_count || 0;


    const price =
        restaurant.price_range || "$$";


    const category =
        restaurant.category || "Restaurant";


    const address =
        restaurant.address || "Address unavailable";


    card.innerHTML = `

        <div class="restaurant-image">
            ${
                restaurant.image_url
                    ? `<img
                        src="${escapeHtml(restaurant.image_url)}"
                        alt="${escapeHtml(restaurant.name)}"
                        loading="lazy"
                        onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                       >
                       <span class="restaurant-image-fallback" style="display:none;">
                           ${getRestaurantEmoji(category)}
                       </span>`
                    : getRestaurantEmoji(category)
            }
        </div>

        <div class="restaurant-content">

            <h3 class="restaurant-name">
                ${escapeHtml(restaurant.name)}
            </h3>

            <div class="restaurant-category">
                ${escapeHtml(category)}
            </div>

            <div class="restaurant-meta">

                <span class="rating">
                    ★ ${rating}
                </span>

                ${
                    ratingCount > 0
                        ? `<span class="rating-count">
                            (${ratingCount})
                           </span>`
                        : ""
                }

                <span class="price">
                    ${escapeHtml(price)}
                </span>

            </div>

            <div class="restaurant-address">
                📍 ${escapeHtml(address)}
            </div>

        </div>
    `;


    card.addEventListener(
        "click",
        () => openRestaurant(restaurant.id)
    );


    return card;
}


function getRestaurantEmoji(category) {

    const text =
        String(category).toLowerCase();


    if (text.includes("pizza")) {
        return "🍕";
    }

    if (
        text.includes("burger") ||
        text.includes("american")
    ) {
        return "🍔";
    }

    if (
        text.includes("coffee") ||
        text.includes("tea")
    ) {
        return "☕";
    }

    if (
        text.includes("sandwich") ||
        text.includes("cheesesteak")
    ) {
        return "🥪";
    }

    if (
        text.includes("chinese") ||
        text.includes("asian") ||
        text.includes("thai") ||
        text.includes("japanese")
    ) {
        return "🍜";
    }

    if (
        text.includes("breakfast") ||
        text.includes("brunch")
    ) {
        return "🥞";
    }

    return "🍽️";
}

function searchRestaurants(query) {

    const normalized =
        query.trim().toLowerCase();


    let filtered =
        restaurants;


    if (normalized) {

        filtered =
            restaurants.filter(restaurant => {

                const name =
                    String(
                        restaurant.name || ""
                    ).toLowerCase();

                const category =
                    String(
                        restaurant.category || ""
                    ).toLowerCase();

                const address =
                    String(
                        restaurant.address || ""
                    ).toLowerCase();


                return (
                    name.includes(normalized) ||
                    category.includes(normalized) ||
                    address.includes(normalized)
                );

            });

    }


    if (currentCategory !== "all") {

        filtered =
            filtered.filter(
                restaurant =>
                    matchesCategory(
                        restaurant,
                        currentCategory
                    )
            );

    }


    renderRestaurants(filtered);
}
function matchesCategory(
    restaurant,
    category
) {

    const text = `
        ${restaurant.name || ""}
        ${restaurant.category || ""}
    `.toLowerCase();


    const keywords = {

        pizza: [
            "pizza"
        ],

        burger: [
            "burger"
        ],

        asian: [
            "asian",
            "chinese",
            "japanese",
            "thai"
        ],

        coffee: [
            "coffee",
            "tea"
        ],

        sandwich: [
            "sandwich",
            "cheesesteak"
        ]

    };


    return (
        keywords[category] || []
    ).some(
        keyword =>
            text.includes(keyword)
    );
}


   function openRestaurant(id) {
    window.location.href = `restaurant.html?id=${id}`;
}


function showLoading() {

    document.getElementById(
        "loading"
    ).style.display = "flex";

    document.getElementById(
        "error"
    ).style.display = "none";

    document.getElementById(
        "restaurants"
    ).innerHTML = "";
}


function showError() {

    document.getElementById(
        "loading"
    ).style.display = "none";

    document.getElementById(
        "error"
    ).style.display = "block";

    document.getElementById(
        "restaurants"
    ).innerHTML = "";

    document.getElementById(
        "resultInfo"
    ).textContent = "Error";
}

function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadRestaurants();


        const searchInput =
            document.getElementById(
                "searchInput"
            );


        const heroSearchInput =
            document.getElementById(
                "heroSearchInput"
            );


        const heroSearchButton =
            document.getElementById(
                "heroSearchButton"
            );


        searchInput.addEventListener(
            "input",
            event => {

                heroSearchInput.value =
                    event.target.value;

                searchRestaurants(
                    event.target.value
                );

            }
        );


        heroSearchInput.addEventListener(
            "input",
            event => {

                searchInput.value =
                    event.target.value;

                searchRestaurants(
                    event.target.value
                );

            }
        );


        heroSearchButton.addEventListener(
            "click",
            () => {

                searchRestaurants(
                    heroSearchInput.value
                );

            }
        );


        document
            .getElementById("retryButton")
            .addEventListener(
                "click",
                loadRestaurants
            );


        document
            .querySelectorAll(".category")
            .forEach(button => {

                button.addEventListener(
                    "click",
                    () => {

                        document
                            .querySelectorAll(
                                ".category"
                            )
                            .forEach(
                                item =>
                                    item.classList.remove(
                                        "active"
                                    )
                            );


                        button.classList.add(
                            "active"
                        );


                        currentCategory =
                            button.dataset.category;


                        searchRestaurants(
                            searchInput.value
                        );

                    }
                );

            });

    }
);

function updateAuthUI() {
    const authArea = document.getElementById("authArea");

    if (!authArea) {
        return;
    }

    const savedUser = localStorage.getItem("foodexpress_user");

    if (!savedUser) {
        authArea.innerHTML = `
            <a href="auth.html" class="nav-link">
                Login / Register
            </a>
        `;
        return;
    }

    try {
        const user = JSON.parse(savedUser);

        const displayName =
            user.name ||
            user.username ||
            "User";

        authArea.innerHTML = `
            <span class="welcome-user">
                Welcome, ${escapeHtml(displayName)}
            </span>
            <button
                class="logout-button"
                onclick="logout()"
            >
                Logout
            </button>
        `;
    } catch (error) {
        console.error("Failed to read user session:", error);

        localStorage.removeItem("foodexpress_user");

        authArea.innerHTML = `
            <a href="auth.html" class="nav-link">
                Login / Register
            </a>
        `;
    }
}

function logout() {
    localStorage.removeItem("foodexpress_user");
    window.location.reload();
}

updateAuthUI();