import json
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from main import app
from mangum import Mangum

# Create the Mangum handler for Netlify Functions
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """Netlify Functions entry point"""
    try:
        return handler(event, context)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Internal server error'
            })
        }