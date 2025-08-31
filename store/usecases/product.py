from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sqlalchemy_update, delete as sqlalchemy_delete
from sqlalchemy.exc import IntegrityError
from store.core.exceptions import NotFoundException
from store.models.product import Product  # seu modelo ORM
from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut

class ProductUsecase:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, body: ProductIn) -> ProductOut:
        """
        Cria um produto no banco.
        Pode lançar IntegrityError se houver conflito (ex: produto duplicado).
        """
        product = Product(**body.dict())
        self.session.add(product)
        try:
            await self.session.commit()
            await self.session.refresh(product)
            return ProductOut.from_orm(product)
        except IntegrityError:
            await self.session.rollback()
            raise

    async def get(self, id: str) -> ProductOut:
        """
        Retorna um produto pelo ID.
        """
        result = await self.session.get(Product, id)
        if not result:
            raise NotFoundException(f"Produto com id {id} não encontrado")
        return ProductOut.from_orm(result)

    async def query(
        self, name: Optional[str] = None, category: Optional[str] = None
    ) -> List[ProductOut]:
        """
        Lista produtos com filtros opcionais.
        """
        stmt = select(Product)
        if name:
            stmt = stmt.where(Product.name.ilike(f"%{name}%"))
        if category:
            stmt = stmt.where(Product.category.ilike(f"%{category}%"))
        result = await self.session.execute(stmt)
        products = result.scalars().all()
        return [ProductOut.from_orm(p) for p in products]

    async def update(self, id: str, body: ProductUpdate) -> ProductUpdateOut:
        """
        Atualiza um produto pelo ID.
        Atualiza updated_at automaticamente.
        """
        product = await self.session.get(Product, id)
        if not product:
            raise NotFoundException(f"Produto com id {id} não encontrado")

        for key, value in body.dict(exclude_unset=True).items():
            setattr(product, key, value)
        product.updated_at = datetime.utcnow()  # atualiza timestamp

        try:
            await self.session.commit()
            await self.session.refresh(product)
            return ProductUpdateOut.from_orm(product)
        except IntegrityError:
            await self.session.rollback()
            raise

    async def delete(self, id: str) -> None:
        """
        Deleta um produto pelo ID.
        """
        product = await self.session.get(Product, id)
        if not product:
            raise NotFoundException(f"Produto com id {id} não encontrado")
        await self.session.delete(product)
        await self.session.commit()
