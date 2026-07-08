from sqladmin import ModelView

from models.movies import Certification, Director, Genre, Movie, Star
from models.orders import Order, OrderItem
from models.payments import Payment
from models.users import UserGroupModel, UserModel, UserProfileModel


class UserAdmin(ModelView, model=UserModel):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"

    column_list = [
        UserModel.id,
        UserModel.email,
        UserModel.is_active,
        UserModel.created_at,
        UserModel.group_id,
    ]
    column_searchable_list = [UserModel.email]
    column_sortable_list = [
        UserModel.id,
        UserModel.email,
        UserModel.created_at,
    ]

    can_create = False
    can_delete = False
    form_excluded_columns = [
        UserModel.hashed_password,
        UserModel.activation_token,
        UserModel.reset_token,
        UserModel.refresh_token,
        UserModel.cart,
    ]


class UserProfileAdmin(ModelView, model=UserProfileModel):
    column_list = [
        UserProfileModel.id,
        UserProfileModel.user_id,
        UserProfileModel.first_name,
        UserProfileModel.last_name,
        UserProfileModel.avatar,
    ]


class UserGroupAdmin(ModelView, model=UserGroupModel):
    column_list = [UserGroupModel.id, UserGroupModel.name]


class MovieAdmin(ModelView, model=Movie):
    name = "Movie"
    name_plural = "Movies"
    icon = "fa-solid fa-film"

    column_list = [
        Movie.id,
        Movie.name,
        Movie.year,
        Movie.imdb,
        Movie.price,
        Movie.certification_id,
    ]
    column_searchable_list = [Movie.name, Movie.description]
    column_sortable_list = [
        Movie.id,
        Movie.name,
        Movie.year,
        Movie.imdb,
        Movie.price,
    ]

    form_excluded_columns = [
        Movie.comments,
        Movie.likes,
        Movie.favorites,
        Movie.ratings,
    ]


class GenreAdmin(ModelView, model=Genre):
    column_list = [Genre.id, Genre.name]
    column_searchable_list = [Genre.name]


class StarAdmin(ModelView, model=Star):
    column_list = [Star.id, Star.name]
    column_searchable_list = [Star.name]


class DirectorAdmin(ModelView, model=Director):
    column_list = [Director.id, Director.name]
    column_searchable_list = [Director.name]


class CertificationAdmin(ModelView, model=Certification):
    column_list = [Certification.id, Certification.name]
    column_searchable_list = [Certification.name]


class OrderAdmin(ModelView, model=Order):
    column_list = [
        Order.id,
        Order.user_id,
        Order.status,
        Order.total_amount,
        Order.created_at,
    ]
    can_create = False
    can_edit = False
    can_delete = False


class OrderItemAdmin(ModelView, model=OrderItem):
    column_list = [
        OrderItem.id,
        OrderItem.order_id,
        OrderItem.movie_id,
        OrderItem.price_at_order,
    ]
    can_create = False
    can_edit = False
    can_delete = False


class PaymentAdmin(ModelView, model=Payment):
    column_list = [
        Payment.id,
        Payment.user_id,
        Payment.order_id,
        Payment.amount,
        Payment.status,
        Payment.created_at,
    ]
    can_create = False
    can_edit = False
    can_delete = False
