# Astris

**Astris** is a Django-based e-commerce platform focused on backend architecture,
clear domain separation, and production-oriented design decisions.

The project is built as a long-term system with a planned transition to
**Django REST Framework + React**, while currently operating as a server-rendered Django application.


## Tech Stack

**Backend**
- Python / **Django 5.2**
- Email-based authentication

**Frontend**
- Django Templates + Bootstrap

**Data & Infrastructure**
- **PostgreSQL** — primary database
- **Redis** — cache, Celery broker, session storage
- **Celery + Celery Beat** — async tasks & scheduled jobs

**External Services**
- Payments: **Mollie API** (TWINT, Switzerland)
- Emails: **Resend API**

**Deployment**
- Docker + docker-compose (local development)
- Production stack (Nginx / Gunicorn) not yet implemented


## Core Functionality

### Product Catalog
- Role-aware UI:
  - buyers: browse & add to cart
  - backoffice users: manage products
- Stock handling via service-layer logic

### Cart & Orders

Two parallel cart flows:

**Authenticated users**
- Cart is a `pending` Order stored in PostgreSQL
- OrderItems store **denormalized product snapshots**
  to avoid side effects from later product changes

**Anonymous users**
- Cart stored in Redis-backed sessions
- Same snapshot strategy is used
- TTL cleanup handled explicitly

### Payments
- Checkout supports multiple payment methods
- Currently implemented: TWINT via Mollie
- Payment system is based on an **abstract Gateway interface**
- Provider logic (webhooks, status sync) is fully isolated
- Designed for easy extension

### Email Notifications
- Event-driven email delivery via Resend API
- All emails are sent asynchronously through Celery
- Covers:
  - registration & email change
  - password reset
  - order status updates

### Order Lifecycle & Backoffice
- Orders automatically expire if left `pending`
- Backoffice features:
  - order status management (`paid → shipped`)
  - optional tracking number
  - guarded user notifications
- Buyers can confirm delivery (`shipped → delivered`) once

### Cleanup Jobs
- `pending` orders removed after 24h of inactivity
- Anonymous carts expire earlier than Redis TTL


## Architecture
- Domain-based apps:
  - `core`, `account`, `payments`, `shared`
- Service layer for all business logic
- Lean models, no fat-model pattern
- Denormalized cart-item snapshots
- Environment-based settings loading
- Decisions aim for a trade-off between SOLID design and development pragmatism


## Middleware & Signals
- Registration attempt restriction middleware
- Silk-integrated request profiling
- Signals for:
  - role-based profile creation/removal
  - login audit logging (basis for traffic analytics)


## Status & Roadmap

**Current**
- Backend, payments, async tasks fully functional
- Django template-based frontend

**Planned**
- Django REST Framework
- React frontend
- JWT-based authentication
- Production deployment stack
- Extended analytics
- Final test coverage


## Notes

This repository is not intended as a plug-and-play solution.
It exists to demonstrate architectural decisions, trade-offs,
and system design thinking.


© Astris
