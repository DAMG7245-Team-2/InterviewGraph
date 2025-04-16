# Use Python 3.12 as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Copy poetry files for interview_agent
COPY backend/interview_agent/pyproject.toml backend/interview_agent/poetry.lock ./backend/interview_agent/

# Copy poetry files for prep_agent
COPY backend/prep_agent/pyproject.toml backend/prep_agent/poetry.lock ./backend/prep_agent/

# Configure Poetry to not create virtualenvs
RUN poetry config virtualenvs.create false
    
# Install project dependencies
RUN poetry install --no-interaction --no-ansi

# Copy the rest of the application
COPY . .

RUN pip install -e ./backend/interview_agent
RUN pip install -e ./backend/prep_agent

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["poetry", "run", "uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
