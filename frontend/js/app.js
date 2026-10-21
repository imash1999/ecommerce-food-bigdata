const API_BASE_URL = "http://localhost:8000";

let restaurants = [];
let currentCategory = "all";

const PAGE_SIZE = 100;
let currentPage = 1;
let filteredRestaurants = [];

async function loadRestaurants() {
    showLoading();

    try {
        const response = await fetch(
            `${API_BASE_URL}/restaurants?limit=5000&offset=0`
        );

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        const result = await response.json();
        restaurants = result.data || [];

        searchRestaurants(
            document.getElementById("searchInput")?.value || ""
        );
    } catch (error) {
        console.error("Failed to load restaurants:", error);
        showError();
    }
}

function renderRestaurants(data) {
    const container = document.getElementById("restaurants");
    const loading = document.getElementById("loading");
    const error = document.getElementById("error");
    const resultInfo = document.getElementById("resultInfo");
    const pagination = document.getElementById("pagination");

    loading.style.display = "none";
    error.style.display = "none";
    container.innerHTML = "";

    filteredRestaurants = data;

    const totalPages = Math.max(
        1,
        Math.ceil(filteredRestaurants.length / PAGE_SIZE)
    );

    if (currentPage > totalPages) {
        currentPage = totalPages;
    }

    if (!filteredRestaurants.length) {
        container.innerHTML = `
            <div class="error-message">
                <strong>No restaurants found.</strong>
                <p>Try another search.</p>
            </div>
        `;

        resultInfo.textContent = "0 restaurants";
        pagination.innerHTML = "";
        pagination.style.display = "none";
        return;
    }

    const startIndex = (currentPage - 1) * PAGE_SIZE;
    const pageRestaurants = filteredRestaurants.slice(
        startIndex,
        startIndex + PAGE_SIZE
    );

    resultInfo.textContent =
        `Showing ${startIndex + 1}–${Math.min(
            startIndex + PAGE_SIZE,
            filteredRestaurants.length
        )} of ${filteredRestaurants.length} restaurants`;

    pageRestaurants.forEach(restaurant => {
        container.appendChild(createRestaurantCard(restaurant));
    });

    renderPagination(totalPages);
}

function renderPagination(totalPages) {
    const pagination = document.getElementById("pagination");
    pagination.innerHTML = "";

    if (totalPages <= 1) {
        pagination.style.display = "none";
        return;
    }

    pagination.style.display = "flex";

    function addButton(label, page, options = {}) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "page-button";
        button.textContent = label;
        button.disabled = Boolean(options.disabled);

        if (options.active) {
            button.classList.add("active");
            button.setAttribute("aria-current", "page");
        }

        button.addEventListener("click", () => {
            if (page === currentPage || button.disabled) {
                return;
            }

            currentPage = page;
            renderRestaurants(filteredRestaurants);

            document.querySelector(".restaurants-section")
                ?.scrollIntoView({ behavior: "smooth", block: "start" });
        });

        pagination.appendChild(button);
    }

    addButton("← Previous", currentPage - 1, {
        disabled: currentPage === 1
    });

    for (let page = 1; page <= totalPages; page++) {
        addButton(String(page), page, {
            active: page === currentPage
        });
    }

    addButton("Next →", currentPage + 1, {
        disabled: currentPage === totalPages
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
                           <img src="${getRestaurantIcon(category)}" alt="" width="64" height="64">
                       </span>`
                    : `<img class="restaurant-placeholder-icon" src="${getRestaurantIcon(category)}" alt="" width="64" height="64">`
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


function getRestaurantIcon(category) {
    const text = String(category || "").toLowerCase();

    if (text.includes("pizza")) return "images/icons/pizza.svg";
    if (text.includes("burger") || text.includes("american")) return "images/icons/burger.svg";
    if (text.includes("coffee") || text.includes("tea")) return "images/icons/coffee.svg";
    if (text.includes("sandwich") || text.includes("cheesesteak")) return "images/icons/sandwich.svg";
    if (
        text.includes("chinese") ||
        text.includes("asian") ||
        text.includes("thai") ||
        text.includes("japanese")
    ) return "images/icons/asian.svg";
    if (text.includes("breakfast") || text.includes("brunch")) {
        return "images/icons/breakfast.svg";
    }
    return "images/icons/restaurant.svg";
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


    currentPage = 1;
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


async function updateAuthUI() {
    const authArea = document.getElementById("authArea");

    if (!authArea) {
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE_URL}/auth/me`,
            {
                method: "GET",
                credentials: "include",
            }
        );

        if (response.status === 401) {
            localStorage.removeItem("foodexpress_user");

            authArea.innerHTML = `
                <a href="auth.html" class="nav-link">
                    Login / Register
                </a>
            `;
            return;
        }

        if (!response.ok) {
            throw new Error(
                `Authentication check failed: ${response.status}`
            );
        }

        const user = await response.json();

        localStorage.setItem(
            "foodexpress_user",
            JSON.stringify(user)
        );

        const displayName =
            user.name ||
            user.username ||
            "User";

        authArea.innerHTML = `
            <span class="welcome-user">
                Welcome, ${escapeHtml(displayName)}
            </span>

            ${
                user.is_admin === true
                    ? '<a href="admin.html" class="nav-link">Admin Panel</a>'
                    : ""
            }

            <button
                class="logout-button"
                onclick="logout()"
            >
                Logout
            </button>
        `;

    } catch (error) {
        console.error(
            "Failed to verify user session:",
            error
        );

        authArea.innerHTML = `
            <a href="auth.html" class="nav-link">
                Sign in again
            </a>
        `;
    }
}



async function logout() {
    try {
        const response = await fetch(
            `${API_BASE_URL}/auth/logout`,
            {
                method: "POST",
                credentials: "include",
            }
        );

        if (!response.ok) {
            throw new Error(
                `Logout failed: ${response.status}`
            );
        }

        localStorage.removeItem("foodexpress_user");
        window.location.reload();

    } catch (error) {
        console.error("Logout failed:", error);
        alert("Could not log out. Please try again.");
    }
}


updateAuthUI();