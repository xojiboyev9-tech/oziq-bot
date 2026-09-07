// ===============================
// TELEGRAM WEB APP
// ===============================

const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();


// ===============================
// MAHSULOTLAR
// ===============================

const products = [
    {
        id: 1,
        name: "Guruch",
        price: 18000,
        category: "Oziq-ovqat",
        image: "🍚"
    },
    {
        id: 2,
        name: "Yog‘",
        price: 25000,
        category: "Oziq-ovqat",
        image: "🫗"
    },
    {
        id: 3,
        name: "Shakar",
        price: 14000,
        category: "Oziq-ovqat",
        image: "🍬"
    },
    {
        id: 4,
        name: "Non",
        price: 4000,
        category: "Non mahsulotlari",
        image: "🍞"
    },
    {
        id: 5,
        name: "Sut",
        price: 10000,
        category: "Sut mahsulotlari",
        image: "🥛"
    },
    {
        id: 6,
        name: "Tuxum",
        price: 18000,
        category: "Sut mahsulotlari",
        image: "🥚"
    }
];


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

    filteredProducts.forEach(product => {

        const cartItem = cart.find(item => item.id === product.id);

        const quantity = cartItem ? cartItem.quantity : 0;

        const card = document.createElement("div");

        card.className = "product-card";

        card.innerHTML = `

            <div class="product-image">
                ${product.image}
            </div>

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


    const order = {

        user: tg.initDataUnsafe.user || null,

        items: cart,

        total: total,

        date: new Date().toISOString()

    };


    // Telegram botga ma'lumot yuborish

    tg.sendData(
        JSON.stringify(order)
    );

});


// ===============================
// BOSHLANG'ICH ISHGA TUSHIRISH
// ===============================

renderCategories();

renderProducts();

updateCart();
