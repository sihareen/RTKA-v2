#!/usr/bin/env python3
"""
Bab 10: Test HTTP GET Request - Basic
======================================
Program sederhana untuk test HTTP GET request

Install:
  pip3 install requests
"""

import requests
import json

print("="*50)
print("Test HTTP GET Request - Basic")
print("="*50)

# Test 1: Simple GET Request
print("\n[Test 1] Simple GET Request")
print("-" * 50)

try:
    url = "https://api.github.com"
    print(f"Requesting: {url}")
    
    response = requests.get(url)
    
    print(f"\n✅ Status Code: {response.status_code}")
    print(f"✅ Response Time: {response.elapsed.total_seconds():.2f}s")
    print(f"✅ Content Type: {response.headers['Content-Type']}")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: GET with Parameters
print("\n\n[Test 2] GET with Query Parameters")
print("-" * 50)

try:
    url = "https://api.github.com/search/repositories"
    params = {
        'q': 'raspberry pi robot',
        'sort': 'stars',
        'order': 'desc',
        'per_page': 3
    }
    
    print(f"URL: {url}")
    print(f"Parameters: {params}")
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Found {data['total_count']} repositories")
        print("\nTop 3 repositories:")
        
        for i, repo in enumerate(data['items'], 1):
            print(f"{i}. {repo['name']}")
            print(f"   Stars: {repo['stargazers_count']}")
            print(f"   URL: {repo['html_url']}")
    else:
        print(f"❌ Status: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: GET Public API (Weather Example)
print("\n\n[Test 3] GET Real-world API")
print("-" * 50)

try:
    # Using wttr.in - simple weather API (no auth required)
    url = "https://wttr.in/Jakarta?format=j1"
    
    print(f"Requesting weather data for Jakarta...")
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        current = data['current_condition'][0]
        
        print(f"\n✅ Current Weather in Jakarta:")
        print(f"   Temperature: {current['temp_C']}°C")
        print(f"   Feels Like: {current['FeelsLikeC']}°C")
        print(f"   Humidity: {current['humidity']}%")
        print(f"   Weather: {current['weatherDesc'][0]['value']}")
    else:
        print(f"❌ Status: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: GET with Headers
print("\n\n[Test 4] GET with Custom Headers")
print("-" * 50)

try:
    url = "https://httpbin.org/headers"
    
    headers = {
        'User-Agent': 'RTKA-Robot/1.0',
        'Accept': 'application/json',
        'Custom-Header': 'Test-Value'
    }
    
    print(f"Sending request with custom headers...")
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Server received headers:")
        for key, value in data['headers'].items():
            print(f"   {key}: {value}")
    else:
        print(f"❌ Status: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Test 5: GET with Timeout
print("\n\n[Test 5] GET with Timeout")
print("-" * 50)

try:
    url = "https://httpbin.org/delay/2"
    timeout = 5
    
    print(f"Request with {timeout}s timeout...")
    
    response = requests.get(url, timeout=timeout)
    
    print(f"✅ Request completed in {response.elapsed.total_seconds():.2f}s")
    
except requests.Timeout:
    print(f"❌ Request timeout after {timeout}s")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*50)
print("✅ All GET request tests completed!")
print("="*50)

"""
PENJELASAN PROGRAM:
==================
Program ini mendemonstrasikan HTTP GET requests menggunakan library requests untuk
komunikasi dengan web APIs dan web services.

HTTP GET Method:
GET adalah HTTP method untuk retrieve/mendapatkan data dari server. GET requests:
- Tidak mengubah data di server (read-only, idempotent)
- Parameters dikirim di URL query string
- Bisa di-cache oleh browser/proxy
- Bisa di-bookmark
- Limited data size (URL length limit ~2000 chars)

Requests Library:
Library Python yang paling populer untuk HTTP requests. Lebih mudah digunakan
dibanding urllib (Python built-in). Features:
- Simple API
- Automatic JSON encoding/decoding
- Session support dengan cookies
- SSL verification
- Connection pooling
- Timeouts dan retries

Basic GET Request:
```python
response = requests.get(url)
```

Response Object Properties:
- response.status_code: HTTP status code (200, 404, 500, etc)
- response.text: response body sebagai string
- response.content: response body sebagai bytes
- response.json(): parse JSON response
- response.headers: response headers (dict-like)
- response.cookies: cookies dari server
- response.url: final URL (after redirects)
- response.elapsed: request duration (timedelta)
- response.ok: True jika status 200-399

HTTP Status Codes:
- 2xx Success:
  * 200 OK: request berhasil
  * 201 Created: resource created
  * 204 No Content: success, no response body

- 3xx Redirection:
  * 301 Moved Permanently
  * 302 Found (temporary redirect)
  * 304 Not Modified (cached)

- 4xx Client Error:
  * 400 Bad Request: invalid request
  * 401 Unauthorized: authentication required
  * 403 Forbidden: no permission
  * 404 Not Found: resource tidak ada
  * 429 Too Many Requests: rate limit

- 5xx Server Error:
  * 500 Internal Server Error
  * 502 Bad Gateway
  * 503 Service Unavailable
  * 504 Gateway Timeout

Query Parameters:
Cara 1 - Manual di URL:
```python
url = "https://api.example.com/search?q=robot&limit=10"
response = requests.get(url)
```

Cara 2 - Dict (Recommended):
```python
params = {'q': 'robot', 'limit': 10}
response = requests.get(url, params=params)
# Automatically encoded: https://api.example.com/search?q=robot&limit=10
```

Headers:
Custom headers untuk authentication, content negotiation, dll:
```python
headers = {
    'Authorization': 'Bearer YOUR_TOKEN',
    'User-Agent': 'MyApp/1.0',
    'Accept': 'application/json'
}
response = requests.get(url, headers=headers)
```

Common Headers:
- User-Agent: identify client application
- Accept: preferred response format (application/json, text/html)
- Authorization: authentication credentials
- Content-Type: request body format (untuk POST/PUT)
- Accept-Language: preferred language
- Cache-Control: caching directives

Authentication:

1. Bearer Token:
```python
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(url, headers=headers)
```

2. Basic Auth:
```python
response = requests.get(url, auth=('username', 'password'))
```

3. API Key (query param):
```python
params = {'api_key': 'YOUR_API_KEY'}
response = requests.get(url, params=params)
```

4. API Key (header):
```python
headers = {'X-API-Key': 'YOUR_API_KEY'}
response = requests.get(url, headers=headers)
```

JSON Response Handling:
```python
response = requests.get('https://api.example.com/data')

# Check status first
if response.status_code == 200:
    data = response.json()  # Parse JSON
    print(data['key'])
else:
    print(f"Error: {response.status_code}")
```

Error Handling:
```python
try:
    response = requests.get(url, timeout=5)
    response.raise_for_status()  # Raise exception for 4xx/5xx
    data = response.json()
except requests.ConnectionError:
    print("Connection failed")
except requests.Timeout:
    print("Request timeout")
except requests.HTTPError as e:
    print(f"HTTP error: {e}")
except requests.RequestException as e:
    print(f"Request failed: {e}")
```

Timeout:
ALWAYS set timeout untuk avoid hanging indefinitely:
```python
response = requests.get(url, timeout=5)  # 5 seconds
response = requests.get(url, timeout=(3, 10))  # (connect, read)
```

Sessions:
Untuk multiple requests, use Session untuk reuse connection:
```python
session = requests.Session()
session.headers.update({'User-Agent': 'MyApp/1.0'})

# Reuse connection
response1 = session.get('https://api.example.com/data1')
response2 = session.get('https://api.example.com/data2')
```

Benefits:
- Connection pooling (faster)
- Cookie persistence
- Default headers

SSL Verification:
By default, requests verify SSL certificates. Untuk disable (not recommended):
```python
response = requests.get(url, verify=False)  # Disable SSL verify
```

Redirects:
Requests automatically follows redirects (up to 30). Untuk disable:
```python
response = requests.get(url, allow_redirects=False)
```

Streaming Large Responses:
Untuk large files, stream response:
```python
response = requests.get(url, stream=True)
for chunk in response.iter_content(chunk_size=8192):
    process_chunk(chunk)
```

Real-World Use Cases:

1. Weather Data:
```python
url = "https://api.openweathermap.org/data/2.5/weather"
params = {'q': 'Jakarta', 'appid': API_KEY, 'units': 'metric'}
response = requests.get(url, params=params)
weather = response.json()
temp = weather['main']['temp']
```

2. GitHub API:
```python
url = f"https://api.github.com/users/{username}"
response = requests.get(url)
user = response.json()
print(f"Name: {user['name']}, Repos: {user['public_repos']}")
```

3. IoT Platform:
```python
# Get sensor data from cloud
url = f"https://iot.example.com/api/devices/{device_id}/data"
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(url, headers=headers)
sensor_data = response.json()
```

4. REST API Query:
```python
# Search database via API
url = "https://api.example.com/products"
params = {'category': 'electronics', 'max_price': 1000}
response = requests.get(url, params=params)
products = response.json()['results']
```

Testing APIs:
1. HTTPBin (https://httpbin.org):
   - /get: test GET request
   - /headers: inspect headers
   - /delay/n: test timeout
   - /status/code: test status codes

2. JSONPlaceholder (https://jsonplaceholder.typicode.com):
   - Fake REST API untuk testing
   - /posts, /users, /comments

3. Public APIs:
   - GitHub API (no auth for public data)
   - OpenWeatherMap (free tier)
   - REST Countries
   - NASA APIs

Rate Limiting:
Many APIs have rate limits. Handle dengan:
```python
response = requests.get(url)
if response.status_code == 429:  # Too Many Requests
    retry_after = int(response.headers.get('Retry-After', 60))
    print(f"Rate limited. Retry after {retry_after}s")
    time.sleep(retry_after)
```

Best Practices:
1. Always set timeout
2. Check status_code before parsing
3. Use try-except untuk handle errors  
4. Use Session untuk multiple requests
5. Follow API documentation
6. Respect rate limits
7. Use environment variables untuk API keys
8. Log requests untuk debugging
9. Use proper User-Agent
10. Verify SSL certificates (don't disable di production)

Robot/IoT Applications:
- Get weather data untuk outdoor robots
- Query cloud database untuk configurations
- Check firmware updates
- Fetch map/navigation data
- Get AI model weights
- Query knowledge base
- Retrieve sensor calibration data
- Check server status
- Download resources
- Integration dengan third-party services

HTTP GET adalah foundation untuk consuming web APIs, making it essential untuk
modern IoT dan robot applications yang communicate dengan cloud services.
"""
