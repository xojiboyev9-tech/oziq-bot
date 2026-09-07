// ===============================
// TELEGRAM WEB APP
// ===============================

const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();


// ===============================
// MAHSULOTLAR (endi bot bazasidan olinadi)
// ===============================

let products = [];


// ===============================
// O'ZGARUVCHILAR
// ===============================

let cart = [];
let selectedCategory = "Hammasi";


// ===============================
// HTML ELEMENTLAR
// ===============================

const categoriesElement = document.getElementById("categories");
const productsElement = document.getElementById("products");

const cartBar = document.getElementById("cart-bar");
const cartCount = document.getElementById("cart-count");
const cartTotal = document.getElementById("cart-total");

const checkoutButton = document.getElementById("checkout-btn");


// ===============================
// PUL FORMAT
// ===============================

function formatPrice(price) {
    return price.toLocaleString("uz-UZ") + " so'm";
}


// ===============================
// MAHSULOTLARNI SERVERDAN OLISH
// ===============================

async function loadProducts() {

    try {

        productsElement.innerHTML = `<div class="loading">Yuklanmoqda...</div>`;

        const response = await fetch("/api/products");

        if (!response.ok) throw new Error("Server xatosi");

        products = await response.json();

        renderCategories();
        renderProducts();

    } catch (err) {

        productsElement.innerHTML = `<div class="loading">Mahsulotlarni yuklab bo'lmadi. Iltimos, sahifani qayta oching.</div>`;
        console.error(err);

    }

}


// ===============================
// KATEGORIYALAR
// ===============================

function renderCategories() {

    const categories = [
        "Hammasi",
        ...new Set(products.map(product => product.category))
    ];

    categoriesElement.innerHTML = "";

    categories.forEach(category => {

        const button = document.createElement("button");

        button.textContent = category;

        if (category === selectedCategory) {
            button.classList.add("active");
        }

        button.addEventListener("click", () => {

            selectedCategory = category;

            renderCategories();
            renderProducts();

        });

        categoriesElement.appendChild(button);

    });
}


// ===============================
// MAHSULOTLARNI CHIQARISH
// ===============================

function renderProducts() {

    productsElement.innerHTML = "";

    let filteredProducts = products;

    if (selectedCategory !== "Hammasi") {

        filteredProducts = products.filter(
            product => product.category === selectedCategory
        );

    }

    if (filteredProducts.length === 0) {
        productsElement.innerHTML = `<div class="loading">Bu kategoriyada mahsulot yo'q.</div>`;
        return;
    }

    filteredProducts.forEach(product => {

        const cartItem = cart.find(item => item.id === product.id);

        const quantity = cartItem ? cartItem.quantity : 0;

        // Rasm bo'lsa — rasmni, bo'lmasa — o'rniga umumiy emoji ko'rsatamiz
        const imageHtml = product.photo_url
            ? `<img class="product-image" src="${product.photo_url}" alt="${product.name}">`
            : `<div class="product-image product-image-placeholder">🛒</div>`;

        const card = document.createElement("div");

        card.className = "product-card";

        card.innerHTML = `

            ${imageHtml}

            <div class="product-name">
                ${product.name}
            </div>

            <div class="product-price">
                ${formatPrice(product.price)}
            </div>

            <div class="product-actions">

                ${
                    quantity === 0

                    ?

                    `<button class="add-btn" data-id="${product.id}">
                        Savatga qo‘shish
                    </button>`

                    :

                    `
                    <button class="minus-btn" data-id="${product.id}">
                        −
                    </button>

                    <span class="quantity">
                        ${quantity}
                    </span>

                    <button class="plus-btn" data-id="${product.id}">
                        +
                    </button>
                    `
                }

            </div>
        `;

        productsElement.appendChild(card);

    });


    // ADD

    document.querySelectorAll(".add-btn").forEach(button => {

        button.addEventListener("click", () => {

            const id = Number(button.dataset.id);

            addToCart(id);

        });

    });


    // PLUS

    document.querySelectorAll(".plus-btn").forEach(button => {

        button.addEventListener("click", () => {

            const id = Number(button.dataset.id);

            addToCart(id);

        });

    });


    // MINUS

    document.querySelectorAll(".minus-btn").forEach(button => {

        button.addEventListener("click", () => {

            const id = Number(button.dataset.id);

            removeFromCart(id);

        });

    });

}


// ===============================
// SAVATGA QO'SHISH
// ===============================

function addToCart(productId) {

    const product = products.find(
        product => product.id === productId
    );

    if (!product) return;


    const existing = cart.find(
        item => item.id === productId
    );


    if (existing) {

        existing.quantity++;

    } else {

        cart.push({
            id: product.id,
            name: product.name,
            price: product.price,
            quantity: 1
        });

    }


    updateCart();

    renderProducts();

    tg.HapticFeedback.impactOccurred("light");

}


// ===============================
// SAVATDAN AYIRISH
// ===============================

function removeFromCart(productId) {

    const existing = cart.find(
        item => item.id === productId
    );

    if (!existing) return;


    existing.quantity--;


    if (existing.quantity <= 0) {

        cart = cart.filter(
            item => item.id !== productId
        );

    }


    updateCart();

    renderProducts();

    tg.HapticFeedback.impactOccurred("light");

}


// ===============================
// SAVATNI YANGILASH
// ===============================

function updateCart() {

    const count = cart.reduce(
        (total, item) => total + item.quantity,
        0
    );


    const total = cart.reduce(
        (sum, item) => sum + item.price * item.quantity,
        0
    );


    cartCount.textContent = count;

    cartTotal.textContent = total.toLocaleString("uz-UZ");


    if (count > 0) {

        cartBar.classList.remove("hidden");

    } else {

        cartBar.classList.add("hidden");

    }

}


// ===============================
// BUYURTMA BERISH
// ===============================

checkoutButton.addEventListener("click", () => {

    if (cart.length === 0) {

        tg.showAlert("Savat bo‘sh!");

        return;

    }


    const total = cart.reduce(
        (sum, item) =>
            sum + item.price * item.quantity,
        0
    );

    // MUHIM: bot.py "qty" nomini kutadi, shuning uchun shu yerda
    // "quantity" emas, "qty" deb yuboramiz — aks holda adminga
    // xabar yuborilmay, bot ichida xatolik yuz beradi.
    const orderItems = cart.map(item => ({
        id: item.id,
        name: item.name,
        price: item.price,
        qty: item.quantity
    }));

    const order = {

        items: orderItems,

        total: total

    };


    // Telegram botga ma'lumot yuborish

    tg.sendData(
        JSON.stringify(order)
    );

});


// ===============================
// BOSHLANG'ICH ISHGA TUSHIRISH
// ===============================

loadProducts();

updateCart();
