from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView

from ralph.data_center.models.physical import Rack, RackAccessory, ServerRoom
from ralph.dc_view.serializers.models_serializer import (
    DataCenterAssetSerializer,
    PDUSerializer,
    RackAccessorySerializer,
    RackBaseSerializer,
    RackSerializer,
    SRSerializer
)


class DCAssetsView(APIView):
    def get_object(self, pk):
        try:
            return Rack.objects.get(id=pk)
        except Rack.DoesNotExist:
            raise Http404

    def _get_assets(self, rack):
        return DataCenterAssetSerializer(rack.get_root_assets(), many=True).data

    def _get_rack_data(self, rack):
        return RackSerializer(rack).data

    def _get_accessories(self, rack):
        accessories = RackAccessory.objects.select_related("accessory").filter(
            rack=rack
        )
        return RackAccessorySerializer(accessories, many=True).data

    def _get_pdus(self, rack):
        return PDUSerializer(rack.get_pdus(), many=True).data

    def get(self, request, rack_id, format=None):
        rack = self.get_object(rack_id)
        devices = {}
        devices["devices"] = self._get_assets(rack) + self._get_accessories(rack)
        devices["pdus"] = self._get_pdus(rack)
        devices["info"] = self._get_rack_data(rack)
        return Response(devices)

    def put(self, request, rack_id, format=None):
        serializer = RackSerializer(self.get_object(rack_id), data=request.data)
        if serializer.is_valid():
            rack = serializer.update(data=request.data)
            return Response(self._get_rack_data(rack))
        return Response(serializer.errors)

    def post(self, request, format=None):
        serializer = RackBaseSerializer(data=request.data)
        if serializer.is_valid():
            rack = serializer.create(serializer.data)
            return Response(self._get_rack_data(rack))
        return Response(serializer.errors)


class SRRacksAPIView(APIView):
    """
    Return information of list rack in data center with their positions.
    """

    def get_object(self, pk):
        try:
            return ServerRoom.objects.get(id=pk)
        except ServerRoom.DoesNotExist:
            raise Http404

    def get(self, request, server_room_id, format=None):
        """
        Collecting racks information for given data_center id.
        :param data_center_id int: data_center id
        :returns list: list of informations about racks in given data center
        """
        return Response(SRSerializer(self.get_object(server_room_id)).data)
