# 🏗️ Beiyangu Backend

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org/)
[![Django](https://img.shields.io/badge/django-4.2%2B-green.svg)](https://djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-13%2B-blue.svg)](https://postgresql.org/)
[![Docker](https://img.shields.io/badge/docker-enabled-blue.svg)](https://docker.com/)
[![Railway](https://img.shields.io/badge/deployed-railway-success.svg)](https://railway.app/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **Beiyangu** (Swahili: "My Price") - A robust backend API for a reverse marketplace where buyers post requests, sellers bid, and funds are held in simulated escrow until delivery completion.

## 🌐 Live API

**Production URL**: [https://beiyangu.up.railway.app/](https://beiyangu.up.railway.app/)

**API Documentation**: [https://beiyangu.up.railway.app/api/](https://beiyangu.up.railway.app/api/)

## 🎯 Project Overview

Beiyangu is a reverse marketplace that flips the traditional e-commerce model. Instead of sellers listing products, buyers post requests with budgets, and sellers compete by submitting bids. The platform includes a simulated escrow system to ensure secure transactions.

### Key Features

- 🔄 **Reverse Marketplace**: Buyers post requests, sellers bid
- 🔐 **Cookie-based Authentication**: Secure authentication with CSRF protection
- 💰 **Simulated Escrow**: Funds locked until delivery completion
- 👥 **Dynamic User Roles**: Users can be both buyers and sellers
- 📊 **Comprehensive API**: RESTful endpoints for all operations
- 🛡️ **Security First**: Input validation, permissions, and error handling
- 🐳 **Docker Ready**: Containerized for easy deployment
- 🚀 **Cloud Deployed**: Live on Railway with PostgreSQL

## 📋 Table of Contents

- [Business Logic](#business-logic)
- [Tech Stack](#tech-stack)
- [Live Demo](#live-demo)
- [Project Structure](#project-structure)
- [Data Models](#data-models)
- [API Endpoints](#api-endpoints)
- [Docker Deployment](#docker-deployment)
- [Local Development](#local-development)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Production Deployment](#production-deployment)
- [Contributing](#contributing)

## 🎯 Business Logic

### Happy Path Flow

1. **User Registration/Login** → Session cookies and CSRF tokens issued
2. **Buyer Creates Request** → Budget set, request posted for bidding
3. **Sellers Browse Requests** → Submit competitive bids
4. **Buyer Creates Escrow** → Funds locked for accepted bid
5. **Seller Marks Delivered** → Request status changes to "delivered"
6. **Buyer Releases Funds** → Escrow released, transaction complete

### User Roles

- **Dynamic Role System**: Users can act as both buyers and sellers
- **Context-Based Permissions**: Role determined by action context
- **Secure Operations**: All actions require proper authentication and CSRF protection

## 🏛️ Tech Stack

### Backend Technologies

- **Framework**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL 13+
- **Authentication**: Session-based with CSRF protection
- **API Documentation**: Django REST Framework browsable API
- **Code Quality**: pycodestyle and pydocstyle compliant

### DevOps & Deployment

- **Containerization**: Docker & Docker Compose
- **Cloud Platform**: Railway
- **Database**: Railway PostgreSQL
- **Environment**: Python 3.8+
- **Package Management**: pip with requirements.txt

### Development Tools

- **Testing**: Django TestCase and cURL validation
- **Code Quality**: Black, pycodestyle, pydocstyle
- **Version Control**: Git with comprehensive documentation

## 🌐 Live Demo

The application is deployed and ready for testing:

### Live API Endpoints

```bash
# Base URL
https://beiyangu.up.railway.app/

# Authentication
https://beiyangu.up.railway.app/api/auth/register/
https://beiyangu.up.railway.app/api/auth/login/

# Requests
https://beiyangu.up.railway.app/api/requests/
https://beiyangu.up.railway.app/api/requests/my_requests/

# Bids
https://beiyangu.up.railway.app/api/requests/{id}/bids/
https://beiyangu.up.railway.app/api/bids/

# Escrow
https://beiyangu.up.railway.app/api/escrow/
https://beiyangu.up.railway.app/api/escrow/create_for_bid/

# Dashboards
https://beiyangu.up.railway.app/api/dashboard/buyer/
https://beiyangu.up.railway.app/api/dashboard/seller/
```

### Quick Test

```bash
# Test the live API
curl https://beiyangu.up.railway.app/api/requests/

# Register a new user
curl -X POST https://beiyangu.up.railway.app/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "password_confirm": "testpass123"
  }'
```

## 🛣️ API Endpoints

### Authentication Endpoints

#### User Registration

```bash
POST https://beiyangu.up.railway.app/api/auth/register/
Content-Type: application/json

{
  "username": "buyer1",
  "email": "buyer1@example.com",
  "password": "buyerpassword123",
  "password_confirm": "buyerpassword123",
  "bio": "Optional bio",
  "location": "Optional location"
}
```

#### User Login (Cookie-based)

```bash
# Login and save cookies
curl -X POST https://beiyangu.up.railway.app/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "buyer1@example.com",
    "password": "buyerpassword123"
  }' \
  -c cookies.txt
```

#### Token Refresh

```bash
POST https://beiyangu.up.railway.app/api/auth/refresh/
```

#### User Logout

```bash
POST https://beiyangu.up.railway.app/api/auth/logout/
```

#### Get Current User Info

```bash
GET https://beiyangu.up.railway.app/api/auth/me/
Cookie: sessionid=<session_id>
```

### Request Management

#### List All Open Requests

```bash
# Get all requests (paginated)
GET https://beiyangu.up.railway.app/api/requests/
GET https://beiyangu.up.railway.app/api/requests/?page=2&page_size=10
```

#### Get User's Own Requests

```bash
GET https://beiyangu.up.railway.app/api/requests/my_requests/
Cookie: sessionid=<session_id>
```

#### Create New Request

```bash
curl -X POST https://beiyangu.up.railway.app/api/requests/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $(grep csrftoken cookies.txt | cut -f7)" \
  -H "Referer: https://beiyangu.up.railway.app" \
  -d '{
    "title": "Need website homepage design",
    "description": "Landing page design for my startup",
    "budget": "200.00",
    "deadline": "2025-07-20",
    "category": "1"
  }' \
  -b cookies.txt
```

#### Get Request Details

```bash
GET https://beiyangu.up.railway.app/api/requests/{id}/
```

#### Update Request Status

```bash
curl -X POST https://beiyangu.up.railway.app/api/requests/{id}/change_status/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $(grep csrftoken cookies.txt | cut -f7)" \
  -H "Referer: https://beiyangu.up.railway.app" \
  -d '{
    "status": "delivered",
    "notes": "Work completed by seller"
  }'
```

#### Delete Request

```bash
DELETE https://beiyangu.up.railway.app/api/requests/{id}/
Cookie: sessionid=<session_id>
X-CSRFToken: <csrf_token>
```

### Bid Management

#### List User's Bids

```bash
GET https://beiyangu.up.railway.app/api/bids/
Cookie: sessionid=<session_id>
```

#### Submit Bid on Request

```bash
curl -X POST https://beiyangu.up.railway.app/api/requests/{request_id}/bids/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "Referer: https://beiyangu.up.railway.app" \
  -H "X-CSRFToken: $(grep csrftoken cookies.txt | cut -f7)" \
  -d '{
    "amount": "175.00",
    "message": "I have 5 years of experience in web development and can deliver this project within the specified timeframe.",
    "delivery_time": 10
  }'
```

#### Update Bid

```bash
PUT https://beiyangu.up.railway.app/api/bids/{id}/
Cookie: sessionid=<session_id>
X-CSRFToken: <csrf_token>
Content-Type: application/json

{
  "amount": "150.00",
  "message": "Updated bid with better offer"
}
```

#### Delete Bid

```bash
DELETE https://beiyangu.up.railway.app/api/bids/{id}/
Cookie: sessionid=<session_id>
X-CSRFToken: <csrf_token>
```

### Escrow Management

#### List Escrow Transactions

```bash
curl -X GET https://beiyangu.up.railway.app/api/escrow/ \
  -b cookies.txt \
  -H "X-CSRFToken: $(grep csrftoken cookies.txt | cut -f7)"
```

#### Create Escrow for Bid

```bash
curl -X POST https://beiyangu.up.railway.app/api/escrow/create_for_bid/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $(grep csrftoken cookies.txt | cut -f7)" \
  -H "Referer: https://beiyangu.up.railway.app" \
  -d '{
    "bid_id": 2,
    "payment_method": "credit_card",
    "payment_details": {
      "card_number": "****1234",
      "card_type": "visa"
    }
  }'
```

#### Get Escrow Transaction Details

```bash
GET https://beiyangu.up.railway.app/api/escrow/{public_id}/
Cookie: sessionid=<session_id>
```

#### Perform Escrow Action (Release/Hold)

```bash
curl -X POST https://beiyangu.up.railway.app/api/escrow/{public_id}/perform_action/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $(grep csrftoken cookies.txt | cut -f7)" \
  -H "Referer: https://beiyangu.up.railway.app" \
  -d '{
    "action": "release",
    "notes": "Work completed satisfactorily"
  }'
```

#### Get Escrow Status

```bash
GET https://beiyangu.up.railway.app/api/escrow/{public_id}/status/
Cookie: sessionid=<session_id>
```

### Dashboard Endpoints

#### Buyer Dashboard

```bash
GET https://beiyangu.up.railway.app/api/dashboard/buyer/
Cookie: sessionid=<session_id>
```

#### Seller Dashboard

```bash
GET https://beiyangu.up.railway.app/api/dashboard/seller/
Cookie: sessionid=<session_id>
```

## 📁 Project Structure

```
beiyangu-backend/
├── beiyangu/                 # Main project settings
│   ├── settings.py          # Django configuration
│   ├── urls.py              # Root URL configuration
│   └── wsgi.py              # WSGI application
├── apps/                     # Application modules
│   ├── users/               # User authentication & profiles
│   │   ├── models.py        # User model extensions
│   │   ├── views.py         # Auth endpoints
│   │   └── serializers.py   # User serialization
│   ├── user_requests/       # Buyer request management
│   │   ├── models.py        # Request model
│   │   ├── views.py         # Request CRUD endpoints
│   │   └── serializers.py   # Request serialization
│   ├── bids/                # Seller bid management
│   │   ├── models.py        # Bid model
│   │   ├── views.py         # Bid endpoints
│   │   └── serializers.py   # Bid serialization
│   ├── escrow/              # Escrow transaction management
│   │   ├── models.py        # EscrowTransaction model
│   │   ├── views.py         # Escrow endpoints
│   │   └── serializers.py   # Escrow serialization
│   └── dashboard/           # Dashboard views
│       ├── views.py         # Buyer/Seller dashboards
│       └── serializers.py   # Dashboard serialization
├── core/                    # Shared utilities
│   ├── permissions.py       # Custom permission classes
│   ├── pagination.py        # Custom pagination
│   └── utils.py             # Helper functions
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile              # Docker container configuration
├── requirements.txt         # Python dependencies
├── manage.py               # Django management script
└── README.md               # This file
```

## 💡 Usage Examples

### Complete Transaction Flow (Live API)

```bash
# 1. Register a buyer
curl -X POST https://beiyangu.up.railway.app/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "buyer1",
    "email": "buyer1@example.com",
    "password": "buyerpassword123",
    "password_confirm": "buyerpassword123"
  }'

# 2. Login and save cookies
curl -X POST https://beiyangu.up.railway.app/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "buyer1@example.com",
    "password": "buyerpassword123"
  }' \
  -c cookies.txt

# 3. Create a request
curl -X POST https://beiyangu.up.railway.app/api/requests/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $(grep csrftoken cookies.txt | cut -f7)" \
  -H "Referer: https://beiyangu.up.railway.app" \
  -d '{
    "title": "Need website homepage design",
    "description": "Landing page design for my startup",
    "budget": "200.00",
    "deadline": "2025-07-20",
    "category": "1"
  }' \
  -b cookies.txt

# 4. Register a seller
curl -X POST https://beiyangu.up.railway.app/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "seller1",
    "email": "seller1@example.com",
    "password": "sellerpassword123",
    "password_confirm": "sellerpassword123"
  }'

# 5. Seller login and save cookies
curl -X POST https://beiyangu.up.railway.app/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "seller1@example.com",
    "password": "sellerpassword123"
  }' \
  -c seller_cookies.txt

# 6. Seller bids on request
curl -X POST https://beiyangu.up.railway.app/api/requests/1/bids/ \
  -b seller_cookies.txt \
  -H "Content-Type: application/json" \
  -H "Referer: https://beiyangu.up.railway.app" \
  -H "X-CSRFToken: $(grep csrftoken seller_cookies.txt | cut -f7)" \
  -d '{
    "amount": "175.00",
    "message": "I have 5 years of experience in web development and can deliver this project within the specified timeframe.",
    "delivery_time": 10
  }'

# 7. Buyer creates escrow for accepted bid
curl -X POST https://beiyangu.up.railway.app/api/escrow/create_for_bid/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $(grep csrftoken cookies.txt | cut -f7)" \
  -H "Referer: https://beiyangu.up.railway.app" \
  -d '{
    "bid_id": 2,
    "payment_method": "credit_card",
    "payment_details": {
      "card_number": "****1234",
      "card_type": "visa"
    }
  }'

# 8. Seller marks work as delivered
curl -X POST https://beiyangu.up.railway.app/api/requests/1/change_status/ \
  -b seller_cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $(grep csrftoken seller_cookies.txt | cut -f7)" \
  -H "Referer: https://beiyangu.up.railway.app" \
  -d '{
    "status": "delivered",
    "notes": "Work completed by seller"
  }'

# 9. Get escrow transaction ID
curl -X GET https://beiyangu.up.railway.app/api/escrow/ \
  -b cookies.txt \
  -H "X-CSRFToken: $(grep csrftoken cookies.txt | cut -f7)"

# 10. Buyer releases funds
curl -X POST https://beiyangu.up.railway.app/api/escrow/{escrow_public_id}/perform_action/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $(grep csrftoken cookies.txt | cut -f7)" \
  -H "Referer: https://beiyangu.up.railway.app" \
  -d '{
    "action": "release",
    "notes": "Work completed satisfactorily"
  }'
```

### Dashboard Examples

```bash
# Get buyer dashboard
curl -X GET https://beiyangu.up.railway.app/api/dashboard/buyer/ \
  -b cookies.txt

# Get seller dashboard
curl -X GET https://beiyangu.up.railway.app/api/dashboard/seller/ \
  -b cookies.txt

# Get user's requests
curl -X GET https://beiyangu.up.railway.app/api/requests/my_requests/ \
  -b cookies.txt

# Get user's bids
curl -X GET https://beiyangu.up.railway.app/api/bids/ \
  -b cookies.txt
```

## 🔑 Authentication Notes

### Cookie-based Authentication

The API uses Django's session-based authentication with CSRF protection:

1. **Login**: Returns session cookies and CSRF token
2. **Subsequent Requests**: Include cookies and CSRF token in headers
3. **CSRF Protection**: All POST/PUT/DELETE requests require CSRF token

### Required Headers for Protected Endpoints

```bash
# Required for all authenticated requests
Cookie: sessionid=<session_id>; csrftoken=<csrf_token>

# Required for POST/PUT/DELETE requests
X-CSRFToken: <csrf_token>
Referer: https://beiyangu.up.railway.app
```

### Cookie Management

```bash
# Save cookies during login
curl -c cookies.txt ...

# Use cookies in subsequent requests
curl -b cookies.txt ...

# Extract CSRF token from cookies
grep csrftoken cookies.txt | cut -f7
```

## 📊 Data Models

### User Model (Extended)

```python
class User(AbstractUser):
    """Extended user model with marketplace-specific fields."""
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Request Model

```python
class Request(models.Model):
    """Buyer request model with escrow integration."""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('accepted', 'Accepted'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('disputed', 'Disputed'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    deadline = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Bid Model

```python
class Bid(models.Model):
    """Seller bid model with unique constraints."""
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='bids')
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField()
    delivery_time = models.IntegerField()  # days
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['request', 'seller']  # One bid per seller per request
```

### EscrowTransaction Model

```python
class EscrowTransaction(models.Model):
    """Simulated escrow system for secure transactions."""
    STATUS_CHOICES = [
        ('locked', 'Locked'),
        ('released', 'Released'),
        ('held', 'Held for Dispute'),
    ]
    public_id = models.UUIDField(default=uuid.uuid4, unique=True)
    request = models.OneToOneField(Request, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    payment_details = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='locked')
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
```

## 🧪 Testing

### Running Tests

```bash
# Local testing
python manage.py test

# Docker testing
docker-compose exec web python manage.py test

# Run tests for specific app
python manage.py test apps.users
python manage.py test apps.user_requests
python manage.py test apps.bids
python manage.py test apps.escrow

# Run tests with coverage
pip install coverage
coverage run manage.py test
coverage report
coverage html  # Generate HTML coverage report
```

### Live API Testing

Test the live API endpoints:

```bash
# Test live API health
curl https://beiyangu.up.railway.app/api/requests/

# Test authentication
curl -X POST https://beiyangu.up.railway.app/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser_' $(date +%s) '",
    "email": "test' $(date +%s) '@example.com",
    "password": "testpass123",
    "password_confirm": "testpass123"
  }'
```

## 🐳 Docker Deployment

The application is fully containerized using Docker for easy deployment and development.

### Docker Configuration

**Dockerfile**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

**docker-compose.yml**

```yaml
version: "3.8"

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://user:password@db:5432/beiyangu
    depends_on:
      - db
    volumes:
      - .:/app

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=beiyangu
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Running with Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop the containers
docker-compose down

# View logs
docker-compose logs -f

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## 🚀 Local Development

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 13 or higher (or Docker)
- pip (Python package manager)

### Setup Options

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/M0imaritim/Beiyangu_backend.git
cd Beiyangu_backend

# Run with Docker
docker-compose up --build

# The API will be available at http://localhost:8000
```

#### Option 2: Local Development

```bash
# Clone the repository
git clone https://github.com/M0imaritim/Beiyangu_backend.git
cd Beiyangu_backend

# Create and activate virtual environment
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Set up PostgreSQL database
createdb beiyangu_dev

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Configuration
SECRET_KEY=your-super-secret-django-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,beiyangu.up.railway.app

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/beiyangu_dev
DB_NAME=beiyangu_dev
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Security Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://beiyangu.up.railway.app
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://beiyangu.up.railway.app

# Email Configuration (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Railway Configuration (Production)
RAILWAY_STATIC_URL=https://beiyangu.up.railway.app/static/
RAILWAY_ENVIRONMENT=production
```

## 🚀 Production Deployment

### Railway Deployment (Current)

The application is deployed on Railway with the following configuration:

**Live URL**: [https://beiyangu.up.railway.app/](https://beiyangu.up.railway.app/)

#### Railway Setup

1. **Connect Repository**

   ```bash
   # Railway CLI
   railway login
   railway link
   railway up
   ```

2. **Environment Variables**
   Set production environment variables in Railway dashboard:

   - `SECRET_KEY`
   - `DATABASE_URL` (provided by Railway PostgreSQL)
   - `ALLOWED_HOSTS=beiyangu.up.railway.app`
   - `DEBUG=False`
   - `RAILWAY_ENVIRONMENT=production`

3. **Database Setup**
   ```bash
   # Railway automatically provisions PostgreSQL
   # Run migrations
   railway run python manage.py migrate
   railway run python manage.py createsuperuser
   ```

### Alternative Deployment Options

#### Docker Deployment

```bash
# Build for production
docker build -t beiyangu-backend .

# Run with production settings
docker run -e DEBUG=False -e DATABASE_URL=your_db_url -p 8000:8000 beiyangu-backend
```

#### Manual Deployment

For other platforms:

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**

   ```bash
   export SECRET_KEY="your-secret-key"
   export DATABASE_URL="postgresql://..."
   export DEBUG=False
   export ALLOWED_HOSTS="your-domain.com"
   ```

3. **Run migrations**

   ```bash
   python manage.py collectstatic --noinput
   python manage.py migrate
   ```

4. **Start server**
   ```bash
   gunicorn beiyangu.wsgi:application --bind 0.0.0.0:8000
   ```

## 📝 API Response

### Success Response

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Need a logo design",
    "description": "Looking for a modern logo",
    "budget": "500.00",
    "status": "open",
    "bids_count": 3
  },
  "message": "Request created successfully"
}
```

### Error Response

```json
{
  "success": false,
  "error": "Authentication required",
  "details": {
    "code": "authentication_required",
    "field": "authorization"
  }
}
```

## 🔧 Development Guidelines

### Code Quality Standards

- **PEP 8**: All code follows Python style guidelines
- **pycodestyle**: Automated style checking
- **pydocstyle**: Docstring conventions
- **Type Hints**: Use type hints where appropriate
- **Documentation**: Comprehensive docstrings for all functions

### API Design Principles

- **RESTful**: Follow REST conventions
- **Consistent**: Uniform response formats
- **Secure**: Proper authentication and authorization
- **Validated**: Input validation on all endpoints
- **Paginated**: Large datasets are paginated

### Database Best Practices

- **Migrations**: All schema changes through migrations
- **Indexing**: Proper database indexing for performance
- **Constraints**: Database-level constraints for data integrity
- **Relationships**: Proper foreign key relationships

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Run tests and style checks**
   ```bash
   python manage.py test
   pycodestyle .
   pydocstyle .
   ```
5. **Commit your changes**
   ```bash
   git commit -m "Add your feature description"
   ```
6. **Push to the branch**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**

### Development Setup for Contributors

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Run linting
flake8 .
black .
isort .
```

## 📊 Project Status

- ✅ **Authentication System**: Complete with JWT tokens
- ✅ **Request Management**: Full CRUD operations
- ✅ **Bidding System**: Bid submission and acceptance
- ✅ **Escrow System**: Simulated fund management
- ✅ **User Dashboards**: Buyer and seller views
- ✅ **API Documentation**: Comprehensive endpoint documentation
- ✅ **Testing**: cURL-validated endpoints
- ✅ **Deployment**: Railway-ready configuration

## 🔮 Future Enhancements

- **Email Notifications**: Automated email alerts
- **Advanced Search**: Filtering and search capabilities
- **Dispute Resolution**: Formal dispute handling system
- **Payment Integration**: Real payment gateway integration
- **Mobile API**: Mobile-optimized endpoints
- **Analytics**: Usage analytics and reporting
- **File Uploads**: Support for images and documents

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, please:

1. Check the [Issues](https://github.com/M0imaritim/Beiyangu_backend/issues) page
2. Create a new issue with detailed description
3. Include relevant error messages and logs
4. Specify your environment (Python version, OS, etc.)

## 🙏 Acknowledgments

- Django and Django REST Framework communities
- PostgreSQL for robust database support
- Railway for deployment platform
- All contributors and testers

---

**Built with ❤️ by M0imaritim**

_Beiyangu - Transforming how people buy and sell services_
