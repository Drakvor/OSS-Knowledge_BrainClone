# Knowledge Base: Software Development Best Practices

## Version Control with Git

### What is Git?

Git is a distributed version control system that tracks changes in source code during software development. It allows multiple developers to work on the same project simultaneously without conflicts.

Key concepts:
- **Repository**: A directory containing your project and its history
- **Commit**: A snapshot of your project at a specific point in time
- **Branch**: A parallel version of your repository
- **Merge**: Combining changes from different branches

### Essential Git Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `git init` | Initialize a new repository | `git init my-project` |
| `git clone` | Copy a remote repository | `git clone https://github.com/user/repo.git` |
| `git add` | Stage changes for commit | `git add file.txt` |
| `git commit` | Save changes to repository | `git commit -m "Add new feature"` |
| `git push` | Upload changes to remote | `git push origin main` |
| `git pull` | Download changes from remote | `git pull origin main` |

### Branching Strategy

We recommend the **Git Flow** branching model:

```
main branch (production-ready code)
├── develop branch (integration branch)
│   ├── feature/user-authentication
│   ├── feature/payment-integration
│   └── feature/email-notifications
├── release/v1.2.0 (prepare for release)
└── hotfix/critical-bug-fix
```

**Branch naming conventions**:
- `feature/feature-name`: New features
- `bugfix/bug-description`: Bug fixes
- `release/version-number`: Release preparation
- `hotfix/issue-description`: Critical production fixes

## Code Review Process

### Why Code Reviews?

Code reviews are essential for:
1. **Quality assurance**: Catch bugs and issues early
2. **Knowledge sharing**: Team members learn from each other
3. **Consistency**: Maintain coding standards across the team
4. **Mentoring**: Help junior developers improve

### Review Checklist

Before submitting code for review:

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New features have appropriate tests
- [ ] Documentation is updated
- [ ] No sensitive information (passwords, API keys) in code
- [ ] Performance impact considered
- [ ] Security implications reviewed

### Review Guidelines

**For Reviewers**:

> Always be constructive and respectful in your feedback. Remember that there's a person behind the code.

Focus on:
- **Logic and algorithm correctness**
- **Code readability and maintainability** 
- **Potential security vulnerabilities**
- **Performance bottlenecks**
- **Test coverage**

**Sample feedback format**:
```
// Instead of: "This is wrong"
// Say: "Consider using a Set here for O(1) lookup instead of Array.includes() for better performance"

// Instead of: "Bad variable name"  
// Say: "Could we use a more descriptive name like 'userPermissions' instead of 'perms'?"
```

## Testing Best Practices

### Testing Pyramid

Structure your tests following the testing pyramid:

```
        /\
       /  \
      / UI \     <- Few, slow, expensive
     /Tests\
    /______\
   /        \
   /Integration\ <- Some, moderate speed
  /   Tests    \
 /______________\
/                \
/   Unit Tests   \  <- Many, fast, cheap
/________________\
```

### Unit Testing

Unit tests verify individual components in isolation:

```python
import unittest
from calculator import Calculator

class TestCalculator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.calc = Calculator()
    
    def test_addition(self):
        """Test addition operation."""
        result = self.calc.add(2, 3)
        self.assertEqual(result, 5)
    
    def test_division_by_zero(self):
        """Test division by zero raises appropriate exception."""
        with self.assertRaises(ZeroDivisionError):
            self.calc.divide(10, 0)
    
    def test_negative_numbers(self):
        """Test operations with negative numbers."""
        result = self.calc.multiply(-5, 3)
        self.assertEqual(result, -15)

if __name__ == '__main__':
    unittest.main()
```

### Test-Driven Development (TDD)

TDD follows a simple cycle:

1. **Red**: Write a failing test
2. **Green**: Write minimal code to make it pass
3. **Refactor**: Improve the code while keeping tests green

```python
# Step 1: Write failing test
def test_user_can_login_with_valid_credentials():
    user = User("john@example.com", "password123")
    result = user.login("john@example.com", "password123")
    assert result.success == True
    assert result.user_id == user.id

# Step 2: Write minimal implementation
class User:
    def login(self, email, password):
        if email == self.email and password == self.password:
            return LoginResult(success=True, user_id=self.id)
        return LoginResult(success=False)

# Step 3: Refactor and improve
```

## Security Guidelines

### Input Validation

**Always validate and sanitize user input**:

```python
import re

def validate_email(email):
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_input(user_input):
    """Remove potentially harmful characters."""
    # Remove HTML tags
    clean_input = re.sub(r'<[^>]+>', '', user_input)
    # Remove special characters that could be used for injection
    clean_input = re.sub(r'[<>"\';\\&]', '', clean_input)
    return clean_input.strip()

# Example usage
email = request.form.get('email')
if not validate_email(email):
    return {"error": "Invalid email format"}, 400

comment = sanitize_input(request.form.get('comment'))
```

### Authentication and Authorization

Implement proper authentication and authorization:

```python
from functools import wraps
import jwt

def require_auth(f):
    """Decorator to require authentication for endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return {"error": "No token provided"}, 401
        
        try:
            # Remove 'Bearer ' prefix
            token = token.split(' ')[1]
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}, 401
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}, 401
        
        return f(current_user_id, *args, **kwargs)
    return decorated_function

@app.route('/api/profile')
@require_auth
def get_profile(current_user_id):
    # User is authenticated, proceed with request
    user = User.get_by_id(current_user_id)
    return user.to_dict()
```

### Password Security

**Never store passwords in plain text**:

```python
import bcrypt

def hash_password(password):
    """Hash a password for storing in database."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password, hashed):
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# Usage example
class User:
    def __init__(self, email, password):
        self.email = email
        self.password_hash = hash_password(password)
    
    def check_password(self, password):
        return verify_password(password, self.password_hash)
```

## Performance Optimization

### Database Optimization

**Use indexes for frequently queried columns**:

```sql
-- Create indexes for better query performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_products_category_id ON products(category_id);

-- Composite index for multiple column queries
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at);
```

**Avoid N+1 queries**:

```python
# BAD: N+1 query problem
users = User.query.all()  # 1 query
for user in users:
    orders = user.orders  # N queries (one per user)
    print(f"{user.name}: {len(orders)} orders")

# GOOD: Use eager loading
users = User.query.options(joinedload(User.orders)).all()  # 1 query
for user in users:
    print(f"{user.name}: {len(user.orders)} orders")
```

### Caching Strategies

Implement caching at different levels:

1. **Browser caching**: Set appropriate HTTP headers
2. **CDN caching**: For static assets
3. **Application caching**: Redis/Memcached for dynamic content
4. **Database query caching**: Cache expensive queries

```python
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration=3600):
    """Cache function result in Redis."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{f.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            
            return result
        return wrapper
    return decorator

@cache_result(expiration=1800)  # Cache for 30 minutes
def get_popular_products():
    # Expensive database query
    return Product.query.filter(Product.views > 1000).all()
```

## Monitoring and Logging

### Structured Logging

Use structured logging for better observability:

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'module': record.module,
            'message': record.getMessage(),
            'user_id': getattr(record, 'user_id', None),
            'request_id': getattr(record, 'request_id', None)
        }
        return json.dumps(log_entry)

# Configure logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage
logger.info("User logged in", extra={'user_id': 12345, 'request_id': 'abc-123'})
```

### Application Metrics

Monitor key application metrics:

```python
import time
from functools import wraps

class MetricsCollector:
    def __init__(self):
        self.request_count = 0
        self.response_times = []
        self.error_count = 0
    
    def time_request(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                self.request_count += 1
                return result
            except Exception as e:
                self.error_count += 1
                raise
            finally:
                duration = time.time() - start_time
                self.response_times.append(duration)
        return wrapper
    
    def get_stats(self):
        if not self.response_times:
            return {"requests": 0, "avg_response_time": 0, "errors": 0}
        
        avg_response = sum(self.response_times) / len(self.response_times)
        return {
            "requests": self.request_count,
            "avg_response_time": round(avg_response, 3),
            "errors": self.error_count,
            "error_rate": round(self.error_count / self.request_count, 3) if self.request_count > 0 else 0
        }

metrics = MetricsCollector()

@app.route('/api/users')
@metrics.time_request
def get_users():
    return User.query.all()

@app.route('/metrics')
def get_metrics():
    return metrics.get_stats()
```

## Documentation Standards

### API Documentation

Use OpenAPI/Swagger for API documentation:

```yaml
openapi: 3.0.0
info:
  title: User Management API
  version: 1.0.0
paths:
  /users:
    get:
      summary: Get all users
      responses:
        200:
          description: List of users
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
    post:
      summary: Create a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserCreate'
      responses:
        201:
          description: User created successfully
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        email:
          type: string
          format: email
        created_at:
          type: string
          format: date-time
```

### Code Documentation

Write clear docstrings for your functions:

```python
def calculate_compound_interest(principal: float, rate: float, 
                              time: int, compound_frequency: int = 1) -> float:
    """
    Calculate compound interest.
    
    Args:
        principal (float): Initial amount of money
        rate (float): Annual interest rate (as decimal, e.g., 0.05 for 5%)
        time (int): Number of years
        compound_frequency (int, optional): Number of times interest is 
            compounded per year. Defaults to 1.
    
    Returns:
        float: The final amount after compound interest
    
    Raises:
        ValueError: If any parameter is negative
    
    Example:
        >>> calculate_compound_interest(1000, 0.05, 10)
        1628.89
        >>> calculate_compound_interest(1000, 0.05, 10, 12)
        1643.62
    """
    if principal < 0 or rate < 0 or time < 0 or compound_frequency < 1:
        raise ValueError("All parameters must be non-negative, compound_frequency must be >= 1")
    
    return principal * (1 + rate / compound_frequency) ** (compound_frequency * time)
```

---

For more information, see:
- [Git Workflow Guide](./git-workflow.md)
- [Testing Framework Setup](./testing-setup.md)  
- [Security Checklist](./security-checklist.md)
- [Performance Monitoring](./monitoring.md)