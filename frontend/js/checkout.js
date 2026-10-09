const API_BASE_URL = "http://localhost:8000";
const DELIVERY_FEE = 2.99;

let cart = [];
let currentUser = null;

function loadData() {
    try {
        const savedCart = localStorage.getItem("foodexpress_cart");
        cart = savedCart ? JSON.parse(savedCart) : [];

        const savedUser = localStorage.getItem("foodexpress_user");
        currentUser = savedUser ? JSON.parse(savedUser) : null;
    } catch (error) {
        console.error("Failed to load checkout data:", error);
        cart = [];
        currentUser = null;
    }
}

function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
}

function calculateSubtotal() {
    return cart.reduce((sum, item) => {
        return sum + (
            Number(item.dish.price) * Number(item.quantity)
        );
    }, 0);
}

function renderUser() {
    const userElement = document.getElementById("checkoutUser");

    if (!currentUser) {
        userElement.textContent = "Not logged in";
        return;
    }

    userElement.textContent =
        `Welcome, ${currentUser.name || currentUser.username}`;
}

function renderItems() {
    const container = document.getElementById("checkoutItems");

    if (cart.length === 0) {
        container.innerHTML = `
            <p>Your cart is empty.</p>
        `;

        document.getElementById("placeOrderButton").disabled = true;
        return;
    }

    container.innerHTML = cart.map(item => {
        const dish = item.dish;
        const quantity = Number(item.quantity);
        const price = Number(dish.price);
        const subtotal = price * quantity;

        return `
            <div class="checkout-item">
                <div>
                    <div class="item-name">
                        ${escapeHtml(dish.name)}
                    </div>

                    <div class="item-quantity">
                        ${quantity} × $${price.toFixed(2)}
                    </div>
                </div>

                <div class="item-price">
                    $${subtotal.toFixed(2)}
                </div>
            </div>
        `;
    }).join("");
}

function renderSummary() {
    const subtotal = calculateSubtotal();
    const total = subtotal + DELIVERY_FEE;

    document.getElementById("checkoutSubtotal").textContent =
        `$${subtotal.toFixed(2)}`;

    document.getElementById("checkoutDelivery").textContent =
        `$${DELIVERY_FEE.toFixed(2)}`;

    document.getElementById("checkoutTotal").textContent =
        `$${total.toFixed(2)}`;
}

function checkAuthentication() {
    const warning = document.getElementById("authWarning");
    const button = document.getElementById("placeOrderButton");

    if (!currentUser) {
        warning.classList.remove("hidden");
        button.disabled = true;
    } else {
        warning.classList.add("hidden");
    }
}

async function placeOrder() {
    if (!currentUser) {
        window.location.href = "auth.html";
        return;
    }

    if (cart.length === 0) {
        alert("Your cart is empty.");
        return;
    }

    const address = document
        .getElementById("deliveryAddress")
        .value
        .trim();

    if (!address) {
        alert("Please enter your delivery address.");
        return;
    }
    const restaurantIds = [
        ...new Set(
            cart.map(item => Number(item.dish.restaurant_id))
        )
    ];

    if (restaurantIds.length !== 1) {
        alert(
            "Your cart contains dishes from multiple restaurants. " +
            "Please order from one restaurant at a time."
        );
        return;
    }

    const restaurantId = restaurantIds[0];

    const items = cart.map(item => ({
        dish_id: Number(item.dish.id),
        quantity: Number(item.quantity)
    }));

    const button = document.getElementById("placeOrderButton");

    button.disabled = true;
    button.textContent = "Placing order...";

    try {
        const response = await fetch(
            `${API_BASE_URL}/orders`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    user_id: Number(currentUser.id),
                    restaurant_id: restaurantId,
                    delivery_address: address,
                    items: items
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Failed to create order"
            );
        }

        localStorage.removeItem("foodexpress_cart");

        localStorage.setItem(
            "foodexpress_last_order",
            JSON.stringify(data.order)
        );

        window.location.href =
            `order-success.html?id=${data.order.id}`;

    } catch (error) {
        console.error("Checkout error:", error);

        alert(error.message);

        button.disabled = false;
        button.textContent = "Place Order";
    }
}

window.placeOrder = placeOrder;
loadData();
renderUser();
renderItems();
renderSummary();
checkAuthentication();
