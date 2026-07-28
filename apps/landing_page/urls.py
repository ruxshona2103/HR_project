from django.urls import path
from .views import LandingPageDataView, ProductListView, PricingPlanListView, ContactInfoView

app_name = 'landing_page'

urlpatterns = [
    path('landing-data/', LandingPageDataView.as_view(), name='landing-all-data'),

    path('products/', ProductListView.as_view(), name='product-list'),
    path('pricing/', PricingPlanListView.as_view(), name='pricing-list'),
    path('contacts/', ContactInfoView.as_view(), name='contact-info'),
]