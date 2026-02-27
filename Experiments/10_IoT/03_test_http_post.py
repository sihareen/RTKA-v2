#!/usr/bin/env python3
"""
Bab 10: Test HTTP POST Request - Basic
=======================================
Program sederhana untuk test HTTP POST request

Install:
  pip3 install requests
"""

import requests
import json
import time

print("="*50)
print("Test HTTP POST Request - Basic")
print("="*50)

# Test 1: Simple POST with JSON Data
print("\n[Test 1] POST JSON Data")
print("-" * 50)

try:
    url = "https://httpbin.org/post"
    
    data = {
        'robot_id': 'RTKA-001',
        'status': 'active',
        'battery': 85,
        'location': {'x': 10, 'y': 20}
    }
    
    print(f"Posting to: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"✅ Server received data:")
        print(json.dumps(result['json'], indent=2))
    else:
        print(f"❌ Status: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: POST Form Data
print("\n\n[Test 2] POST Form Data")
print("-" * 50)

try:
    url = "https://httpbin.org/post"
    
    form_data = {
        'username': 'robot_admin',
        'device_name': 'RTKA Robot',
        'timestamp': str(time.time())
    }
    
    print(f"Posting form data...")
    print(f"Form: {form_data}")
    
    response = requests.post(url, data=form_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"✅ Form data received:")
        for key, value in result['form'].items():
            print(f"   {key}: {value}")
    else:
        print(f"❌ Status: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: POST with Headers and Authentication
print("\n\n[Test 3] POST with Headers")
print("-" * 50)

try:
    url = "https://httpbin.org/post"
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'RTKA-Robot/1.0',
        'X-Device-ID': 'RTKA-001'
    }
    
    data = {
        'sensor_data': {
            'temperature': 25.5,
            'humidity': 60,
            'distance': 150
        },
        'timestamp': time.time()
    }
    
    print(f"Posting with custom headers...")
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"✅ Headers sent:")
        for key, value in result['headers'].items():
            if key.startswith('X-') or key == 'User-Agent':
                print(f"   {key}: {value}")
    else:
        print(f"❌ Status: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: POST Sensor Data (IoT Simulation)
print("\n\n[Test 4] POST IoT Sensor Data")
print("-" * 50)

try:
    url = "https://httpbin.org/post"
    
    # Simulate sensor readings
    sensor_payload = {
        'device': {
            'id': 'RTKA-001',
            'type': 'mobile_robot',
            'location': 'Lab A'
        },
        'sensors': {
            'ultrasonic': {
                'distance_cm': 45,
                'unit': 'cm'
            },
            'battery': {
                'voltage': 7.4,
                'percentage': 85,
                'unit': 'V'
            },
            'motors': {
                'left_speed': 50,
                'right_speed': 50,
                'unit': 'percent'
            }
        },
        'timestamp': int(time.time()),
        'status': 'operational'
    }
    
    print("Sending sensor data to cloud...")
    print("Payload size:", len(json.dumps(sensor_payload)), "bytes")
    
    response = requests.post(url, json=sensor_payload, timeout=5)
    
    if response.status_code == 200:
        print(f"\n✅ Data uploaded successfully")
        print(f"✅ Response time: {response.elapsed.total_seconds():.2f}s")
        print(f"✅ Server confirmed receipt of {len(sensor_payload)} fields")
    else:
        print(f"❌ Upload failed: {response.status_code}")
        
except requests.Timeout:
    print("❌ Request timeout")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 5: POST with Response Validation
print("\n\n[Test 5] POST with Response Validation")
print("-" * 50)

try:
    url = "https://httpbin.org/post"
    
    data = {
        'action': 'update_status',
        'robot_id': 'RTKA-001',
        'new_status': 'charging'
    }
    
    print("Posting command...")
    
    response = requests.post(url, json=data)
    
    # Validate response
    if response.status_code == 200:
        result = response.json()
        
        # Check if server received correct data
        received = result.get('json', {})
        if received.get('robot_id') == data['robot_id']:
            print("\n✅ Command sent successfully")
            print(f"✅ Robot ID verified: {received['robot_id']}")
            print(f"✅ New status: {received['new_status']}")
        else:
            print("⚠️  Data mismatch in response")
    else:
        print(f"❌ Command failed: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*50)
print("✅ All POST request tests completed!")
print("="*50)

"""
PENJELASAN PROGRAM:
==================
Program ini mendemonstrasikan HTTP POST requests untuk mengirim data ke server,
essential untuk IoT data logging, command sending, dan API interactions.

HTTP POST Method:
POST adalah HTTP method untuk mengirim data ke server untuk processing atau storage.
POST requests:
- Modify/create data di server (not idempotent)
- Data dikirim di request body (not di URL)
- No size limit (praktis, dibanding GET)
- Tidak bisa di-cache
- Tidak bisa di-bookmark
- More secure untuk sensitive data

POST vs GET:
GET:
- Retrieve data (read)
- Parameters di URL
- Idempotent (safe to repeat)
- Can be cached
- Data visible di URL/logs

POST:
- Send data untuk processing
- Data di request body
- Not idempotent
- Cannot be cached
- Data not visible di URL

POST Data Formats:

1. JSON (application/json):
```python
data = {'key': 'value'}
response = requests.post(url, json=data)
# Auto sets Content-Type: application/json
```

2. Form Data (application/x-www-form-urlencoded):
```python
data = {'key': 'value'}
response = requests.post(url, data=data)
# Like HTML form submission
```

3. Multipart Form (multipart/form-data):
```python
files = {'file': open('image.jpg', 'rb')}
response = requests.post(url, files=files)
# For file uploads
```

4. Raw Data (custom Content-Type):
```python
data = '<xml>content</xml>'
headers = {'Content-Type': 'application/xml'}
response = requests.post(url, data=data, headers=headers)
```

JSON POST Request:
Most common untuk APIs:
```python
import requests

url = "https://api.example.com/data"
payload = {
    'sensor_id': 'temp_01',
    'value': 25.5,
    'unit': 'celsius'
}

response = requests.post(url, json=payload)
```

The `json=payload` parameter:
- Automatically serializes dict to JSON
- Sets Content-Type: application/json
- Sends data di request body

Form Data POST:
Traditional HTML form style:
```python
data = {
    'username': 'user',
    'password': 'pass'
}
response = requests.post(url, data=data)
# Content-Type: application/x-www-form-urlencoded
```

POST with Headers:
Custom headers untuk authentication, content-type, dll:
```python
headers = {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json',
    'X-API-Key': 'your_api_key'
}
response = requests.post(url, json=data, headers=headers)
```

Response Handling:
```python
response = requests.post(url, json=data)

if response.status_code == 200:
    # Success - OK
    result = response.json()
elif response.status_code == 201:
    # Success - Created
    print("Resource created")
elif response.status_code == 400:
    # Client error - Bad Request
    print("Invalid data")
elif response.status_code == 401:
    # Unauthorized
    print("Authentication required")
elif response.status_code == 500:
    # Server error
    print("Server error")
```

Error Handling:
```python
try:
    response = requests.post(url, json=data, timeout=5)
    response.raise_for_status()  # Raise for 4xx/5xx
    
    result = response.json()
    print("Success:", result)
    
except requests.ConnectionError:
    print("Connection failed")
except requests.Timeout:
    print("Request timeout")
except requests.HTTPError as e:
    print(f"HTTP error: {e.response.status_code}")
except requests.RequestException as e:
    print(f"Request failed: {e}")
except json.JSONDecodeError:
    print("Invalid JSON response")
```

File Upload:
POST files dengan multipart/form-data:
```python
# Single file
files = {'file': open('data.csv', 'rb')}
response = requests.post(url, files=files)

# Multiple files
files = {
    'file1': open('image1.jpg', 'rb'),
    'file2': open('image2.jpg', 'rb')
}
response = requests.post(url, files=files)

# File with additional data
files = {'file': open('data.csv', 'rb')}
data = {'description': 'Sensor data', 'date': '2024-01-01'}
response = requests.post(url, files=files, data=data)
```

Authentication:

1. Bearer Token:
```python
headers = {'Authorization': f'Bearer {token}'}
response = requests.post(url, json=data, headers=headers)
```

2. Basic Auth:
```python
response = requests.post(url, json=data, 
                        auth=('username', 'password'))
```

3. API Key in Header:
```python
headers = {'X-API-Key': 'your_api_key'}
response = requests.post(url, json=data, headers=headers)
```

4. OAuth2:
```python
token = get_oauth_token()
headers = {'Authorization': f'Bearer {token}'}
response = requests.post(url, json=data, headers=headers)
```

Real-World Use Cases:

1. IoT Data Logging:
```python
# Send sensor data to cloud
data = {
    'device_id': 'SENSOR_01',
    'temperature': 25.5,
    'humidity': 60,
    'timestamp': time.time()
}
response = requests.post('https://iot.example.com/api/data', json=data)
```

2. Robot Command:
```python
# Send command to robot via API
command = {
    'robot_id': 'ROBOT_01',
    'action': 'move_forward',
    'speed': 50,
    'duration': 5
}
response = requests.post('https://robot.example.com/api/command', json=command)
```

3. User Registration:
```python
# Create new user account
user_data = {
    'username': 'newuser',
    'email': 'user@example.com',
    'password': 'hashed_password'
}
response = requests.post('https://api.example.com/register', json=user_data)
```

4. Data Storage:
```python
# Save measurement to database
measurement = {
    'sensor_type': 'temperature',
    'value': 25.5,
    'location': 'room_A',
    'timestamp': int(time.time())
}
response = requests.post('https://api.example.com/measurements', json=measurement)
```

5. Webhook/Callback:
```python
# Notify external service
notification = {
    'event': 'motion_detected',
    'device': 'camera_01',
    'timestamp': time.time()
}
response = requests.post('https://webhook.example.com/notify', json=notification)
```

Batch POST:
Send multiple records at once:
```python
readings = [
    {'sensor': 'temp_01', 'value': 25.5, 'time': time.time()},
    {'sensor': 'temp_02', 'value': 26.1, 'time': time.time()},
    {'sensor': 'temp_03', 'value': 24.8, 'time': time.time()}
]
response = requests.post(url, json={'readings': readings})
```

Response Validation:
Verify server processed data correctly:
```python
response = requests.post(url, json=data)

if response.status_code == 201:  # Created
    result = response.json()
    
    # Check response contains expected fields
    if 'id' in result:
        print(f"Created with ID: {result['id']}")
    
    # Verify data echoed back
    if result.get('status') == 'success':
        print("Data saved successfully")
```

Retry Logic:
Handle temporary failures:
```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(
    total=3,              # 3 retries
    backoff_factor=0.3,   # Wait: 0.3, 0.6, 1.2 seconds
    status_forcelist=[500, 502, 503, 504]  # Retry for these errors
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

response = session.post(url, json=data)
```

Rate Limiting:
Respect API rate limits:
```python
import time

for data in sensor_readings:
    response = requests.post(url, json=data)
    
    if response.status_code == 429:  # Too Many Requests
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"Rate limited. Waiting {retry_after}s...")
        time.sleep(retry_after)
    
    time.sleep(1)  # Throttle requests
```

Testing POST Endpoints:

1. HTTPBin (https://httpbin.org):
   - /post: echo POST data
   - /status/code: test specific status codes
   - /delay/n: test timeouts

2. JSONPlaceholder (https://jsonplaceholder.typicode.com):
   - /posts: create fake post
   - /users: create fake user
   - Returns JSON response

3. RequestBin / Webhook.site:
   - Inspect incoming POST requests
   - Useful untuk debugging webhooks

Common POST Errors:

400 Bad Request:
- Invalid JSON format
- Missing required fields
- Invalid data types
- Solution: Validate data before sending

401 Unauthorized:
- Missing authentication
- Invalid credentials
- Expired token
- Solution: Check auth headers/credentials

403 Forbidden:
- Authenticated but no permission
- API key not authorized
- Solution: Verify permissions

413 Payload Too Large:
- Request body too big
- Solution: Reduce data size or batch

422 Unprocessable Entity:
- Valid format but semantic errors
- Business logic validation failed
- Solution: Check data values

429 Too Many Requests:
- Rate limit exceeded
- Solution: Implement backoff/retry

500 Internal Server Error:
- Server-side error
- Solution: Contact API provider, check logs

Best Practices:

1. Always set timeout:
```python
response = requests.post(url, json=data, timeout=5)
```

2. Validate data before sending:
```python
def validate_sensor_data(data):
    required = ['device_id', 'value', 'timestamp']
    return all(k in data for k in required)

if validate_sensor_data(data):
    response = requests.post(url, json=data)
```

3. Handle errors gracefully:
```python
try:
    response = requests.post(url, json=data)
    response.raise_for_status()
except Exception as e:
    log_error(e)
    # Fallback: save to local queue
```

4. Use HTTPS for sensitive data:
```python
# Always use https:// not http://
url = "https://api.example.com/data"  # ✅
# url = "http://api.example.com/data"  # ❌
```

5. Log requests untuk debugging:
```python
import logging

logging.info(f"POST {url}: {data}")
response = requests.post(url, json=data)
logging.info(f"Response: {response.status_code}")
```

6. Use environment variables untuk secrets:
```python
import os

API_KEY = os.getenv('API_KEY')
headers = {'Authorization': f'Bearer {API_KEY}'}
```

7. Compress large payloads:
```python
import gzip

data = large_json_string
compressed = gzip.compress(data.encode())
headers = {'Content-Encoding': 'gzip'}
response = requests.post(url, data=compressed, headers=headers)
```

Robot/IoT Applications:
- Upload sensor telemetry to cloud
- Send commands to actuators
- Log events dan errors
- Update configuration
- Report status
- Trigger alerts/notifications
- Store training data
- Submit task results
- Register devices
- Send heartbeats

HTTP POST adalah fundamental untuk IoT applications yang perlu send data ke cloud
platforms, APIs, dan remote services untuk monitoring, control, dan analytics.
"""
