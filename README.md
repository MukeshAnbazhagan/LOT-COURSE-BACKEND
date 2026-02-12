# LOT Platform - Backend API

FastAPI-based backend for the Learning Online Together platform with RuPay/Razorpay integration.

## Features

- ✅ RESTful API with FastAPI
- ✅ JWT authentication with role-based access
- ✅ SQLAlchemy ORM with SQLite/PostgreSQL
- ✅ RuPay (Razorpay) payment gateway integration
- ✅ WhatsApp notifications (Twilio)
- ✅ Email notifications
- ✅ Course management system
- ✅ Event calendar management
- ✅ User dashboard with analytics
- ✅ CORS enabled for frontend
- ✅ Comprehensive error handling

## Project Structure

```
backend/
├── app/
│   ├── routes/
│   │   ├── auth.py
│   │   ├── courses.py
│   │   ├── events.py
│   │   ├── payments.py
│   │   └── dashboard.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── courses.py
│   │   └── payments.py
│   ├── database.py
│   ├── security.py
│   └── main.py
├── .env.example
├── requirements.txt
├── Dockerfile
└── run.sh
```

## Prerequisites

- Python 3.9+
- pip
- Virtual environment (recommended)

## Installation

1. **Clone and navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```ini
   # Database
   DATABASE_URL=sqlite:///./lot.db
   
   # JWT
   SECRET_KEY=your-super-secret-key-change-this
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # RuPay (Razorpay)
   RAZORPAY_KEY_ID=your_key_id
   RAZORPAY_KEY_SECRET=your_key_secret
   
   # WhatsApp (Twilio)
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890
   
   # CORS
   CORS_ORIGINS=http://localhost:3000
   ```

5. **Run migrations (if using Alembic)**
   ```bash
   alembic upgrade head
   ```

6. **Start development server**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

   API will be available at `http://localhost:8000`
   Documentation at `http://localhost:8000/docs`

## API Endpoints

### Authentication
```
POST   /api/auth/signup              - Register new user
POST   /api/auth/login               - Login user
POST   /api/auth/logout              - Logout user
GET    /api/auth/profile             - Get user profile
PUT    /api/auth/profile             - Update profile
```

### Courses
```
GET    /api/courses                  - Get all courses (with filters)
GET    /api/courses/{id}             - Get course details
POST   /api/courses/{id}/enroll      - Enroll in course
GET    /api/courses/{id}/progress    - Get course progress
POST   /api/courses/{id}/reviews     - Add course review
```

### Events
```
GET    /api/events                   - Get all events (with filters)
GET    /api/events/{id}              - Get event details
POST   /api/events/{id}/rsvp         - RSVP for event
GET    /api/events/my-schedule       - Get user's event schedule
```

### Payments
```
POST   /api/payments/create          - Initialize payment
POST   /api/payments/verify          - Verify payment
GET    /api/payments/transactions    - Get user transactions
```

### Dashboard
```
GET    /api/dashboard/overview       - Get overview stats
GET    /api/dashboard/my-courses     - Get enrolled courses
GET    /api/dashboard/progress       - Get detailed progress
GET    /api/dashboard/certificates   - Get certificates
```

## Database Models

### User
```python
- id: Integer
- name: String
- email: String (unique)
- phone: String (unique)
- password_hash: String
- role: Enum (admin, instructor, student)
- profile_image: String (nullable)
- bio: Text (nullable)
- created_at: DateTime
- updated_at: DateTime
```

### Course
```python
- id: Integer
- title: String
- description: Text
- category: String
- level: String (Beginner, Intermediate, Advanced)
- price: Float
- duration: Integer (weeks)
- instructor_id: Integer (FK)
- image: String (nullable)
- rating: Float
- reviews_count: Integer
- students_count: Integer
- created_at: DateTime
```

### Event
```python
- id: Integer
- title: String
- description: Text
- event_type: Enum (workshop, live_event, online_quiz)
- instructor_id: Integer (FK)
- date: DateTime
- time: String
- duration: Integer (minutes)
- location: String (nullable)
- image: String (nullable)
- capacity: Integer
- registered: Integer
- event_url: String (nullable)
- created_at: DateTime
```

### Payment
```python
- id: Integer
- user_id: Integer (FK)
- course_id: Integer (FK, nullable)
- event_id: Integer (FK, nullable)
- amount: Float
- payment_method: String (rupay, stripe, etc.)
- transaction_id: String (unique)
- status: Enum (pending, completed, failed, refunded)
- payment_gateway_response: Text (nullable)
- created_at: DateTime
```

## Payment Integration

### RuPay/Razorpay Setup

1. **Create Razorpay account** at https://razorpay.com
2. **Get API credentials**
   - Key ID from Dashboard
   - Key Secret from Settings
3. **Add to .env**
   ```
   RAZORPAY_KEY_ID=rzp_live_xxxxx
   RAZORPAY_KEY_SECRET=xxxxx
   ```

### Payment Flow

1. **Client initiates payment**: POST `/api/payments/create`
2. **Backend creates Razorpay order**
3. **Client shows Razorpay payment form**
4. **Client verifies payment**: POST `/api/payments/verify`
5. **Backend confirms and creates enrollment/registration**

## WhatsApp Integration

### Twilio Setup

1. **Create Twilio account** at https://www.twilio.com
2. **Enable WhatsApp Sandbox**
3. **Get credentials**
   - Account SID
   - Auth Token
   - WhatsApp Number
4. **Add to .env**
   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxx
   TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890
   ```

### Webhook for notifications
After enrollment/event registration, WhatsApp message is sent with:
- Confirmation message
- Access link/details
- Support contact

## Security

### Implemented
- Password hashing with bcrypt
- JWT authentication
- CORS protection
- SQL injection prevention (SQLAlchemy)
- Rate limiting ready
- HTTPS in production

### Best Practices
- Never commit .env file
- Use strong SECRET_KEY
- Enable HTTPS in production
- Regular security updates
- Input validation on all endpoints

## Database

### SQLite (Development)
- Automatic file creation: `lot.db`
- No setup required
- Suitable for testing

### PostgreSQL (Production)
```ini
DATABASE_URL=postgresql://user:password@localhost:5432/lot_db
```

## Running the Server

### Development
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

## Docker

### Build
```bash
docker build -t lot-backend .
```

### Run
```bash
docker run -p 8000:8000 --env-file .env lot-backend
```

### Docker Compose
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - db
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: lot_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
```

## Testing

### Run tests
```bash
pytest
```

### With coverage
```bash
pytest --cov=app
```

## Deployment

### Heroku
```bash
heroku create lot-api
git push heroku main
heroku config:set -r .env
```

### AWS (EC2 + RDS)
1. Launch EC2 instance (Python 3.9+)
2. Install dependencies
3. Set environment variables
4. Run with gunicorn/supervisor
5. Set up RDS PostgreSQL database

### DigitalOcean
1. Create droplet (Ubuntu)
2. Install Python and dependencies
3. Configure app
4. Set up with systemd
5. Configure Nginx reverse proxy

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### API Documentation
Visit `http://localhost:8000/docs` for interactive Swagger UI

## Common Issues

### Import errors
```bash
pip install -r requirements.txt
```

### Database locked
```bash
rm lot.db  # Reset SQLite
```

### Port already in use
```bash
python -m uvicorn app.main:app --port 8001
```

### CORS errors
- Check `CORS_ORIGINS` in `.env`
- Ensure frontend URL is added

## Troubleshooting

### Payment verification fails
- Check Razorpay credentials
- Verify signature algorithm
- Check test vs live keys

### WhatsApp not sending
- Verify Twilio credentials
- Check WhatsApp number format
- Check sandbox status

### Database connection errors
- Verify DATABASE_URL
- For PostgreSQL, check credentials
- Ensure database exists

## API Response Format

### Success
```json
{
  "data": { ... },
  "message": "Success message",
  "status": "success"
}
```

### Error
```json
{
  "detail": "Error message",
  "error": "Additional details"
}
```

## Rate Limiting

Configure in production:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
```

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, contact: support@lotplatform.com
