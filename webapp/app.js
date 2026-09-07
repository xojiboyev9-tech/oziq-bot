// ==========================================
// TELEGRAM WEB APP
// ==========================================

const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();


// ==========================================
// MAHSULOTLAR
// ==========================================

let products = [
    {
        id: 1,
        name: "Guruch",
        price: 18000,
        category: "Oziq-ovqat",
        image: null
    },
    {
        id: 2,
        name: "Yog‘",
        price: 25000,
        category: "Oziq-ovqat",
        image: null
    }
];


// ==========================================
// SAVAT
// ==========================================

let cart = [];


// ==========================================
// TANLANGAN KATEGORIYA
// ==========================================

let selectedCategory = "Hammasi";


// ==========================================
// HTML ELEMENTLAR
// ==========================================

const categories = document.getElementById("categories");
const productsContainer = document.getElementById("products");

const cartBar = document.getElementById("cart-bar");
const cartCount = document.getElementById("cart-count");
const cartTotal = document.getElementById("cart-total");

const checkoutBtn = document.getElementById("checkout-btn");


// ==========================================
// NARX FORMAT
// ==========================================

function formatPrice(price) {
    return Number(price).toLocaleString("uz-UZ");
}


// ==========================================
// KATEGORIYALAR
// ==========================================

function renderCategories() {

    const categoryList = [
        "Hammasi",
        ...new Set(products.map(product => product.category))
    ];

    categories.innerHTML = "";

    categoryList.forEach(category => {

        const button = document.createElement("button");

        button.textContent = category;

        if (category === selectedCategory) {
            button.classList.add("active");
        }

        button.onclick = () => {

            selectedCategory = category;

            renderCategories();
            renderProducts();

        };

        categories.appendChild(button);

    });
}


// ==========================================
// MAHSULOT RASMINI TANLASH
// ==========================================

function selectImage(productId) {

    const input = document.createElement("input");

    input.type = "file";
    input.accept = "image/*";

    input.onchange = event => {

        const file = event.target.files[0];

        if (!file) return;

        const reader = new FileReader();

        reader.onload = e => {

            const product = products.find(
                p => p.id === productId
            );

            if (!product) return;

            product.image = e.target.result;

            renderProducts();

        };

        reader.readAsDataURL(file);

    };

    input.click();
}


// ==========================================
// MAHSULOTLARNI KO‘RSATISH
// ==========================================

function renderProducts() {

    productsContainer.innerHTML = "";

    let list = products;

    if (selectedCategory !== "Hammasi") {

        list = products.filter(
            product =>
                product.category === selectedCategory
        );

    }

    list.forEach(product => {

        const itemInCart = cart.find(
            item => item.id === product.id
        );

        const quantity = itemInCart
            ? itemInCart.quantity
            : 0;


        const card = document.createElement("div");

        card.className = "product-card";


        // --------------------------------------
        // RASM
        // --------------------------------------

        const imageBox = document.createElement("div");

        imageBox.className = "product-image";


        if (product.image) {

            const image = document.createElement("img");

            image.src = product.image;

            image.alt = product.name;

            image.style.width = "100%";
            image.style.height = "100%";
            image.style.objectFit = "cover";

            imageBox.appendChild(image);

        } else {

            imageBox.textContent = "📷";

        }


        // Rasmni bosganda qurilmadan tanlash

        imageBox.onclick = () => {

            selectImage(product.id);

        };


        // --------------------------------------
        // NOM
        // --------------------------------------

        const name = document.createElement("div");

        name.className = "product-name";

        name.textContent = product.name;


        // --------------------------------------
        // NARX
        // --------------------------------------

        const price = document.createElement("div");

        price.className = "product-price";

        price.textContent =
            formatPrice(product.price) + " so‘m";


        // --------------------------------------
        // ACTION
        // --------------------------------------

        const actions = document.createElement("div");

        actions.className = "product-actions";


        if (quantity === 0) {

            const addButton = document.createElement("button");

            addButton.textContent = "Savatga qo‘shish";

            addButton.className = "add-btn";

            addButton.onclick = () => {

                addToCart(product.id);

            };

            actions.appendChild(addButton);

        } else {

            const minus = document.createElement("button");

            minus.textContent = "−";

            minus.className = "minus-btn";

            minus.onclick = () => {

                removeFromCart(product.id);

            };


            const count = document.createElement("span");

            count.className = "quantity";

            count.textContent = quantity;


            const plus = document.createElement("button");

            plus.textContent = "+";

            plus.className = "plus-btn";

            plus.onclick = () => {

                addToCart(product.id);

            };


            actions.appendChild(minus);
            actions.appendChild(count);
            actions.appendChild(plus);

        }


        // --------------------------------------
        // CARD
        // --------------------------------------

        card.appendChild(imageBox);
        card.appendChild(name);
        card.appendChild(price);
        card.appendChild(actions);

        productsContainer.appendChild(card);

    });

}


// ==========================================
// SAVATGA QO‘SHISH
// ==========================================

function addToCart(productId) {

    const product = products.find(
        p => p.id === productId
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


    if (tg.HapticFeedback) {

        tg.HapticFeedback.impactOccurred("light");

    }

}


// ==========================================
// SAVATDAN AYIRISH
// ==========================================

function removeFromCart(productId) {

    const item = cart.find(
        product => product.id === productId
    );

    if (!item) return;


    item.quantity--;


    if (item.quantity <= 0) {

        cart = cart.filter(
            product => product.id !== productId
        );

    }


    updateCart();

    renderProducts();

}


// ==========================================
// SAVATNI YANGILASH
// ==========================================

function updateCart() {

    const count = cart.reduce(
        (sum, item) =>
            sum + item.quantity,
        0
    );


    const total = cart.reduce(
        (sum, item) =>
            sum + item.price * item.quantity,
        0
    );


    cartCount.textContent = count;

    cartTotal.textContent =
        formatPrice(total);


    if (count > 0) {

        cartBar.classList.remove("hidden");

    } else {

        cartBar.classList.add("hidden");

    }

}


// ==========================================
// BUYURTMA BERISH
// ==========================================

checkoutBtn.onclick = () => {

    if (cart.length === 0) {

        tg.showAlert("Savat bo‘sh!");

        return;

    }


    const total = cart.reduce(
        (sum, item) =>
            sum + item.price * item.quantity,
        0
    );


    const user =
        tg.initDataUnsafe &&
        tg.initDataUnsafe.user
            ? tg.initDataUnsafe.user
            : null;


    const order = {

        user: user,

        items: cart,

        total: total,

        date: new Date().toISOString()

    };


    tg.sendData(
        JSON.stringify(order)
    );

};


// ==========================================
// ISHGA TUSHIRISH
// ==========================================

renderCategories();

renderProducts();

updateCart();
