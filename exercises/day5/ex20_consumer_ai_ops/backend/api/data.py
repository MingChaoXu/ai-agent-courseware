"""Data access endpoints for frontend direct access."""

from fastapi import APIRouter
from data_loader import DataLoader

router = APIRouter()


@router.get("/data/customers")
def data_customers():
    return DataLoader.customers()


@router.get("/data/products")
def data_products():
    return DataLoader.products()


@router.get("/data/reviews")
def data_reviews():
    return DataLoader.reviews()
