const API_BASE_URL = "http://localhost:8000";

let restaurant = null;
let dishes = [];

let activeCategory = "all";
let cart = loadCart();

function getRestaurantId() {

    const params =
        new URLSearchParams(
            window.location.search
        );

    return params.get("id");
}

async function loadRestaurant() {

    const restaurantId =
        getRestaurantId();


    if (!restaurantId) {
        showError();
        return;
    }


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/restaurants/${restaurantId}`
            );


        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        restaurant =
            data.restaurant;

        dishes =
            data.menu || [];


        renderRestaurant();

        renderCategories();

        renderDishes(dishes);


        document.getElementById(
            "restaurantLoading"
        ).style.display = "none";


        document.getElementById(
            "restaurantPage"
        ).style.display = "block";


    } catch (error) {

        console.error(
            "Failed to load restaurant:",
            error
        );

        showError();

    }
}

function renderRestaurant() {

    document.title =
        `${restaurant.name} - FoodExpress`;


    document.getElementById(
        "restaurantName"
    ).textContent =
        restaurant.name;


    document.getElementById(
        "restaurantCategory"
    ).textContent =
        restaurant.category ||
        "Restaurant";


    const rating =
        restaurant.rating !== null &&
        restaurant.rating !== undefined
            ? Number(
                restaurant.rating
              ).toFixed(1)
            : "New";


    const ratingCount =
        restaurant.rating_count || 0;


    document.getElementById(
        "restaurantRating"
    ).textContent =
        ratingCount > 0
            ? `★ ${rating} (${ratingCount})`
            : `★ ${rating}`;


    document.getElementById(
        "restaurantPrice"
    ).textContent =
        restaurant.price_range ||
        "$$";


    document.getElementById(
        "restaurantAddress"
    ).textContent =
        `📍 ${
            restaurant.address ||
            "Address unavailable"
        }`;
}

function renderCategories() {

    const container =
        document.getElementById(
            "menuCategories"
        );


    const categories =
        new Map();


    dishes.forEach(dish => {

        if (!categories.has(
            dish.category_id
        )) {

            categories.set(
                dish.category_id,
                `Category ${dish.category_id}`
            );

        }

    });


    container.innerHTML = `

        <button
            class="menu-category active"
            data-category="all"
        >
            All dishes
        </button>

    `;


    categories.forEach(
        (name, categoryId) => {

            const button =
                document.createElement(
                    "button"
                );


            button.className =
                "menu-category";


            button.dataset.category =
                categoryId;


            button.textContent =
                name;


            button.addEventListener(
                "click",
                () => {

                    document
                        .querySelectorAll(
                            ".menu-category"
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


                    activeCategory =
                        categoryId;


                    renderDishes(
                        getFilteredDishes()
                    );

                }
            );


            container.appendChild(
                button
            );

        }
    );


    const allButton =
        container.querySelector(
            '[data-category="all"]'
        );


    allButton.addEventListener(
        "click",
        () => {

            document
                .querySelectorAll(
                    ".menu-category"
                )
                .forEach(
                    item =>
                        item.classList.remove(
                            "active"
                        )
                );


            allButton.classList.add(
                "active"
            );


            activeCategory =
                "all";


            renderDishes(
                getFilteredDishes()
            );

        }
    );
}

function getFilteredDishes() {

    if (activeCategory === "all") {
        return dishes;
    }


    return dishes.filter(
        dish =>
            String(dish.category_id) ===
            String(activeCategory)
    );
}

function renderDishes(data) {

    const container =
        document.getElementById(
            "menuGrid"
        );


    const count =
        document.getElementById(
            "dishCount"
        );


    const title =
        document.getElementById(
            "menuTitle"
        );


    container.innerHTML = "";


    count.textContent =
        `${data.length} dishes`;


    title.textContent =
        activeCategory === "all"
            ? "All dishes"
            : `Category ${activeCategory}`;


    if (!data.length) {

        container.innerHTML = `
            <div class="error-message">
                <strong>
                    No dishes found.
                </strong>
            </div>
        `;

        return;
    }


    data.forEach(dish => {

        container.appendChild(
            createDishCard(dish)
        );

    });
}

function createDishCard(dish) {

    const card =
        document.createElement("article");


    card.className =
        "dish-card";


    const description =
        dish.description ||
        "No description available.";


    const price =
        Number(dish.price || 0)
            .toFixed(2);


    card.innerHTML = `

        <div class="dish-info">

            <h3 class="dish-name">
                ${escapeHtml(dish.name)}
            </h3>

            <p class="dish-description">
                ${escapeHtml(description)}
            </p>

            <div class="dish-bottom">

                <span class="dish-price">
                    $${price}
                </span>

                <button
                    class="add-dish"
                    title="Add to cart"
                >
                    +
                </button>

            </div>

        </div>

        <div class="dish-image">
            ${
                dish.image_url
                    ? `<img
                        src="${escapeHtml(dish.image_url)}"
                        alt="${escapeHtml(dish.name)}"
                        loading="lazy"
                        onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                       >
                       <span class="dish-image-fallback" style="display:none;">
                           ${getDishEmoji(dish.name)}
                       </span>`
                    : getDishEmoji(dish.name)
            }
        </div>

    `;


    const button =
        card.querySelector(
            ".add-dish"
        );


    button.addEventListener(
        "click",
        event => {

            event.stopPropagation();

            addToCart(dish);

        }
    );


    return card;
}

function getDishEmoji(name) {

    const text =
        String(name).toLowerCase();


    if (
        text.includes("pizza") ||
        text.includes("stripper")
    ) {
        return "🍕";
    }


    if (
        text.includes("pasta") ||
        text.includes("spaghetti") ||
        text.includes("fettucine")
    ) {
        return "🍝";
    }


    if (
        text.includes("burger")
    ) {
        return "🍔";
    }


    if (
        text.includes("salad")
    ) {
        return "🥗";
    }


    if (
        text.includes("nacho") ||
        text.includes("dip")
    ) {
        return "🌮";
    }


    if (
        text.includes("pretzel")
    ) {
        return "🥨";
    }


    if (
        text.includes("drink")
    ) {
        return "🥤";
    }


    if (
        text.includes("cookie") ||
        text.includes("dessert")
    ) {
        return "🍪";
    }


    return "🍽️";
}

function searchDishes(query) {

    const normalized =
        query.trim().toLowerCase();


    let filtered =
        getFilteredDishes();


    if (normalized) {

        filtered =
            filtered.filter(dish => {

                const name =
                    String(
                        dish.name || ""
                    ).toLowerCase();


                const description =
                    String(
                        dish.description || ""
                    ).toLowerCase();


                return (
                    name.includes(normalized) ||
                    description.includes(normalized)
                );

            });

    }


    renderDishes(filtered);
}

   function loadCart() {

    try {

        const saved =
            localStorage.getItem(
                "foodexpress_cart"
            );

        return saved
            ? JSON.parse(saved)
            : [];

    } catch (error) {

        console.error(
            "Failed to load cart:",
            error
        );

        return [];
    }
}


function saveCart() {

    localStorage.setItem(
        "foodexpress_cart",
        JSON.stringify(cart)
    );
}

   function addToCart(dish) {

    const existing = cart.find(
        item => item.dish.id === dish.id
    );

    if (existing) {
        existing.quantity++;
    } else {
        cart.push({
            dish: dish,
            quantity: 1
        });
    }

    saveCart();

    updateCartBar();
}


function updateCartBar() {

    const bar =
        document.getElementById(
            "cartBar"
        );


    const cartCount =
        document.getElementById(
            "cartCount"
        );


    const itemsCount =
        cart.reduce(
            (total, item) =>
                total + item.quantity,
            0
        );


    const total =
        cart.reduce(
            (sum, item) =>
                sum +
                (
                    Number(item.dish.price) *
                    item.quantity
                ),
            0
        );


    cartCount.textContent =
        itemsCount;


    document.getElementById(
        "cartItemsCount"
    ).textContent =
        `${itemsCount} ${
            itemsCount === 1
                ? "item"
                : "items"
        }`;


    document.getElementById(
        "cartTotal"
    ).textContent =
        `$${total.toFixed(2)}`;


    bar.style.display =
        itemsCount > 0
            ? "flex"
            : "none";
}

function showError() {

    document.getElementById(
        "restaurantLoading"
    ).style.display = "none";


    document.getElementById(
        "restaurantPage"
    ).style.display = "none";


    document.getElementById(
        "restaurantError"
    ).style.display = "block";
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

        loadRestaurant();


        document
            .getElementById("menuSearch")
            .addEventListener(
                "input",
                event => {

                    searchDishes(
                        event.target.value
                    );

                }
            );

    }
);
