# Stage 1: Build Tailwind CSS
FROM node:20-alpine AS tailwind-builder

WORKDIR /app

# Include the Django templates and scripts Tailwind scans when generating CSS.
COPY core/ ./core/
COPY theme/ ./theme/

# Install dependencies and build production CSS
WORKDIR /app/theme/static_src
RUN npm ci && npm run build


# Stage 2: Build the Django application
FROM python:3.13-slim AS django-app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Django application
COPY . .

# Copy compiled Tailwind CSS into the Django application
COPY --from=tailwind-builder \
    /app/theme/static/css/dist/styles.css \
    /app/theme/static/css/dist/styles.css

EXPOSE 8000

CMD ["gunicorn", "balance.wsgi:application", "--bind", "0.0.0.0:8000"]
