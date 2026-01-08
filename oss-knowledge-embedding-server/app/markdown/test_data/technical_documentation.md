# API Documentation

## Authentication

All API requests require authentication using an API key. Include your key in the header:

```http
Authorization: Bearer your-api-key-here
```

### Getting an API Key

1. Sign up for an account
2. Navigate to the **API Keys** section
3. Click "Generate New Key"
4. Copy and store your key securely

**Important**: Keep your API keys secure and never commit them to version control.

## User Endpoints

### Create User

Creates a new user account in the system.

**Endpoint**: `POST /api/users`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| username | string | Yes | Unique username (3-50 chars) |
| email | string | Yes | Valid email address |
| password | string | Yes | Password (min 8 chars) |
| profile | object | No | Additional profile information |

**Example Request**:

```javascript
const response = await fetch('/api/users', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-api-key'
  },
  body: JSON.stringify({
    username: 'johndoe',
    email: 'john@example.com',
    password: 'securepassword123',
    profile: {
      firstName: 'John',
      lastName: 'Doe'
    }
  })
});
```

**Response Example**:

```json
{
  "success": true,
  "data": {
    "id": 12345,
    "username": "johndoe",
    "email": "john@example.com",
    "created_at": "2023-10-15T10:30:00Z",
    "profile": {
      "firstName": "John",
      "lastName": "Doe"
    }
  }
}
```

### Get User

Retrieves user information by ID.

**Endpoint**: `GET /api/users/{id}`

```python
import requests

def get_user(user_id, api_key):
    """
    Fetch user information from the API.
    
    Args:
        user_id (int): The user's ID
        api_key (str): Your API authentication key
    
    Returns:
        dict: User information or None if not found
    """
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(f'/api/users/{user_id}', headers=headers)
    
    if response.status_code == 200:
        return response.json()['data']
    return None

# Usage example
user = get_user(12345, 'your-api-key')
if user:
    print(f"User: {user['username']}")
```

### Update User

Updates existing user information. Only provided fields will be updated.

**Endpoint**: `PATCH /api/users/{id}`

The update operation supports partial updates. You can update specific fields:

- **username**: Change the username (must be unique)
- **email**: Update email address (must be valid)
- **profile**: Update profile information (merged with existing)

```bash
# Update user email using curl
curl -X PATCH /api/users/12345 \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"email": "newemail@example.com"}'
```

## Data Models

### User Model

The User model represents a system user with the following properties:

```typescript
interface User {
  id: number;           // Unique identifier
  username: string;     // Username (3-50 characters)
  email: string;        // Email address
  created_at: string;   // ISO timestamp
  updated_at: string;   // ISO timestamp
  profile?: {           // Optional profile data
    firstName?: string;
    lastName?: string;
    avatar?: string;
    bio?: string;
  };
  preferences?: {       // User preferences
    theme: 'light' | 'dark';
    notifications: boolean;
    language: string;
  };
}
```

## Error Handling

All API endpoints return consistent error responses:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "username": "Username must be at least 3 characters",
      "email": "Invalid email format"
    }
  }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Request validation failed | 400 |
| `UNAUTHORIZED` | Invalid or missing API key | 401 |
| `FORBIDDEN` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `RATE_LIMIT` | Too many requests | 429 |
| `SERVER_ERROR` | Internal server error | 500 |

## Rate Limiting

API requests are limited to prevent abuse:

- **Free tier**: 100 requests per hour
- **Pro tier**: 1,000 requests per hour  
- **Enterprise**: 10,000 requests per hour

Rate limit headers are included in all responses:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1634567890
```

> **Note**: When you exceed the rate limit, you'll receive a 429 status code. Implement exponential backoff in your client applications.

## SDKs and Libraries

Official SDKs are available for popular programming languages:

- **JavaScript/Node.js**: `npm install @myapi/sdk`
- **Python**: `pip install myapi-python`
- **Go**: `go get github.com/myapi/go-sdk`
- **Ruby**: `gem install myapi-ruby`

### SDK Example

```python
from myapi import Client

# Initialize client
client = Client(api_key='your-api-key')

# Create a user
user = client.users.create({
    'username': 'alice',
    'email': 'alice@example.com',
    'password': 'secure123'
})

# Get user by ID
user = client.users.get(user.id)

# Update user
client.users.update(user.id, {'email': 'alice.new@example.com'})
```

## Webhooks

Configure webhooks to receive real-time notifications about events in your account.

### Supported Events

- `user.created` - New user registration
- `user.updated` - User profile changes
- `user.deleted` - User account deletion

### Webhook Configuration

Set up webhooks in your dashboard or via API:

```javascript
const webhook = await client.webhooks.create({
  url: 'https://yourapp.com/webhooks/myapi',
  events: ['user.created', 'user.updated'],
  secret: 'webhook-signing-secret'
});
```

For more information, see the [Webhook Guide](./webhooks.md) and [Security Best Practices](./security.md).