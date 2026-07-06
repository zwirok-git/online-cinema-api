from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.carts import Cart, CartItem


class CartRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Cart | None:
        result = await self.db.execute(
            select(Cart)
            .where(Cart.user_id == user_id)
            .options(selectinload(Cart.items).selectinload(CartItem.movie))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, cart_id: int) -> Cart | None:
        result = await self.db.execute(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(selectinload(Cart.items).selectinload(CartItem.movie))
        )
        return result.scalar_one_or_none()

    async def create_cart(self, user_id: int) -> Cart:
        cart = Cart(user_id=user_id)
        self.db.add(cart)
        await self.db.commit()
        await self.db.refresh(cart)
        return cart

    async def get_or_create_cart(self, user_id: int) -> Cart:
        cart = await self.get_by_user_id(user_id)
        if cart is not None:
            return cart
        return await self.create_cart(user_id)

    async def get_item(
        self, cart_id: int, movie_id: int
    ) -> CartItem | None:
        result = await self.db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart_id,
                CartItem.movie_id == movie_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_item(self, cart_id: int, movie_id: int) -> CartItem:
        item = CartItem(cart_id=cart_id, movie_id=movie_id)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def remove_item(self, cart_id: int, movie_id: int) -> bool:
        item = await self.get_item(cart_id, movie_id)
        if item is None:
            return False
        await self.db.delete(item)
        await self.db.commit()
        return True

    async def clear_cart(self, cart_id: int) -> None:
        cart = await self.get_by_id(cart_id)
        if cart is None:
            return
        for item in list(cart.items):
            await self.db.delete(item)
        await self.db.commit()

    async def get_all_carts(
        self, limit: int, offset: int
    ) -> list[Cart]:
        result = await self.db.execute(
            select(Cart)
            .limit(limit)
            .offset(offset)
            .options(selectinload(Cart.items).selectinload(CartItem.movie))
        )
        return list(result.scalars().all())

    async def get_carts_containing_movie(self, movie_id: int) -> list[Cart]:
        result = await self.db.execute(
            select(Cart)
            .join(CartItem, CartItem.cart_id == Cart.id)
            .where(CartItem.movie_id == movie_id)
            .options(selectinload(Cart.items).selectinload(CartItem.movie))
        )
        return list(result.scalars().unique().all())
