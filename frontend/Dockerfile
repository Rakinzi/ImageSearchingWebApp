# Multi-stage build for Vue.js frontend
# Stage 1: Build stage
FROM alpine:latest AS builder

# Install Node.js and Bun with required C++ libraries
RUN apk add --no-cache \
    curl \
    unzip \
    bash \
    libstdc++ \
    libgcc \
    && curl -fsSL https://bun.sh/install | bash \
    && rm -rf /var/cache/apk/*

# Add Bun to PATH
ENV BUN_INSTALL="/root/.bun"
ENV PATH="$BUN_INSTALL/bin:$PATH"

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with retry logic and cache clearing
RUN rm -rf ~/.bun/install/cache && \
    bun install --verbose || \
    (echo "First attempt failed, retrying..." && sleep 2 && bun install --verbose) || \
    (echo "Second attempt failed, trying with --force..." && bun install --force --verbose)

# Explicitly install the platform-specific Rollup binary for Alpine (musl libc)
RUN bun add -d @rollup/rollup-linux-x64-musl

# Copy source code
COPY . .

# Build argument for API URL (default for Docker internal networking)
ARG VITE_API_URL=http://backend:8080
ENV VITE_API_URL=${VITE_API_URL}

# Build the application
RUN bun run build

# Stage 2: Production stage with nginx
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
