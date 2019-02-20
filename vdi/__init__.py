
from starlette.applications import Starlette

from .settings import settings

app = Starlette(**settings)
