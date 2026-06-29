from core.models import Shipment, ShipmentStatus, Consignment, Driver, Vehicle
from django.db import transaction

class ShipmentService:
    @staticmethod
    def create_ftl_shipment(origin, destination, booking_date, vehicle_obj, metadata):
        """Creates an FTL Shipment within a transaction."""
        with transaction.atomic():
            shipment = Shipment.objects.create(
                shipment_type='FTL',
                origin=origin,
                destination=destination,
                dispatch_date=booking_date,
                vehicle=vehicle_obj,
                metadata=metadata
            )
            ShipmentStatus.objects.create(
                shipment=shipment,
                status='DRAFT'
            )
            return shipment

    @staticmethod
    def update_shipment_status(shipment_id, new_status):
        """Adds a new status log for the shipment."""
        with transaction.atomic():
            shipment = Shipment.objects.get(id=shipment_id)
            ShipmentStatus.objects.create(
                shipment=shipment,
                status=new_status
            )
            return shipment
