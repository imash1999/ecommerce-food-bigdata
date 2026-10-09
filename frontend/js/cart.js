const CART_KEY = "foodexpress_cart";

let cart = [];


function loadCart() {

    try {

        const saved =
            localStorage.getItem(
                CART_KEY
            );

        cart =
            saved
                ? JSON.parse(saved)
                : [];

    } catch (error) {

        console.error(
            "Failed to load cart:",
            error
        );

        cart = [];
    }
}

function saveCart() {

    localStorage.setItem(
        CART_KEY,
        JSON.stringify(cart)
    );
}

function renderCart() {

    const emptyCart =
        document.getElementById(
            "emptyCart"
        );

    const cartContent =
        document.getElementById(
            "cartContent"
        );

    const container =
        document.getElementById(
            "cartItems"
        );


    if (cart.length === 0) {

        emptyCart.style.display =
            "block";

        cartContent.style.display =
            "none";

        updateCartCount();

        return;
    }


    emptyCart.style.display =
        "none";

    cartContent.style.display =
        "grid";


    container.innerHTML = "";


    cart.forEach(
        (item, index) => {

            container.appendChild(
                createCartItem(
                    item,
                    index
                )
            );

        }
    );


    updateSummary();

    updateCartCount();
}

function createCartItem(
    item,
    index
) {

    const dish =
        item.dish;


    const quantity =
        item.quantity;


    const price =
        Number(
            dish.price || 0
        );


    const itemTotal =
        price * quantity;


    const element =
        document.createElement(
            "article"
        );


    element.className =
        "cart-item";


    element.innerHTML = `

        <div class="cart-item-image">
            ${getDishEmoji(dish.name)}
        </div>

        <div class="cart-item-info">

            <h3 class="cart-item-name">
                ${escapeHtml(dish.name)}
            </h3>

            <div class="cart-item-price">
                $${price.toFixed(2)} each
            </div>

            <div class="cart-item-total">
                $${itemTotal.toFixed(2)}
            </div>

        </div>


        <div class="quantity-control">

            <button
                class="quantity-button decrease"
                data-index="${index}"
            >
                −
            </button>

            <span class="quantity-value">
                ${quantity}
            </span>

            <button
                class="quantity-button increase"
                data-index="${index}"
            >
                +
            </button>

        </div>


        <button
            class="remove-button"
            data-index="${index}"
        >
            Remove
        </button>

    `;


    element
        .querySelector(".decrease")
        .addEventListener(
            "click",
            () => changeQuantity(
                index,
                -1
            )
        );


    element
        .querySelector(".increase")
        .addEventListener(
            "click",
            () => changeQuantity(
                index,
                1
            )
        );


    element
        .querySelector(".remove-button")
        .addEventListener(
            "click",
            () => removeItem(index)
        );


    return element;
}

function changeQuantity(
    index,
    amount
) {

    if (!cart[index]) {
        return;
    }


    cart[index].quantity += amount;


    if (
        cart[index].quantity <= 0
    ) {

        cart.splice(
            index,
            1
        );

    }


    saveCart();

    renderCart();
}

function removeItem(index) {

    cart.splice(
        index,
        1
    );

    saveCart();

    renderCart();
}

function updateSummary() {

    const subtotal =
        cart.reduce(
            (sum, item) => {

                return sum +
                    Number(
                        item.dish.price || 0
                    ) *
                    item.quantity;

            },
            0
        );

    const deliveryFee =
        subtotal > 0
            ? 2.99
            : 0;


    const total =
        subtotal +
        deliveryFee;


    document.getElementById(
        "subtotal"
    ).textContent =
        `$${subtotal.toFixed(2)}`;


    document.getElementById(
        "deliveryFee"
    ).textContent =
        `$${deliveryFee.toFixed(2)}`;


    document.getElementById(
        "total"
    ).textContent =
        `$${total.toFixed(2)}`;
}

function updateCartCount() {

    const count =
        cart.reduce(
            (total, item) =>
                total +
                item.quantity,
            0
        );


    document.getElementById(
        "cartCount"
    ).textContent =
        count;
}

function getDishEmoji(name) {

    const text =
        String(name)
            .toLowerCase();


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

function escapeHtml(value) {

    return String(value)
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}


function checkout() {
    window.location.href = "checkout.html";
}

const checkoutButton = document.getElementById("checkoutButton");

if (checkoutButton) {
    checkoutButton.addEventListener("click", checkout);
}

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadCart();

        renderCart();

    }
);