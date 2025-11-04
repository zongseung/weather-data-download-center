# 1. Dependencies stage
FROM node:20-slim AS deps

# Enable pnpm
RUN corepack enable

WORKDIR /app

# Copy dependency information
COPY frontend/package.json ./
COPY frontend/pnpm-lock.yaml* ./

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
COPY frontend/package.json ./

# Copy only necessary source files (exclude node_modules and .next)
COPY frontend/app ./app
COPY frontend/components* ./components
COPY frontend/lib* ./lib
COPY frontend/next-env.d.ts* ./
COPY frontend/next.config* ./
COPY frontend/tsconfig.json* ./
COPY frontend/tailwind.config* ./
COPY frontend/postcss.config* ./
COPY frontend/public* ./public

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
