from typing import List
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status, Query
from pydantic import UUID4
from sqlalchemy.exc import IntegrityError
from store.core.exceptions import NotFoundException

from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut
from store.usecases.product import ProductUsecase

router = APIRouter(tags=["products"])


@router.post(path="/", status_code=status.HTTP_201_CREATED)
async def post(
    body: ProductIn = Body(...), usecase: ProductUsecase = Depends()
) -> ProductOut:
    """
    Cria um novo produto.
    Captura IntegrityError caso haja duplicidade ou violação de integridade.
    """
    try:
        return await usecase.create(body=body)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro de integridade: {exc.orig}"
        )


@router.get(path="/{id}", status_code=status.HTTP_200_OK)
async def get(
    id: UUID4 = Path(alias="id"), usecase: ProductUsecase = Depends()
) -> ProductOut:
    """
    Retorna um produto pelo ID.
    Retorna 404 se não encontrado.
    """
    try:
        return await usecase.get(id=id)
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


@router.get(path="/", status_code=status.HTTP_200_OK)
async def query(
    name: str | None = Query(None),
    category: str | None = Query(None),
    usecase: ProductUsecase = Depends()
) -> List[ProductOut]:
    """
    Lista produtos com filtros opcionais por nome e categoria.
    """
    return await usecase.query(name=name, category=category)


@router.patch(path="/{id}", status_code=status.HTTP_200_OK)
async def patch(
    id: UUID4 = Path(alias="id"),
    body: ProductUpdate = Body(...),
    usecase: ProductUsecase = Depends(),
) -> ProductUpdateOut:
    """
    Atualiza um produto.
    Retorna 404 se o produto não existir.
    O updated_at deve ser atualizado dentro do usecase.update().
    """
    try:
        return await usecase.update(id=id, body=body)
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro de integridade: {exc.orig}"
        )


@router.delete(path="/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: UUID4 = Path(alias="id"), usecase: ProductUsecase = Depends()
) -> None:
    """
    Deleta um produto pelo ID.
    Retorna 404 se não encontrado.
    """
    try:
        await usecase.delete(id=id)
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
