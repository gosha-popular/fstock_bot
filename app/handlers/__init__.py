__all__ = ('router',)
from aiogram import Router

from .user import router as user_router
from .channel import router as channel_router

router = Router(name=__name__)
router.include_routers(
    user_router, channel_router,
)