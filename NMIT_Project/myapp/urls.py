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
    path('bills_of_materials/', views.bills_of_materials, name='bills_of_materials'),
    path("new_manufacturing/", views.new_manufacturing_order, name="new_manufacturing_order"),
    path('work_center', views.work_center, name='work_center'),
    path("new-order/", views.new_order, name="new_order"),
    path('stock_ledger', views.stock_ledger, name='stock_ledger'),
    path("stock_ledger/new/", views.stock_product_new, name="stock_product_new"),
]