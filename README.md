# Diploma Project: Service-Oriented ERP Platform Prototype
#TODO: update readme

## Abstract

This repository contains a diploma-scale prototype of a service-oriented enterprise platform.  
The system is organized as a set of independent backend services supported by shared internal libraries, a relational database, a cache layer, and an observability foundation. The current implementation focuses on two bounded domains:

- **User Service** — lifecycle management of user accounts and roles.
- **Document Gateway** — upload, storage, parsing, chunking, and vector-oriented retrieval of tabular documents.

From an architectural perspective, the project demonstrates the practical application of:

- layered service design;
- domain-driven modeling of aggregates and domain events;
- asynchronous application flows;
- the Unit of Work and Repository patterns;
- reusable infrastructure modules for idempotency, metrics, error handling, and logging;
- container-based local deployment.

The repository should be read both as a technical implementation and as a compact architectural case study for a diploma paper.

---

## 1. Project Goal

The goal of the project is to design and implement a modular backend platform that can serve as the core of an ERP-like information system. The solution aims to prove the following thesis:

> A service-oriented backend built on explicit domain boundaries, reusable platform patterns, and observable infrastructure is easier to evolve, test, and extend than a tightly coupled monolith.

To support that goal, the project introduces:

- independent services for different business capabilities;
- shared packages for architectural patterns and platform utilities;
- a consistent command/event execution model inside services;
- a deployable local environment based on Docker Compose;
- a foundation for auditability and operational monitoring.

---

## 2. Research and Engineering Context

Modern enterprise systems must process business data reliably, expose stable APIs, and remain maintainable as requirements grow. In practice, this creates several engineering challenges:

- keeping business rules separated from transport and persistence details;
- making service behavior observable in development and operations;
- preventing duplicated infrastructure code across services;
- enabling future scaling of individual domains without rewriting the whole system.

This project addresses these challenges through a **microservice-inspired architecture**. Each service owns its own API and application logic, while cross-cutting concerns are extracted into internal shared packages.

---

## 3. Architectural Overview

### 3.1 High-Level Structure

The repository is divided into three main layers:

1. **Application services** in `apps/`
2. **Shared internal libraries** in `packages/`
3. **Operational and observability assets** in `observability/`

```text
.
├── apps/
│   ├── user-service/
│   └── document-gateway/
├── packages/
│   ├── patterns/
│   └── utils/
├── observability/
│   ├── grafana/
│   ├── logstash/
│   └── prometheus/
├── docker-compose.yaml
└── example.env
```

### 3.2 Architectural Style

The implementation combines several complementary styles:

- **Service-oriented decomposition** at repository level;
- **Layered architecture** inside each service;
- **DDD-inspired domain modeling** for aggregates and domain events;
- **Message-bus orchestration** for command and event handling;
- **Repository + Unit of Work** for persistence isolation.

This results in a system where HTTP endpoints remain thin, domain entities encapsulate state transitions, and infrastructure concerns are replaceable.

---

## 4. Implemented Services

### 4.1 User Service

**Location:** `apps/user-service`

The User Service manages user accounts and core account operations. Its API is implemented with FastAPI and its internal workflow is asynchronous.

### Functional scope

- user registration;
- user listing and profile retrieval;
- profile update;
- password change;
- activation and deactivation;
- promotion to administrator role.

### Architectural characteristics

- FastAPI API layer in `src/fastapi_app.py`
- command/event bootstrap in `src/bootstrap/async_settings.py`
- domain aggregate `User` in `src/domains/users/model.py`
- asynchronous command handlers in `src/gateway/handlers/async_user.py`
- async Unit of Work and repositories in `src/infrastructure/` and `src/repository/`

### Domain model

The central aggregate is `User`, which encapsulates:

- identity;
- email and username uniqueness rules;
- locale;
- activation state;
- role transitions.

The aggregate emits domain events such as:

- `UserRegistered`
- `UserProfileUpdated`
- `UserPasswordChanged`
- `UserActivated`
- `UserDeactivated`
- `UserRoleChanged`

These events are consumed by the internal message bus and can be routed to infrastructure-side publishers or notifiers.

### 4.2 Document Gateway

**Location:** `apps/document-gateway`

The Document Gateway manages uploaded business documents and prepares them for vector-style retrieval.

### Functional scope

- document creation with file upload;
- file persistence on local storage;
- document download;
- document metadata update;
- document deletion;
- chunk listing;
- semantic-style chunk search using embeddings.

### Processing pipeline

The implemented document pipeline is sequential and explicit:

1. create document metadata;
2. save uploaded file to storage;
3. parse CSV / Excel-like tabular content;
4. transform rows into textual chunks;
5. generate embeddings for chunks;
6. persist chunks for vector search.

### Domain model

The main aggregate is `Document`, which moves through the following states:

- `CREATED`
- `UPLOADED`
- `PARSED`
- `READY`

The service also models `Chunk` entities that store:

- document reference;
- textual chunk content;
- vector embedding.

### Vector-search implementation

The service stores embeddings in PostgreSQL using **pgvector** and defines an HNSW index for chunk similarity search. This creates a practical basis for retrieval-augmented workflows over tabular business documents.

### Current implementation note

The codebase already contains an `OpenAIEmbeddingGenerator`, but the active execution path currently uses `MockEmbeddingGenerator`. In other words, the vector pipeline and schema are implemented, while production embedding-provider integration remains a future extension.

---

## 5. Shared Internal Packages

### 5.1 `packages/patterns`

This package contains reusable architectural patterns used by services:

- aggregate base class;
- message abstractions;
- asynchronous message bus;
- repository interfaces;
- Unit of Work abstractions;
- observability hook contracts.

Its purpose is to standardize application flow across services and reduce duplication of architectural code.

### 5.2 `packages/utils`

This package contains reusable infrastructure and domain utilities:

- shared exception hierarchy;
- FastAPI exception handler installation;
- idempotency middleware backed by Redis;
- Prometheus metrics middleware;
- logging helpers.

This package represents the common platform layer shared by application services.

---

## 6. Internal Service Layering

Both services follow a similar internal structure:

```text
src/
├── bootstrap/       # message bus assembly and dependency wiring
├── cli/             # FastAPI entrypoints
├── config.py        # environment-based settings
├── domains/         # aggregates and domain logic
├── dto/             # commands, events, and transfer models
├── gateway/         # HTTP handlers and schemas
├── infrastructure/  # DB, logging, hooks, storage, middleware integration
└── repository/      # repository implementations
```

### Layer responsibilities

- **CLI layer** exposes HTTP endpoints.
- **Gateway layer** converts transport input into application commands.
- **Bootstrap layer** connects commands, events, handlers, and dependencies.
- **Domain layer** encapsulates business state and invariants.
- **Repository / infrastructure layers** implement persistence and technical services.

This separation keeps domain logic independent from FastAPI and database details.

---

## 7. Persistence Model

### 7.1 Relational storage

The project uses **PostgreSQL** as the primary data store.  
The Document Gateway specifically uses the **pgvector** extension through the `pgvector/pgvector:pg18` image.

### 7.2 User data

The User Service persists user records through asynchronous SQLAlchemy-based infrastructure.

### 7.3 Document data

The Document Gateway persists:

- document metadata in the `documents` table;
- vectorized chunks in the `chunks` table;
- document binaries in a mounted filesystem directory defined by `DOCUMENT_STORAGE_DIR`.

### 7.4 Migrations

Both services include **Alembic** configuration and migration files, which formalize schema evolution and support reproducible environment setup.

---

## 8. Cross-Cutting Concerns

### 8.1 Error handling

Shared exception handlers in `packages/utils` produce consistent JSON error responses and attach correlation identifiers when available.

### 8.2 Logging and audit support

Each service configures:

- console logging;
- optional Logstash-compatible asynchronous logging;
- request correlation through request IDs;
- audit-oriented structured logging hooks.

### 8.3 Metrics

Both services expose a `/metrics` endpoint and can enable Prometheus instrumentation via `PROM_ENABLED`.

### 8.4 Idempotency

The shared Redis-backed idempotency middleware caches eligible HTTP responses and helps stabilize repeated requests. In the current code, the middleware is applied in both services and is oriented around repeated safe request handling.

---

## 9. Observability Foundation

The repository includes a dedicated `observability/` directory with configuration for:

- **Prometheus**
- **Logstash**
- **Grafana**

These files define the intended operational stack of the platform. At present:

- Docker Compose directly launches `user-service`, `document-gateway`, `postgres`, and `redis`;
- observability configuration files are present in the repository;
- full runtime wiring of Grafana / Elasticsearch / Logstash services is a planned operational extension rather than a fully composed local stack.

This is an important distinction for diploma documentation: the project already defines the observability contract, but not every operational component is yet started by the current Compose file.

---

## 10. Testing Strategy and Current Coverage

The repository currently contains explicit test coverage for the **User Service**:

- **unit tests** for user-domain behavior;
- **integration tests** for message-bus, Unit of Work, and observability-hook flows;
- **end-to-end API tests** for the FastAPI lifecycle.

This test suite validates the core user-management slice from domain logic to HTTP interface.

### Current limitation

At the time reflected by this repository state, equivalent automated test coverage is not yet present for the Document Gateway. This should be treated as one of the next engineering priorities.

---

## 11. Deployment Model

### 11.1 Local environment

The local runtime is defined in `docker-compose.yaml`.

### Services started by Compose

- `user-service` on port **8001**
- `document-gateway` on port **8002**
- `postgres` on port **5432**
- `redis` on port **6379**

### Persistent volumes

- `postgres_data`
- `documents_data`

### Environment configuration

The root `example.env` file defines the shared variables used by the local environment, including:

- application name and mode flags;
- database connection settings;
- Redis configuration;
- logging and request ID configuration;
- document-gateway storage and embedding parameters.

---

## 12. Technology Stack

### Core backend

- Python 3.12
- FastAPI
- SQLAlchemy 2
- Alembic
- Uvicorn

### Data and messaging support

- PostgreSQL
- pgvector
- Redis

### Data processing

- Pandas
- OpenPyXL
- NumPy

### AI / retrieval integration

- OpenAI SDK (prepared in codebase, not yet active in the default document flow)

### Observability

- Prometheus client
- Logstash async handler
- Grafana / Prometheus / Logstash configuration assets

### Packaging

- Poetry
- Docker Compose

---

## 13. Repository Walkthrough

### `apps/user-service`

Implements user management as an asynchronous service with domain events and tested business flows.

### `apps/document-gateway`

Implements document ingestion and retrieval preparation with local file storage and pgvector-backed chunk search.

### `packages/patterns`

Provides architectural abstractions reused by services.

### `packages/utils`

Provides infrastructure helpers reused by services.

### `observability`

Contains the operational blueprints for metrics, logs, and dashboards.

---

## 14. How to Run the Project

### 14.1 Prerequisites

- Docker and Docker Compose
- Python 3.12
- Poetry

### 14.2 Local startup with Docker Compose

1. Create an environment file from the example:

```bash
cp example.env .env
```

2. Start the local stack:

```bash
docker compose up --build
```

This starts PostgreSQL, Redis, User Service, and Document Gateway.

### 14.3 Service-level manual startup

Each service also contains its own Python project files and Alembic setup. A typical service-level run sequence is:

```bash
poetry install
poetry run alembic upgrade head
poetry run uvicorn src.fastapi_app:app --reload --port <service-port>
```

Default ports in the current architecture:

- User Service — `8001`
- Document Gateway — `8002`

---

## 15. API Summary

### 15.1 User Service API

Representative endpoints:

- `GET /users`
- `POST /users`
- `GET /users/{user_id}`
- `PATCH /users/{user_id}`
- `POST /users/{user_id}/password`
- `POST /users/{user_id}/activate`
- `POST /users/{user_id}/deactivate`
- `POST /users/{user_id}/promote`
- `GET /metrics`

### 15.2 Document Gateway API

Representative endpoints:

- `GET /documents`
- `POST /documents`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/download`
- `PATCH /documents/{document_id}`
- `DELETE /documents/{document_id}`
- `GET /documents/{document_id}/chunks`
- `GET /documents/{document_id}/chunks/search`
- `GET /metrics`

---

## 16. Architectural Strengths

The current repository demonstrates several strong engineering properties:

- clear domain separation between users and documents;
- reusable architectural and infrastructure packages;
- explicit service boundaries;
- asynchronous application flow;
- observable HTTP services;
- built-in extensibility for event publication and notification flows;
- an implemented foundation for vector retrieval over structured business documents.

These features make the project suitable as both a diploma artifact and a practical prototype.

---

## 17. Known Limitations

The current state of the project also includes known limitations:

- document embeddings use a mock generator in the active flow;
- document-gateway automated tests are not yet present at the same level as user-service tests;
- the Compose stack does not yet start the full observability platform;
- some event-driven integrations are scaffolded through protocols and hooks, but external brokers/providers are still future work;
- API gateway / ingress composition is not yet represented as a separate runtime component.

These limitations are not defects in the architectural concept; rather, they define the next iteration scope.

---

## 18. Future Development Directions

Recommended next steps for the project are:

1. activate real embedding generation with secure provider configuration;
2. add document-gateway unit, integration, and API tests;
3. extend Compose with Grafana, Prometheus, Logstash, and Elasticsearch containers;
4. introduce an API gateway or reverse proxy for unified routing;
5. connect domain events to a real broker for cross-service communication;
6. add authentication, authorization, and stronger security controls;
7. formalize CI validation for linting, tests, and migrations.

---

## 19. Conclusion

This repository presents a coherent backend architecture for a diploma-level enterprise system prototype.  
Its value lies not only in the implemented endpoints, but in the architectural discipline behind them: explicit domain boundaries, reusable patterns, asynchronous workflows, and operational awareness.

In its current form, the project already demonstrates:

- a functioning multi-service backend;
- shared platform abstractions;
- a vector-ready document-processing pipeline;
- tested user-management workflows;
- a credible foundation for further ERP-oriented development.

For academic and engineering purposes, the system can therefore be considered a meaningful intermediate result: sufficiently implemented to validate the architectural approach, and sufficiently extensible to support future applied research and product evolution.
