# 🏗️ Beiyangu Backend

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org/)
[![Django](https://img.shields.io/badge/django-4.2%2B-green.svg)](https://djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-13%2B-blue.svg)](https://postgresql.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **Beiyangu** (Swahili: "My Price") - A robust backend API for a reverse marketplace where buyers post requests, sellers bid, and funds are held in simulated escrow until delivery completion.

## 🎯 Project Overview

Beiyangu is a reverse marketplace that flips the traditional e-commerce model. Instead of sellers listing products, buyers post requests with budgets, and sellers compete by submitting bids. The platform includes a simulated escrow system to ensure secure transactions.

### Key Features

- 🔄 **Reverse Marketplace**: Buyers post requests, sellers bid
- 🔐 **JWT Authentication**: Secure authentication with httpOnly cookies
- 💰 **Simulated Escrow**: Funds locked until delivery completion
- 👥 **Dynamic User Roles**: Users can be both buyers and sellers
- 📊 **Comprehensive API**: RESTful endpoints for all operations
- 🛡️ **Security First**: Input validation, permissions, and error handling

## 📋 Table of Contents

- [Business Logic](#business-logic)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Data Models](#data-models)
- [API Endpoints](#api-endpoints)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

## 🎯 Business Logic

### Happy Path Flow

1. **User Registration/Login** → JWT token issued
2. **Buyer Creates Request** → Budget set, escrow locks funds (simulated)
3. **Sellers Browse Requests** → Submit competitive bids
4. **Buyer Accepts Bid** → Request status changes to "accepted"
5. **Seller Marks Delivered** → Buyer reviews delivery
6. **Buyer Releases Funds** → Escrow updated, transaction complete

### User Roles

- **Dynamic Role System**: Users can act as both buyers and sellers
- **Context-Based Permissions**: Role determined by action context
- **Secure Operations**: All actions require proper authentication

## 🏛️ Tech Stack

### Backend Technologies

- **Framework**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL 13+
- **Authentication**: JWT (djangorestframework-simplejwt)
- **API Documentation**: Django REST Framework browsable API
- **Code Quality**: pycodestyle and pydocstyle compliant

### Development Tools

- **Environment**: Python 3.8+
- **Package Management**: pip with requirements.txt
- **Testing**: Django TestCase and cURL validation
- **Deployment**: Railway (configured)

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
│   ├── requests/            # Buyer request management
│   │   ├── models.py        # Request model
│   │   ├── views.py         # Request CRUD endpoints
│   │   └── serializers.py   # Request serialization
│   ├── bids/                # Seller bid management
│   │   ├── models.py        # Bid model
│   │   ├── views.py         # Bid endpoints
│   │   └── serializers.py   # Bid serialization
│   └── escrow/              # Escrow transaction management
│       ├── models.py        # EscrowTransaction model
│       ├── views.py         # Escrow endpoints
│       └── serializers.py   # Escrow serialization
├── core/                    # Shared utilities
│   ├── permissions.py       # Custom permission classes
│   ├── pagination.py        # Custom pagination
│   └── utils.py             # Helper functions
├── requirements.txt         # Python dependencies
├── manage.py               # Django management script
└── README.md               # This file
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
    request = models.OneToOneField(Request, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='locked')
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
```

## 🛣️ API Endpoints

### Authentication Endpoints

```bash
# User registration
POST /api/auth/register/
Content-Type: application/json
{
  "username": "user123",
  "email": "user@example.com",
  "password": "securepassword123",
  "bio": "Optional bio",
  "location": "Optional location"
}

# User login (returns JWT in httpOnly cookie)
POST /api/auth/login/
Content-Type: application/json
{
  "username": "user123",
  "password": "securepassword123"
}

# Token refresh
POST /api/auth/refresh/

# User logout (clear cookies)
POST /api/auth/logout/

# Get current user info
GET /api/auth/me/
Authorization: Bearer <token>
```

### Request Management

```bash
# List all open requests (paginated)
GET /api/requests/
GET /api/requests/?page=2&page_size=10

# Create new request (buyer only)
POST /api/requests/
Authorization: Bearer <token>
Content-Type: application/json
{
  "title": "Need a logo design",
  "description": "Looking for a modern logo for my startup",
  "budget": "500.00"
}

# Get request details with bids
GET /api/requests/{id}/

# Update request (owner only)
PUT /api/requests/{id}/
Authorization: Bearer <token>

# Delete request (owner only, if no bids)
DELETE /api/requests/{id}/
Authorization: Bearer <token>

# Mark as delivered (accepted seller only)
POST /api/requests/{id}/deliver/
Authorization: Bearer <token>

# Release funds (buyer only)
POST /api/requests/{id}/release/
Authorization: Bearer <token>
```

### Bid Management

```bash
# List user's bids
GET /api/bids/
Authorization: Bearer <token>

# Submit bid on request
POST /api/requests/{id}/bids/
Authorization: Bearer <token>
Content-Type: application/json
{
  "amount": "450.00",
  "message": "I can deliver this within 3 days"
}

# Update bid (owner only, if not accepted)
PUT /api/bids/{id}/
Authorization: Bearer <token>

# Delete bid (owner only, if not accepted)
DELETE /api/bids/{id}/
Authorization: Bearer <token>

# Accept bid (request owner only)
POST /api/bids/{id}/accept/
Authorization: Bearer <token>
```

### Dashboard Endpoints

```bash
# Buyer dashboard (my requests + received bids)
GET /api/dashboard/buyer/
Authorization: Bearer <token>

# Seller dashboard (available requests + my bids)
GET /api/dashboard/seller/
Authorization: Bearer <token>
```

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 13 or higher
- pip (Python package manager)

### Local Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/M0imaritim/Beiyangu_backend.git
   cd Beiyangu_backend
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up PostgreSQL database**

   ```bash
   # Create database
   createdb beiyangu_dev

   # Run migrations
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser (optional)**

   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**
   ```bash
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
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/beiyangu_dev
DB_NAME=beiyangu_dev
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_LIFETIME=60  # minutes
JWT_REFRESH_TOKEN_LIFETIME=1440  # minutes (24 hours)

# Security Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Email Configuration (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Database Configuration

For PostgreSQL (recommended):

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}
```

## 💡 Usage Examples

### Complete Transaction Flow (cURL)

```bash
# 1. Register a buyer
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "buyer1",
    "email": "buyer@example.com",
    "password": "securepass123",
    "bio": "Looking for quality services"
  }'

# 2. Login and get token
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "buyer1",
    "password": "securepass123"
  }'

# 3. Create a request (use token from login)
curl -X POST http://127.0.0.1:8000/api/requests/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Need a website built",
    "description": "Looking for a responsive website for my business",
    "budget": "1500.00"
  }'

# 4. Register a seller
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "seller1",
    "email": "seller@example.com",
    "password": "securepass123",
    "bio": "Professional web developer"
  }'

# 5. Seller bids on request
curl -X POST http://127.0.0.1:8000/api/requests/1/bids/ \
  -H "Authorization: Bearer SELLER_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "1200.00",
    "message": "I can build a modern, responsive website within 2 weeks"
  }'

# 6. Buyer accepts bid
curl -X POST http://127.0.0.1:8000/api/bids/1/accept/ \
  -H "Authorization: Bearer BUYER_TOKEN_HERE"

# 7. Seller marks as delivered
curl -X POST http://127.0.0.1:8000/api/requests/1/deliver/ \
  -H "Authorization: Bearer SELLER_TOKEN_HERE"

# 8. Buyer releases funds
curl -X POST http://127.0.0.1:8000/api/requests/1/release/ \
  -H "Authorization: Bearer BUYER_TOKEN_HERE"
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test apps.users
python manage.py test apps.requests
python manage.py test apps.bids
python manage.py test apps.escrow

# Run tests with coverage
pip install coverage
coverage run manage.py test
coverage report
coverage html  # Generate HTML coverage report
```

### API Testing with cURL

The project includes comprehensive cURL testing examples. All endpoints have been validated using cURL commands to ensure proper functionality.

### Test Data Creation

```bash
# Create test users and data
python manage.py shell
>>> from django.contrib.auth.models import User
>>> from apps.requests.models import Request
>>> from apps.bids.models import Bid
>>> # Create test data programmatically
```

## 🚀 Deployment

### Railway Deployment

The project is configured for Railway deployment:

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
   - `DATABASE_URL`
   - `ALLOWED_HOSTS`
   - `DEBUG=False`

3. **Database Migration**
   ```bash
   railway run python manage.py migrate
   railway run python manage.py createsuperuser
   ```

### Manual Deployment

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

## 📝 API Response Format

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
