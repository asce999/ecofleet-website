from django.http import JsonResponse
from django.views.decorators.http import require_GET
from core.services.tracking import fetch_tracking_info

@require_GET
def shipment_tracking_api(request, pod_no):
    """
    Public API endpoint to fetch tracking info.
    Proxies the request to the upstream tracking service.
    """
    if not pod_no:
        return JsonResponse({"error": "Missing pod_no"}, status=400)

    data = fetch_tracking_info(pod_no)
    
    if "error" in data:
        status_code = 404 if "not found" in data["error"].lower() else 502
        return JsonResponse(data, status=status_code)
        
    return JsonResponse(data)
