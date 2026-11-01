const API_BASE_URL = "http://localhost:8000";

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatMoney(value) {
    return `$${Number(value || 0).toFixed(2)}`;
}

function formatDate(value) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString();
}

function showState(state) {
    document.getElementById("loadingState").hidden = state !== "loading";
    document.getElementById("errorState").hidden = state !== "error";
    document.getElementById("emptyState").hidden = state !== "empty";
}

function renderOrders(orders) {
    const ordersList = document.getElementById("ordersList");

    ordersList.innerHTML = "";

    if (!orders || orders.length === 0) {
        showState("empty");
        return;
    }

    showState("orders");

    orders.forEach(order => {
        const card = document.createElement("article");
        card.className = "order-card";

        const itemsHtml = (order.items || []).map(item => `
            <div class="order-item">
                <div>
                    <span class="item-name">
                        ${escapeHtml(item.dish_name)}
                    </span>
                    <span class="item-quantity">
                        × ${Number(item.quantity)}
                    </span>
                </div>

                <div class="item-price">
                    ${formatMoney(item.subtotal)}
                </div>
            </div>
        `).join("");

        card.innerHTML = `
            <div class="order-header">
                <div>
                    <h2 class="order-number">
                        Order #${escapeHtml(order.id)}
                    </h2>

                    <p class="restaurant-name">
                        ${escapeHtml(order.restaurant_name)}
                    </p>

                    <p class="restaurant-address">
                        ${escapeHtml(order.restaurant_address)}
                    </p>
                </div>

                <div class="status">
                    ${escapeHtml(order.status)}
                </div>
            </div>

            <div class="order-items">
                ${itemsHtml}
            </div>

            <div class="order-summary">
                <div class="summary-row">
                    <span>Subtotal</span>
                    <span>${formatMoney(order.subtotal)}</span>
                </div>

                <div class="summary-row">
                    <span>Delivery fee</span>
                    <span>${formatMoney(order.delivery_fee)}</span>
                </div>

                <div class="summary-row">
                    <span>Discount</span>
                    <span>-${formatMoney(order.discount)}</span>
                </div>

                <div class="summary-row total">
                    <span>Total</span>
                    <span>${formatMoney(order.total_amount)}</span>
                </div>
            </div>

            <div class="delivery-address">
                <strong>Delivery address</strong>
                <span>${escapeHtml(order.delivery_address)}</span>
            </div>

            <div class="order-date">
                ${formatDate(order.created_at)}
            </div>
        `;

        ordersList.appendChild(card);
    });
}

async function loadOrders() {
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
        `Orders for ${currentUser.name || currentUser.username}`;

    try {
        const response = await fetch(
            `${API_BASE_URL}/users/${Number(currentUser.id)}/orders`,{
                credentials: "include"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Failed to load orders");
        }

        renderOrders(data.orders || []);

    } catch (error) {
        console.error("Failed to load orders:", error);

        const errorState = document.getElementById("errorState");
        errorState.textContent = error.message || "Failed to load orders.";

        showState("error");
    }
}

document.addEventListener("DOMContentLoaded", loadOrders);
