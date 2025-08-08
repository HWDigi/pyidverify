# Multi-stage Docker build for PyIDVerify
# Security-hardened production container for ID verification services

# Build stage
FROM python:3.11-slim-bookworm as builder

# Security: Run as non-root user
RUN groupadd -r pyidverify && useradd -r -g pyidverify pyidverify

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./
COPY pyproject.toml VERSION ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY pyidverify/ ./pyidverify/
COPY README.md CHANGELOG.md LICENSE ./

# Install the package
RUN pip install --no-cache-dir -e .

# Production stage
FROM python:3.11-slim-bookworm as production

# Security labels
LABEL maintainer="PyIDVerify Security Team <security@pyidverify.com>"
LABEL org.opencontainers.image.title="PyIDVerify"
LABEL org.opencontainers.image.description="Enterprise-grade ID verification with military-level security"
LABEL org.opencontainers.image.vendor="PyIDVerify"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/pyidverify/pyidverify"
LABEL org.opencontainers.image.documentation="https://pyidverify.readthedocs.io"
LABEL security.policy="https://github.com/pyidverify/pyidverify/blob/main/SECURITY.md"

# Security: Create non-root user
RUN groupadd -r pyidverify && useradd -r -g pyidverify -s /bin/bash pyidverify

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libssl3 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set security-hardened environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYIDVERIFY_SECURITY_LEVEL=maximum \
    PYIDVERIFY_CONTAINER_MODE=true \
    PYIDVERIFY_LOG_LEVEL=INFO

# Create application directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder --chown=pyidverify:pyidverify /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder --chown=pyidverify:pyidverify /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder --chown=pyidverify:pyidverify /app/pyidverify ./pyidverify
COPY --chown=pyidverify:pyidverify README.md CHANGELOG.md LICENSE ./

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data /app/config && \
    chown -R pyidverify:pyidverify /app

# Security: Remove unnecessary packages and clean up
RUN apt-get autoremove -y && \
    apt-get autoclean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Switch to non-root user
USER pyidverify

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import pyidverify; print('PyIDVerify is healthy')" || exit 1

# Expose port (if running as web service)
EXPOSE 8000

# Volume for persistent data
VOLUME ["/app/data", "/app/logs"]

# Default command
CMD ["python", "-m", "pyidverify.server"]

# Security scanning metadata
LABEL security.scan.vendor="Trivy,Snyk,Docker Scout"
LABEL security.compliance="GDPR,HIPAA,PCI-DSS,SOX"
LABEL security.encryption="AES-256-GCM,ChaCha20-Poly1305,Argon2id"

# Development stage (for development builds)
FROM builder as development

# Install development dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Install debugging tools
RUN apt-get update && apt-get install -y \
    vim \
    git \
    htop \
    strace \
    && rm -rf /var/lib/apt/lists/*

# Set development environment
ENV PYIDVERIFY_SECURITY_LEVEL=development \
    PYIDVERIFY_DEBUG=true \
    PYIDVERIFY_TEST_MODE=true

# Switch to non-root user
USER pyidverify

# Development command
CMD ["python", "-c", "print('PyIDVerify development container ready'); exec(open('/bin/bash').read())"]

# Testing stage
FROM development as testing

# Copy test files
COPY --chown=pyidverify:pyidverify tests/ ./tests/

# Set testing environment
ENV PYIDVERIFY_SECURITY_LEVEL=testing \
    PYIDVERIFY_TEST_MODE=true \
    PYTEST_CURRENT_TEST=true

# Run tests by default
CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
