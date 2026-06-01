import base64
import io
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicart.settings')

# Add the project root to sys.path so Django can be imported
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import django
django.setup()

from django.core.handlers.wsgi import WSGIHandler

_application = None


def _get_application():
    global _application
    if _application is None:
        _application = WSGIHandler()
    return _application


def handler(event, context):
    application = _get_application()

    method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')

    params = event.get('queryStringParameters') or {}
    if isinstance(params, dict):
        query_string = '&'.join(f'{k}={v}' for k, v in params.items())
    else:
        query_string = ''

    body = event.get('body') or ''
    if event.get('isBase64Encoded') and body:
        body_bytes = base64.b64decode(body)
    elif isinstance(body, str):
        body_bytes = body.encode('utf-8')
    else:
        body_bytes = body

    headers = event.get('headers') or {}

    environ = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'SERVER_NAME': headers.get('host', 'localhost'),
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'HTTPS': 'on',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': io.BytesIO(body_bytes),
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'CONTENT_LENGTH': str(len(body_bytes)),
        'CONTENT_TYPE': headers.get('content-type', ''),
    }

    for key, value in headers.items():
        key_upper = key.upper().replace('-', '_')
        if key_upper == 'CONTENT_TYPE':
            environ['CONTENT_TYPE'] = value
        elif key_upper == 'CONTENT_LENGTH':
            environ['CONTENT_LENGTH'] = value
        else:
            environ[f'HTTP_{key_upper}'] = value

    status_holder = [200]
    response_headers_holder = [{}]

    def start_response(status, response_headers, exc_info=None):
        status_holder[0] = int(status.split(' ')[0])
        response_headers_holder[0] = dict(response_headers)

    try:
        response_iter = application(environ, start_response)
        body_content = b''.join(response_iter)
    except Exception as exc:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/html; charset=utf-8'},
            'body': f'<h1>500 Internal Server Error</h1><pre>{exc}</pre>',
        }

    content_type = response_headers_holder[0].get('Content-Type', '')
    text_types = ('text/', 'application/json', 'application/javascript', 'application/xml', 'image/svg')
    is_text = any(t in content_type for t in text_types)

    if is_text:
        return {
            'statusCode': status_holder[0],
            'headers': response_headers_holder[0],
            'body': body_content.decode('utf-8', errors='replace'),
        }
    else:
        return {
            'statusCode': status_holder[0],
            'headers': response_headers_holder[0],
            'body': base64.b64encode(body_content).decode('utf-8'),
            'isBase64Encoded': True,
        }
