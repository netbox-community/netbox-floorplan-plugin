from django.urls import include, path
from . import models, views
from netbox.views.generic import ObjectChangeLogView
from utilities.urls import get_model_urls

urlpatterns = (
    path('floorplans/', views.FloorplanListView.as_view(), name='floorplan_list'),
    path('floorplans/racks/', views.FloorplanRackListView.as_view(), name='floorplan_rack_list'),
    path('floorplans/devices/', views.FloorplanDeviceListView.as_view(), name='floorplan_device_list'),
    path('floorplans/add/', views.FloorplanAddView.as_view(), name='floorplan_add'),
    path('floorplans/<int:pk>/edit/', views.FloorplanMapEditView.as_view(), name='floorplan_edit'),
    path('floorplans/<int:pk>/delete/', views.FloorplanDeleteView.as_view(), name='floorplan_delete'),
    path('floorplans/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='floorplan_changelog', kwargs={'model': models.Floorplan}),

    # Community
    path(
        "floorplans/floorplanimages/",
        include(get_model_urls("netbox_floorplan", "floorplanimage", detail=False)),
    ),
    path(
        "floorplans/floorplanimages/<int:pk>/",
        include(get_model_urls("netbox_floorplan", "floorplanimage")),
    ),
)
