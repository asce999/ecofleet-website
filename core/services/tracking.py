import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def fetch_tracking_info(pod_no: str) -> dict:
    """
    Fetches raw tracking info from the third-party provider.
    """
    url = getattr(settings, 'EXTERNAL_TRACKING_API_URL', 'http://ecofleetexpress.com/Auth_tracking')
    
    try:
        response = requests.post(
            url,
            data={'pod_no': pod_no},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'true' or data.get('status') is True:
            return data
        else:
            logger.warning(f"Tracking API returned non-true status for pod_no={pod_no}: {data}")
            return {"error": "Tracking data not found or invalid response", "raw": data}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching tracking info for pod_no={pod_no}: {e}")
        return {"error": "Unable to connect to tracking service"}
    except ValueError:
        logger.error(f"Invalid JSON response from tracking service for pod_no={pod_no}")
        return {"error": "Invalid response from tracking service"}
