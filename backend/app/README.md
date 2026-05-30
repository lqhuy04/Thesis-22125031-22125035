# Thesis Authentication API

Backend API for authentication with password reset functionality.

## Features
- User signup with validation
- User login with JWT
- Password reset via email
- Protected routes with middleware
- Organized project structure

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run the server:
```bash
python -m app.main
```

## API Endpoints

### Public Routes
- `POST /api/auth/signup` - Register new user (creates unverified account and sends verification email)
- `GET /api/auth/verify-email?token=...` - Verify email by token
- `POST /api/auth/login` - Login user (only verified accounts)
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password with old_password and new_password (requires Authorization header)

### Protected Routes (Require Authorization header)
- `GET /api/auth/me` - Get current user info

### Agentic Analysis
- `POST /api/agentic/analyze` - Run the full analysis pipeline and return the structured recommendation.
- `POST /api/agentic/chat` - Chat mode with session memory.
- `POST /api/agentic/backtest` - Run the historical technical backtest used for thesis evaluation.

For the backtest methodology and assumptions, see [BACKTEST.md](../BACKTEST.md).

## Testing Protected Routes

```bash
# Add header to your requests:
Authorization: Bearer <your-jwt-token>
```