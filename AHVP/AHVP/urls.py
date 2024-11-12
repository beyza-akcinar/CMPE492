"""
URL configuration for AHVP project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from AHVP_app import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', views.home_view, name='home'),
    path('yenimuayene/', views.new_examination_view, name='new_examination'),
    path('yenihasta/', views.new_patient_view, name='new_patient'),
    path('freesurfer-sonuc/', views.freesurfer_list_view, name='freesurfer_list'),
    path('freesurfer/export_excel/', views.export_freesurfer_to_excel, name='export_excel'),
    path('toplu-veri-yukleme/', views.upload_bulk_data_view, name='upload_bulk_data'),
    path('muayene/edit/', views.search_examination_view, name='search_examination_view'),
    path('muayene/edit/<int:id>/', views.edit_examination_view, name='edit_examination_view'),
    path('hasta/<int:patient_id>/', views.patient_detail_view, name='patient_detail_view'),
    path('datareport/', views.data_report_view, name='data_report_view'),
]
