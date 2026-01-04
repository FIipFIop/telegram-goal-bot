"""
Simple test endpoint to verify Vercel is working.
"""

def handler(request):
    """Simple test handler."""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"status": "success", "message": "Vercel is working!"}'
    }
