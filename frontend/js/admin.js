"use strict";

const API_BASE_URL = "http://localhost:8000";

const $ = (id) => document.getElementById(id);

let restaurants = [];
let dishes = [];
let selectedRestaurantId = null;

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

function notify(message, type = "success") {
    const element = $("notice");
    element.textContent = message;
    element.className = `notice visible ${type}`;
}

function clearNotice() {
    $("notice").className = "notice";
    $("notice").textContent = "";
}

async function api(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        credentials: "include",
        headers: {
            ...(options.body ? { "Content-Type": "application/json" } : {}),
            ...(options.headers || {})
        }
    });

    const text = await response.text();
    let data = null;

    if (text) {
        try {
            data = JSON.parse(text);
        } catch {
            data = { detail: text };
        }
    }

    if (response.status === 401 || response.status === 403) {
        throw new Error(
            response.status === 401
                ? "Authentication required. Log in with an administrator account."
                : "Access denied. This account does not have administrator rights."
        );
    }

    if (!response.ok) {
        throw new Error(data?.detail || `Request failed (${response.status})`);
    }

    return data;
}

function statusBadge(active) {
    return `<span class="status ${active ? "" : "off"}">${active ? "Active" : "Disabled"}</span>`;
}

function renderRestaurants() {
    const body = $("restaurantsBody");

    if (!restaurants.length) {
        body.innerHTML = '<tr><td colspan="5" class="empty">No restaurants found.</td></tr>';
        return;
    }

    body.innerHTML = restaurants.map((restaurant) => `
        <tr>
            <td>${restaurant.id}</td>
            <td>${escapeHtml(restaurant.name)}</td>
            <td>${escapeHtml(restaurant.category || "—")}</td>
            <td>${statusBadge(restaurant.is_active)}</td>
            <td class="actions">
                <button class="small" data-action="select-restaurant" data-id="${restaurant.id}">Dishes</button>
                <button class="small secondary" data-action="edit-restaurant" data-id="${restaurant.id}">Edit</button>
                ${restaurant.is_active
                    ? `<button class="small danger" data-action="disable-restaurant" data-id="${restaurant.id}">Disable</button>`
                    : `<button class="small" data-action="enable-restaurant" data-id="${restaurant.id}">Enable</button>`}
            </td>
        </tr>
    `).join("");
}

function renderDishes() {
    const body = $("dishesBody");

    if (!selectedRestaurantId) {
        body.innerHTML = '<tr><td colspan="5" class="empty">Select a restaurant first.</td></tr>';
        return;
    }

    if (!dishes.length) {
        body.innerHTML = '<tr><td colspan="5" class="empty">No dishes found for this restaurant.</td></tr>';
        return;
    }

    
    body.innerHTML = dishes.map((dish) => `
        <tr>
            <td>${dish.id}</td>
            <td>${escapeHtml(dish.name)}</td>
            <td>${Number(dish.price).toFixed(2)}</td>
            <td>${statusBadge(dish.is_available)}</td>
            <td class="actions">
                <button class="small secondary" data-action="edit-dish" data-id="${dish.id}">Edit</button>
                ${dish.is_available
                    ? `<button class="small danger" data-action="disable-dish" data-id="${dish.id}">Disable</button>`
                    : ""}
            </td>
        </tr>
    `).join("");
}


async function loadRestaurants() {
    restaurants = await api("/admin/restaurants");
    renderRestaurants();
}

async function loadDishes(restaurantId) {
    selectedRestaurantId = Number(restaurantId);

    const restaurant = restaurants.find(
        (item) => Number(item.id) === selectedRestaurantId
    );

    $("selectedRestaurantLabel").textContent =
        `Selected restaurant: ${restaurant ? restaurant.name : selectedRestaurantId}`;

    $("newDishBtn").disabled = !restaurant || !restaurant.is_active;

    dishes = await api(`/admin/restaurants/${selectedRestaurantId}/dishes`);
    renderDishes();
}


function resetRestaurantForm() {
    $("restaurantForm").reset();
    $("restaurantId").value = "";
    $("restaurantFormTitle").textContent = "New restaurant";
    $("restaurantForm").classList.add("hidden");
}

function resetDishForm() {
    $("dishForm").reset();
    $("dishId").value = "";
    $("dishFormTitle").textContent = "New dish";
    $("dishForm").classList.add("hidden");
}

function startRestaurantEdit(restaurant) {
    $("restaurantId").value = restaurant.id;
    $("restaurantName").value = restaurant.name || "";
    $("restaurantCategory").value = restaurant.category || "";
    $("restaurantPriceRange").value = restaurant.price_range || "";
    $("restaurantAddress").value = restaurant.address || "";
    $("restaurantZip").value = restaurant.zip_code || "";
    $("restaurantImage").value = restaurant.image_url || "";
    $("restaurantRating").value = restaurant.rating ?? "";
    $("restaurantRatingCount").value = restaurant.rating_count ?? "";
    $("restaurantDescription").value = restaurant.description || "";
    $("restaurantFormTitle").textContent = `Edit restaurant #${restaurant.id}`;
    $("restaurantForm").classList.remove("hidden");
    $("restaurantForm").scrollIntoView({ behavior: "smooth", block: "start" });
}

function startDishEdit(dish) {
    $("dishId").value = dish.id;
    $("dishName").value = dish.name || "";
    $("dishPrice").value = dish.price;
    $("dishCategoryId").value = dish.category_id ?? "";
    $("dishImage").value = dish.image_url || "";
    $("dishDescription").value = dish.description || "";
    $("dishFormTitle").textContent = `Edit dish #${dish.id}`;
    $("dishForm").classList.remove("hidden");
    $("dishForm").scrollIntoView({ behavior: "smooth", block: "start" });
}

$("newRestaurantBtn").addEventListener("click", () => {
    resetRestaurantForm();
    $("restaurantForm").classList.remove("hidden");
    $("restaurantName").focus();
});

$("cancelRestaurantBtn").addEventListener("click", resetRestaurantForm);

$("newDishBtn").addEventListener("click", () => {
    resetDishForm();
    $("dishForm").classList.remove("hidden");
    $("dishName").focus();
});

$("cancelDishBtn").addEventListener("click", resetDishForm);

$("restaurantForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    clearNotice();

    const id = $("restaurantId").value;
    const payload = {
        name: $("restaurantName").value.trim(),
        category: $("restaurantCategory").value.trim() || null,
        price_range: $("restaurantPriceRange").value.trim() || null,
        address: $("restaurantAddress").value.trim() || null,
        zip_code: $("restaurantZip").value.trim() || null,
        image_url: $("restaurantImage").value.trim() || null,
        rating: $("restaurantRating").value === "" ? null : Number($("restaurantRating").value),
        rating_count: $("restaurantRatingCount").value === "" ? null : Number($("restaurantRatingCount").value),
        description: $("restaurantDescription").value.trim() || null
    };

    try {
        await api(
            id ? `/admin/restaurants/${id}` : "/admin/restaurants",
            {
                method: id ? "PATCH" : "POST",
                body: JSON.stringify(payload)
            }
        );

        resetRestaurantForm();
        await loadRestaurants();
        notify(id ? "Restaurant updated." : "Restaurant created.");
    } catch (error) {
        notify(error.message, "error");
    }
});

$("dishForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    clearNotice();

    const id = $("dishId").value;
    const categoryValue = $("dishCategoryId").value;

    const payload = {
        name: $("dishName").value.trim(),
        price: Number($("dishPrice").value),
        category_id: categoryValue === "" ? null : Number(categoryValue),
        image_url: $("dishImage").value.trim() || null,
        description: $("dishDescription").value.trim() || null
    };

    try {
        await api(
            id
                ? `/admin/dishes/${id}`
                : `/admin/restaurants/${selectedRestaurantId}/dishes`,
            {
                method: id ? "PATCH" : "POST",
                body: JSON.stringify(payload)
            }
        );

        resetDishForm();
        await loadDishes(selectedRestaurantId);
        notify(id ? "Dish updated." : "Dish created.");
    } catch (error) {
        notify(error.message, "error");
    }
});

document.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;

    const action = button.dataset.action;
    const id = Number(button.dataset.id);

    try {
        clearNotice();

        if (action === "select-restaurant") {
            await loadDishes(id);
            return;
        }

        if (action === "edit-restaurant") {
            const restaurant = restaurants.find((item) => Number(item.id) === id);
            if (restaurant) startRestaurantEdit(restaurant);
            return;
        }

        if (action === "edit-dish") {
            const dish = dishes.find((item) => Number(item.id) === id);
            if (dish) startDishEdit(dish);
            return;
        }

        if (action === "disable-restaurant") {
            if (!confirm("Disable this restaurant? Its database record will be preserved.")) return;

            await api(`/admin/restaurants/${id}/disable`, { method: "POST" });
            if (selectedRestaurantId === id) {
                selectedRestaurantId = null;
                dishes = [];
                $("selectedRestaurantLabel").textContent = "Select a restaurant to manage its dishes.";
                $("newDishBtn").disabled = true;
                renderDishes();
            }
            await loadRestaurants();
            notify("Restaurant disabled. The record was preserved.");
            return;
        }

        if (action === "enable-restaurant") {
            if (!confirm("Enable this restaurant again?")) return;
        
            await api(`/admin/restaurants/${id}`, {
                method: "PATCH",
                body: JSON.stringify({ is_active: true })
            });
        
            await loadRestaurants();
            notify("Restaurant enabled.");
            return;
        }

        if (action === "disable-dish") {
            if (!confirm("Disable this dish? Its database record will be preserved.")) return;

            await api(`/admin/dishes/${id}/disable`, { method: "POST" });
            await loadDishes(selectedRestaurantId);
            notify("Dish disabled. The record was preserved.");
        }
    } catch (error) {
        notify(error.message, "error");
    }
});

$("logoutBtn").addEventListener("click", async () => {
    try {
        await api("/auth/logout", { method: "POST" });
    } catch (error) {
        notify(error.message, "error");
        return;
    }

    window.location.href = "auth.html";
});


async function triggerDag(dagId, buttonId) {
    const button = $(buttonId);
    const status = $("trainingStatus");

    button.disabled = true;
    status.textContent = `Requesting ${dagId}...`;

    try {
        const result = await api(
            `/admin/airflow/dags/${encodeURIComponent(dagId)}/runs`,
            { method: "POST", body: JSON.stringify({}) }
        );

        status.textContent =
            `Run created: ${result.dag_id} | ` +
            `Run ID: ${result.dag_run_id} | ` +
            `State: ${result.state || "queued"}`;

        notify(`Airflow accepted the ${dagId} run request.`);
    } catch (error) {
        status.textContent = `Failed: ${error.message}`;
        notify(error.message, "error");
    } finally {
        button.disabled = false;
    }
}

$("runRecommendationsBtn").addEventListener("click", () => {
    if (!confirm("Start the recommendations pipeline?")) return;

    triggerDag(
        "recommendations_daily",
        "runRecommendationsBtn"
    );
});

$("runRfmBtn").addEventListener("click", () => {
    if (!confirm("Start RFM segmentation?")) return;

    triggerDag(
        "rfm_segmentation_daily",
        "runRfmBtn"
    );
});


(async function init() {
    try {
        await loadRestaurants();
    } catch (error) {
        notify(error.message, "error");
        $("restaurantsBody").innerHTML =
            '<tr><td colspan="5" class="empty">Could not load restaurants.</td></tr>';
    }
})();
