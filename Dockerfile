FROM python:3.13-slim

# Install Node.js, AWS CLI and additional utilities
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    iproute2 \
    iputils-ping \
    net-tools \
    dnsutils \
    sudo \
    git \
    jq \
    unzip \
    procps \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws

# Set non-sensitive environment variables
ENV PYTHONPATH=/app:/app/src

# Create a non-root user
RUN useradd -ms /bin/bash appuser

# Create app directory with proper ownership
RUN mkdir -p /app && chown appuser:appuser /app

# Install Python dependencies as root to avoid permission issues
WORKDIR /app
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir boto3==1.34.23 botocore==1.34.23 uvicorn fastapi \
    && pip install --no-cache-dir langchain-aws \
    && mkdir -p /home/appuser/.aws && chown -R appuser:appuser /home/appuser/

# Now switch to non-root user for remaining operations
USER appuser

# Copy application code
COPY --chown=appuser src ./src
COPY --chown=appuser chat-ui ./chat-ui

# Build the frontend
WORKDIR /app/chat-ui
RUN npm install && \
    npm run build && \
    mkdir -p /app/chat-ui/dist && \
    if [ -d "/app/chat-ui/.svelte-kit/output/client" ]; then \
        cp -r /app/chat-ui/.svelte-kit/output/client/* /app/chat-ui/dist/; \
    fi

# Back to app directory
WORKDIR /app

# Copy entrypoint script
COPY --chown=appuser docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Expose ports
EXPOSE 1234 5173

# Start the application
ENTRYPOINT ["./docker-entrypoint.sh"]
