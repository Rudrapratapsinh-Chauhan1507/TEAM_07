from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path('work_order_analysis/', views.work_order_analysis, name='work_order_analysis'),
    path('manufacturing_products/', views.manufacturing_products, name='manufacturing_products'),
    path('work_products/', views.work_products, name='work_products'),
    path('work_order/<int:pk>/', views.view_work_order, name='view_work_order'),
    path('work_order/<int:pk>/edit/', views.edit_work_order, name='edit_work_order'),
    path('work_order/delete/<int:pk>/', views.delete_work_order, name='delete_work_order'),
    path('bills_of_materials/', views.bills_of_materials, name='bills_of_materials'),
    path("new_manufacturing/", views.new_manufacturing_order, name="new_manufacturing_order"),
    path("manufacturing/new/", views.new_manufacturing_order, name="new_manu"),
    path('get_components/<int:bom_id>/', views.get_components, name='get_components'),
    path("work-centers/", views.work_center, name="work_center"),
    path("work-centers/new/", views.new_work_center, name="new_work_center"),
    path("work-centers/edit/<int:pk>/", views.edit_work_center, name="edit_work_center"),
    path("work-centers/delete/<int:pk>/", views.delete_work_center, name="delete_work_center"),
    path("new-order/", views.new_order, name="new_order"),
    path('stock_ledger', views.stock_ledger, name='stock_ledger'),
    path('stock_ledger/edit/<int:product_id>/', views.stock_product_edit, name='stock_product_edit'),
    path("stock_ledger/new/", views.stock_product_new, name="stock_product_new"),
]

