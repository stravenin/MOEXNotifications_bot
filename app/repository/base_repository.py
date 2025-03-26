from abc import ABC
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class AbstractRepository(ABC):
    pass


class SqlRepository(AbstractRepository):
    model = Any

    def __init__(self, session: AsyncSession):
        self.session = session
