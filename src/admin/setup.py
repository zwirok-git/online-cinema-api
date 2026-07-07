from sqladmin import Admin

from admin.auth import AdminAuth
from admin.views import (
    CertificationAdmin,
    DirectorAdmin,
    GenreAdmin,
    MovieAdmin,
    OrderAdmin,
    OrderItemAdmin,
    PaymentAdmin,
    StarAdmin,
    UserAdmin,
    UserGroupAdmin,
    UserProfileAdmin,
)
from core.config import settings
from core.database import engine


def setup_admin(app):
    authentication_backend = AdminAuth(secret_key=settings.TOKEN_SECRET_KEY)

    admin = Admin(
        app=app,
        engine=engine,
        title="Online Cinema Admin",
        authentication_backend=authentication_backend,
    )

    admin.add_view(UserAdmin)
    admin.add_view(UserProfileAdmin)
    admin.add_view(UserGroupAdmin)

    admin.add_view(MovieAdmin)
    admin.add_view(GenreAdmin)
    admin.add_view(StarAdmin)
    admin.add_view(DirectorAdmin)
    admin.add_view(CertificationAdmin)

    admin.add_view(OrderAdmin)
    admin.add_view(OrderItemAdmin)
    admin.add_view(PaymentAdmin)
