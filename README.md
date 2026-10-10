# Airport API Service
REST API service for flight tracking and ticket booking management built with Django REST Framework.

---

## Features

- **JWT Authentication**: Secure user registration, authentication, and token management (`/api/user/register/`, `/api/user/token/`).
- **Role-Based Access Control**: Custom permissions (`IsAdminOrReadOnly`) separating standard passengers from staff members.
- **Flight & Route Management**: Filter flights by source/destination airports and departure/arrival dates.
- **Advanced Ticket Validation**: Multi-layer validation preventing seat overbooking (checking rows, seats per row) and duplicate seat reservations.
- **Order Booking System**: Atomic transaction handling for managing user ticket purchases.
- **Interactive Documentation**: Integrated Swagger UI and ReDoc OpenAPI documentation powered by `drf-spectacular` and located at `/api/doc/swagger/` and `/api/doc/redoc/`.
- **Database Optimization**: Optimized ORM queries using `select_related` and `prefetch_related` to eliminate N+1 query problems.
- **Complete Test Coverage**: Isolated test suite using custom factories and mock client execution.
- **Containerization**: Fully Dockerized environment with automatic database health-checks (`wait_for_db`).

---

## DB Structure

The database schema manages relationship dependencies between routes, flights, crews, airplanes, orders, and tickets.


```
Airport ──< Route ──< Flight >── Airplane >── AirplaneType
                        │
                        ├──────< Ticket >── Order >── User
                        │
                        └──< Crew (Many-to-Many)
```

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed on your machine.
- Alternatively: Python 3.11+ and PostgreSQL installed locally.

---

### Run with Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/LassisterV16/py-airport-api.git
   cd py-airport-api
   ```

2. **Create environment configuration:**
   ```bash
   cp .env.sample .env
   ```

3. **Build and launch the containers:**
   ```bash
   docker-compose build
   docker-compose up
   ```

The service will automatically run migrations and start at `http://127.0.0.1:8000/`.

---

### Run Locally (Without Docker)

1. **Create and activate a virtual environment, install dependencies:**
   ```bash
   python -m venv venv
   venv\Scripts\activate (on Windows)
   source venv/bin/activate (on macOS)
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
Set up your PostgreSQL database and update `.env` with your DB credentials.

3. **Apply migrations and run dev server:**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

---

## Getting Access & Usage Flow

1. **Register a new account:**
   * `POST /api/user/register/` with `username`, `email`, and `password`.

2. **Obtain JWT Token:**
   * `POST /api/user/token/` to receive your `access` and `refresh` tokens.

3. **Authorize Requests:**
   * Include the token in the request header:
   ```
   authorization: Bearer <your_access_token>
   ```

---

## API Documentation

Interactive API documentation is accessible once the server is running:

* **Swagger UI**: `http://127.0.0.1:8000/api/doc/swagger/`
* **ReDoc**: `http://127.0.0.1:8000/api/doc/redoc/`

---

## Running Tests

To run the full test suite inside the Docker container:

   ```bash
   docker-compose exec airport python manage.py test
   ```
