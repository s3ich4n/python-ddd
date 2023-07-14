from abc import ABC

from modules.catalog.domain.entities import GenericUUID, Listing
from seedwork.domain.repositories import GenericRepository


class ListingRepository(GenericRepository[GenericUUID, Listing], ABC):
    """An interface for Listing repository"""
