@router.message(AddProduct.category)
async def add_product_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(AddProduct.description)
    await message.answer("Qisqacha tavsif kiriting (yoki - yozing, agar kerak bo'lmasa):")

@router.message(AddProduct.description)
async def add_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text if message.text != "-" else "")
    await state.set_state(AddProduct.photo)
    await message.answer("Mahsulot rasmi linkini yuboring (yoki - yozing, rasm bo'lmasa):")

@router.message(AddProduct.photo)
async def add_product_photo(message: Message, state: FSMContext):
    data = await state.update_data(photo_url=message.text if message.text != "-" else "")
    db.add_product(
        name=data["name"],
        price=data["price"],
        description=data["description"],
        category=data["category"],
        photo_url=data["photo_url"],
    )
    await state.clear()
    await message.answer(
        f"✅ Mahsulot qo'shildi: {data['name']} — {data['price']} so'm",
        reply_markup=admin_menu_kb(),
    )
