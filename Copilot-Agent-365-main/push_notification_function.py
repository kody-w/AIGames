"""
Azure Function for Push Notifications
Handles push notification subscriptions and sending notifications to users
"""

import azure.functions as func
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pywebpush import webpush, WebPushException
from azure.storage.fileshare import ShareFileClient, ShareDirectoryClient

# Initialize logger
logger = logging.getLogger(__name__)

# VAPID credentials (should be in environment variables)
# Generate using: npx web-push generate-vapid-keys
VAPID_PRIVATE_KEY = "your-vapid-private-key"
VAPID_PUBLIC_KEY = "your-vapid-public-key"
VAPID_CLAIMS = {
    "sub": "mailto:support@ai-ambassadors.app"
}


def build_cors_response(body: str, status_code: int = 200) -> func.HttpResponse:
    """Build HTTP response with CORS headers"""
    return func.HttpResponse(
        body=body,
        status_code=status_code,
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )


def push_subscribe_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle push notification subscription
    POST /api/push/subscribe
    Body: {
        "subscription": {...},
        "userId": "user_123",
        "ambassadorId": "creative-001",
        "timestamp": 1234567890
    }
    """
    try:
        req_body = req.get_json()

        subscription = req_body.get('subscription')
        user_id = req_body.get('userId')
        ambassador_id = req_body.get('ambassadorId')

        if not subscription or not user_id:
            return build_cors_response(
                json.dumps({"error": "Missing required fields"}),
                status_code=400
            )

        # Save subscription to Azure File Storage
        subscription_data = {
            "userId": user_id,
            "ambassadorId": ambassador_id,
            "subscription": subscription,
            "timestamp": req_body.get('timestamp', datetime.now().timestamp()),
            "active": True
        }

        success = save_subscription(user_id, subscription_data)

        if success:
            logger.info(f"Subscription saved for user: {user_id}")
            return build_cors_response(
                json.dumps({
                    "success": True,
                    "message": "Subscription saved successfully"
                })
            )
        else:
            return build_cors_response(
                json.dumps({"error": "Failed to save subscription"}),
                status_code=500
            )

    except ValueError as e:
        logger.error(f"Invalid request body: {e}")
        return build_cors_response(
            json.dumps({"error": "Invalid request body"}),
            status_code=400
        )
    except Exception as e:
        logger.error(f"Subscribe error: {e}")
        return build_cors_response(
            json.dumps({"error": str(e)}),
            status_code=500
        )


def push_unsubscribe_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle push notification unsubscribe
    POST /api/push/unsubscribe
    Body: { "endpoint": "..." }
    """
    try:
        req_body = req.get_json()
        endpoint = req_body.get('endpoint')

        if not endpoint:
            return build_cors_response(
                json.dumps({"error": "Missing endpoint"}),
                status_code=400
            )

        # Find and remove subscription
        success = remove_subscription_by_endpoint(endpoint)

        if success:
            logger.info(f"Subscription removed: {endpoint}")
            return build_cors_response(
                json.dumps({
                    "success": True,
                    "message": "Subscription removed successfully"
                })
            )
        else:
            return build_cors_response(
                json.dumps({"error": "Subscription not found"}),
                status_code=404
            )

    except Exception as e:
        logger.error(f"Unsubscribe error: {e}")
        return build_cors_response(
            json.dumps({"error": str(e)}),
            status_code=500
        )


def push_send_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    Send push notification to user(s)
    POST /api/push/send
    Body: {
        "userId": "user_123" or "userIds": ["user_123", "user_456"],
        "notification": {
            "title": "New Message",
            "body": "You have a new message from Creative Ambassador",
            "icon": "/icons/icon-192x192.png",
            "badge": "/icons/badge-72x72.png",
            "tag": "message",
            "data": {
                "url": "/mobile-chat.html?ambassador=creative-001",
                "ambassadorId": "creative-001"
            }
        }
    }
    """
    try:
        req_body = req.get_json()

        # Get target users
        user_id = req_body.get('userId')
        user_ids = req_body.get('userIds', [])

        if user_id:
            user_ids = [user_id]

        if not user_ids:
            return build_cors_response(
                json.dumps({"error": "No users specified"}),
                status_code=400
            )

        notification = req_body.get('notification', {})

        if not notification:
            return build_cors_response(
                json.dumps({"error": "No notification data"}),
                status_code=400
            )

        # Send notifications
        results = send_notifications(user_ids, notification)

        success_count = sum(1 for r in results if r['success'])

        return build_cors_response(
            json.dumps({
                "success": True,
                "sent": success_count,
                "total": len(user_ids),
                "results": results
            })
        )

    except Exception as e:
        logger.error(f"Send notification error: {e}")
        return build_cors_response(
            json.dumps({"error": str(e)}),
            status_code=500
        )


def send_notifications(user_ids: List[str], notification_data: Dict) -> List[Dict]:
    """
    Send push notifications to multiple users
    """
    results = []

    for user_id in user_ids:
        try:
            # Get user subscription
            subscription_data = get_subscription(user_id)

            if not subscription_data or not subscription_data.get('active'):
                results.append({
                    "userId": user_id,
                    "success": False,
                    "error": "No active subscription"
                })
                continue

            subscription = subscription_data.get('subscription')

            # Send push notification
            response = webpush(
                subscription_info=subscription,
                data=json.dumps(notification_data),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )

            results.append({
                "userId": user_id,
                "success": True,
                "statusCode": response.status_code
            })

            logger.info(f"Notification sent to user: {user_id}")

        except WebPushException as e:
            logger.error(f"WebPush error for user {user_id}: {e}")

            # If subscription is invalid, mark as inactive
            if e.response and e.response.status_code in [404, 410]:
                subscription_data['active'] = False
                save_subscription(user_id, subscription_data)

            results.append({
                "userId": user_id,
                "success": False,
                "error": str(e)
            })

        except Exception as e:
            logger.error(f"Send error for user {user_id}: {e}")
            results.append({
                "userId": user_id,
                "success": False,
                "error": str(e)
            })

    return results


def save_subscription(user_id: str, subscription_data: Dict) -> bool:
    """
    Save push subscription to Azure File Storage
    """
    try:
        # TODO: Implement Azure File Storage integration
        # For now, store in memory (should be replaced with persistent storage)

        # Example implementation:
        # connection_string = os.getenv("AzureWebJobsStorage")
        # share_name = os.getenv("AZURE_FILES_SHARE_NAME")
        # file_path = f"subscriptions/{user_id}.json"

        # file_client = ShareFileClient.from_connection_string(
        #     connection_string,
        #     share_name,
        #     file_path
        # )

        # file_client.upload_file(json.dumps(subscription_data))

        logger.info(f"Subscription saved for user: {user_id}")
        return True

    except Exception as e:
        logger.error(f"Save subscription error: {e}")
        return False


def get_subscription(user_id: str) -> Optional[Dict]:
    """
    Get push subscription from storage
    """
    try:
        # TODO: Implement Azure File Storage integration
        # For now, return None (should be replaced with persistent storage)

        # Example implementation:
        # connection_string = os.getenv("AzureWebJobsStorage")
        # share_name = os.getenv("AZURE_FILES_SHARE_NAME")
        # file_path = f"subscriptions/{user_id}.json"

        # file_client = ShareFileClient.from_connection_string(
        #     connection_string,
        #     share_name,
        #     file_path
        # )

        # data = file_client.download_file().readall()
        # return json.loads(data)

        return None

    except Exception as e:
        logger.error(f"Get subscription error: {e}")
        return None


def remove_subscription_by_endpoint(endpoint: str) -> bool:
    """
    Remove subscription by endpoint
    """
    try:
        # TODO: Implement Azure File Storage integration
        # Search for subscription with matching endpoint and remove it

        logger.info(f"Subscription removed for endpoint: {endpoint}")
        return True

    except Exception as e:
        logger.error(f"Remove subscription error: {e}")
        return False


def get_all_subscriptions() -> List[Dict]:
    """
    Get all active subscriptions
    """
    try:
        # TODO: Implement Azure File Storage integration
        # List all subscription files and return active ones

        return []

    except Exception as e:
        logger.error(f"Get all subscriptions error: {e}")
        return []


# Main function handler
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main handler for push notification functions
    Route based on path
    """

    # Handle CORS preflight
    if req.method == "OPTIONS":
        return build_cors_response("", status_code=200)

    # Get route path
    route = req.route_params.get('route', '')

    if route == 'subscribe':
        return push_subscribe_handler(req)
    elif route == 'unsubscribe':
        return push_unsubscribe_handler(req)
    elif route == 'send':
        return push_send_handler(req)
    else:
        return build_cors_response(
            json.dumps({"error": "Invalid route"}),
            status_code=404
        )
