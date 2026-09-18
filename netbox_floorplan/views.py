from netbox.views import generic
from . import forms, models, tables
from .ui import panels
from dcim.models import Site, Rack, Device, Location
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import View
from django.shortcuts import render, redirect
from django.db.models import Q

from extras.ui.panels import CustomFieldsPanel, TagsPanel
from netbox.ui import layout
from netbox.ui.breadcrumbs import Breadcrumb, filtered_list_url
from netbox.ui.panels import CommentsPanel, PluginContentPanel, TemplatePanel

from utilities.views import ViewTab, register_model_view


# The canvas and the pro tips block are shared by both floorplan tab views.
FLOORPLAN_PANELS = (
    TemplatePanel('netbox_floorplan/inc/floorplan_canvas.html'),
    TemplatePanel('netbox_floorplan/inc/pro_tips_panel.html'),
)


@register_model_view(Site, name='floorplans')
class FloorplanSiteTabView(generic.ObjectView):
    queryset = Site.objects.all()

    tab = ViewTab(
        label='Floor Plan',
        hide_if_empty=False,
        permission="netbox_floorplan.view_floorplan",
    )
    template_name = "netbox_floorplan/floorplan_view.html"
    layout = layout.SimpleLayout(
        # As the template did, walk the site's region and group ancestors. NetBox's own site
        # view shows neither, so these are the plugin's addition.
        breadcrumbs=[
            Breadcrumb(
                lambda obj: obj.region.get_ancestors(include_self=True) if obj.region else [],
                url=filtered_list_url('dcim:site_list', 'region_id'),
            ),
            Breadcrumb(
                lambda obj: obj.group.get_ancestors(include_self=True) if obj.group else [],
                url=filtered_list_url('dcim:site_list', 'group_id'),
            ),
        ],
        bottom_panels=[
            *FLOORPLAN_PANELS,
            PluginContentPanel('full_width_page'),
        ],
    )

    def get_extra_context(self, request, instance):
        floorplan_qs = models.Floorplan.objects.filter(
            site=instance.id).first()
        if floorplan_qs:
            floorplan_qs.resync_canvas()
            return {"floorplan": floorplan_qs, "record_type": "site"}
        else:
            return {"floorplan": None, "record_type": "site"}


@register_model_view(Location, name='floorplans')
class FloorplanLocationTabView(generic.ObjectView):
    queryset = Location.objects.all()

    tab = ViewTab(
        label="Floor Plan",
        hide_if_empty=False,
        permission="netbox_floorplan.view_floorplan",
    )
    template_name = "netbox_floorplan/floorplan_view.html"
    layout = layout.SimpleLayout(
        # Matching NetBox's own location view, which walks the location's ancestors. The
        # template checked for a region and a group, neither of which a Location has, so it
        # only ever rendered the root breadcrumb here.
        breadcrumbs=[
            Breadcrumb(lambda obj: obj.get_ancestors()),
        ],
        bottom_panels=[
            *FLOORPLAN_PANELS,
            PluginContentPanel('full_width_page'),
        ],
    )

    def get_extra_context(self, request, instance):
        floorplan_qs = models.Floorplan.objects.filter(
            location=instance.id).first()
        if floorplan_qs:
            floorplan_qs.resync_canvas()
            return {"floorplan": floorplan_qs, "record_type": "location"}
        else:
            return {"floorplan": None, "record_type": "location"}


class FloorplanListView(generic.ObjectListView):
    queryset = models.Floorplan.objects.all()
    table = tables.FloorplanTable
    template_name = "netbox_floorplan/floorplan_ui_listview.html"


class FloorplanAddView(PermissionRequiredMixin, View):
    permission_required = "netbox_floorplan.add_floorplan"

    def get(self, request):
        if request.GET.get("site"):
            id = request.GET.get("site")
            instance = models.Floorplan(site=Site.objects.get(id=id))
            instance.save()
            return redirect("plugins:netbox_floorplan:floorplan_edit", pk=instance.id)
        elif request.GET.get("location"):
            id = request.GET.get("location")
            instance = models.Floorplan(
                location=Location.objects.get(id=id))
            instance.save()
            return redirect("plugins:netbox_floorplan:floorplan_edit", pk=instance.id)


class FloorplanDeleteView(generic.ObjectDeleteView):
    queryset = models.Floorplan.objects.all()


class FloorplanMapEditView(LoginRequiredMixin, View):
    permission_required = "netbox_floorplan.edit_floorplan"

    def get(self, request, pk):
        fp = models.Floorplan.objects.get(pk=pk)
        fp.resync_canvas()
        site = None
        location = None
        if fp.record_type == "site":
            site = Site.objects.get(id=fp.site.id)
        else:
            location = Location.objects.get(id=fp.location.id)
        racklist = Rack.objects.filter(site=site)
        form = forms.FloorplanRackFilterForm
        form2 = forms.FloorplanForm
        return render(request, "netbox_floorplan/floorplan_edit.html", {
            "form": form,
            "form2": form2,
            "site": site,
            "location": location,
            "racklist": racklist,
            "obj": fp,
            "record_type": fp.record_type
        })


class FloorplanRackListView(generic.ObjectListView):
    # Grab the dcim/rack data from Netbox as well as the associated dcim/rack-role data if
    # the rack role is set
    queryset = Rack.objects.all().select_related("role", "rack_type")
    table = tables.FloorplanRackTable

    def get(self, request):
        fp_id = request.GET["floorplan_id"]
        fp_instance = models.Floorplan.objects.get(pk=fp_id)
        if fp_instance.record_type == "site":
            self.queryset = Rack.objects.all().select_related("role", "rack_type").filter(~Q(id__in=fp_instance.mapped_racks)).filter(
                site=fp_instance.site.id).order_by("name")
        else:
            self.queryset = Rack.objects.all().select_related("role", "rack_type").filter(~Q(id__in=fp_instance.mapped_racks)).filter(
                location=fp_instance.location.id).order_by("name")
        return super().get(request)


class FloorplanDeviceListView(generic.ObjectListView):
    queryset = Device.objects.all()
    table = tables.FloorplanDeviceTable

    def get(self, request):
        fp_id = request.GET["floorplan_id"]
        fp_instance = models.Floorplan.objects.get(pk=fp_id)
        if fp_instance.record_type == "site":
            self.queryset = Device.objects.all().filter(~Q(id__in=fp_instance.mapped_devices)).filter(
                site=fp_instance.site.id, rack=None).order_by("name")
        else:
            self.queryset = Device.objects.all().filter(~Q(id__in=fp_instance.mapped_devices)).filter(
                location=fp_instance.location.id, rack=None).order_by("name")
        return super().get(request)


@register_model_view(models.FloorplanImage)
class FloorplanImageView(generic.ObjectView):
    queryset = models.FloorplanImage.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            panels.FloorplanImagePanel(),
            CustomFieldsPanel(),
            TagsPanel(),
            CommentsPanel(),
            PluginContentPanel('left_page'),
        ],
        right_panels=[
            PluginContentPanel('right_page'),
        ],
        bottom_panels=[
            PluginContentPanel('full_width_page'),
        ],
    )


@register_model_view(models.FloorplanImage, "list", path="", detail=False)
class FloorplanImageListView(generic.ObjectListView):
    queryset = models.FloorplanImage.objects.all()
    table = tables.FloorplanImageTable


@register_model_view(models.FloorplanImage, "add", detail=False)
@register_model_view(models.FloorplanImage, "edit")
class FloorplanImageEditView(generic.ObjectEditView):
    queryset = models.FloorplanImage.objects.all()
    form = forms.FloorplanImageForm
    template_name = 'netbox_floorplan/floorplanimage_edit.html'


@register_model_view(models.FloorplanImage, "delete")
class FloorplanImageDeleteView(generic.ObjectDeleteView):
    queryset = models.FloorplanImage.objects.all()
