# 1. Dependencies stage
FROM node:20-slim AS deps

# Enable pnpm
RUN corepack enable

WORKDIR /app

# Copy dependency information
COPY docker/frontend/package.json ./
COPY docker/frontend/pnpm-lock.yaml* ./

# Install dependencies
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --no-frozen-lockfile

# 2. Build stage
FROM node:20-slim AS builder

# Enable pnpm
RUN corepack enable

WORKDIR /app

# Copy dependencies from deps stage first
COPY --from=deps /app/node_modules ./node_modules

# Copy package.json
COPY docker/frontend/package.json ./

# Copy only necessary source files (exclude node_modules and .next)
COPY docker/frontend/app ./app
COPY docker/frontend/components* ./components
COPY docker/frontend/lib* ./lib
COPY docker/frontend/next-env.d.ts* ./
COPY docker/frontend/next.config* ./
COPY docker/frontend/tsconfig.json* ./
COPY docker/frontend/tailwind.config* ./
COPY docker/frontend/postcss.config* ./
COPY docker/frontend/public* ./public

# Set environment variable for the API URL at build time
ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

# Build the application
RUN pnpm build

# 3. Production stage
FROM node:20-slim AS runner

# Enable pnpm
RUN corepack enable

WORKDIR /app

# Set to production environment
ENV NODE_ENV=production
ENV PORT=3000

# Copy necessary files from builder
COPY --from=builder /app/package.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules

# Expose port
EXPOSE 3000

# Start the application
CMD ["pnpm", "start"]
