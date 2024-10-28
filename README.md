# Paylinker Project

## Overview

The Paylinker project is a payment link management system that allows users to create and manage payment links for various transactions. It supports features like rate limiting, idempotency, and customizable link settings.

## Requirements

Before you begin, ensure you have the following installed on your machine:

- Python 3.x
- pip (Python package installer)
- PostgreSQL (or your preferred database)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/isaacoduh/paylinker-api.git
cd paylinker
```

### 2. Setup a Virtual Environment

```bash
    # Create a virtual environment
    python -m venv venv

    # Activate the virtual environment
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
```

### 3. Install Dependencies

```bash
    pip install -r requirements.txt
```

### 4. Setup the Database

```bash
    CREATE DATABASE paylinker;

```

### 5. Run the Application

```bash
    uvicorn app.main:app --reload

```

## Running Tests

To run the unit tests without a virtual environment, you can simply use the pytest framework installed on your system. Ensure all required dependencies are installed `(from requirements.txt)`.

### 1. Install Pytest (if not already installed)

```bash
    pip install pytest

```

### 2. Run tests

```bash
    pytest
```

## Further Improvements

- Implementing rate limiting using Redis.
- Allow users to create "vanquishable" links that expire after payment.
- Enhancing idempotency to prevent duplicate transactions.

## License

Feel free to modify any sections to better fit your project's specifics!
