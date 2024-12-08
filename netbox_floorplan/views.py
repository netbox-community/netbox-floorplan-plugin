from netbox.views import generic
from . import forms, models, tables
from dcim.models import Site, Rack, Device, Location
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import View
from django.shortcuts import render, redirect
from django.db.models import Q


from utilities.views import ViewTab, register_model_view


@register_model_view(Site, name='floorplans')
class FloorplanSiteTabView(generic.ObjectView):
    queryset = Site.objects.all()

    tab = ViewTab(
        label='Floor Plan',
        hide_if_empty=False,
        permission="netbox_floorplan.view_floorplan",
    )
    template_name = "netbox_floorplan/floorplan_view.html"

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
    queryset = Rack.objects.all()
    table = tables.FloorplanRackTable

    def get(self, request):
        fp_id = request.GET["floorplan_id"]
        fp_instance = models.Floorplan.objects.get(pk=fp_id)
        if fp_instance.record_type == "site":
            self.queryset = Rack.objects.all().filter(~Q(id__in=fp_instance.mapped_racks)).filter(
                site=fp_instance.site.id).order_by("name")
        else:
            locations = Location.objects.get(pk=fp_instance.location.id).get_descendants(include_self=True)
            self.queryset = Rack.objects.all().filter(~Q(id__in=fp_instance.mapped_racks)).filter(
                location__in=locations).order_by("name")
        return super().get(request)


class FloorplanDeviceListView(generic.ObjectListView):
    queryset = Device.objects.all()
    table = tables.FloorplanDeviceTable

    def get(self, request):
        fp_id = request.GET["floorplan_id"]
        fp_instance = models.Floorplan.objects.get(pk=fp_id)
        if fp_instance.record_type == "site":
            self.queryset = Device.objects.all().filter(~Q(id__in=fp_instance.mapped_devices)).filter(
                site=fp_instance.site.id).order_by("name")
        else:
            locations = Location.objects.get(pk=fp_instance.location.id).get_descendants(include_self=True)
            self.queryset = Device.objects.all().filter(~Q(id__in=fp_instance.mapped_devices)).filter(
                location__in=locations).order_by("name")
        return super().get(request)


class FloorplanImageView(generic.ObjectView):
    queryset = models.FloorplanImage.objects.all()


class FloorplanImageListView(generic.ObjectListView):
    queryset = models.FloorplanImage.objects.all()
    table = tables.FloorplanImageTable


class FloorplanImageEditView(generic.ObjectEditView):
    queryset = models.FloorplanImage.objects.all()
    form = forms.FloorplanImageForm
    template_name = 'netbox_floorplan/floorplanimage_edit.html'


class FloorplanImageDeleteView(generic.ObjectDeleteView):
    queryset = models.FloorplanImage.objects.all()
