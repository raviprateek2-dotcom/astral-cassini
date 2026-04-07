# Frontend Dockerfile for PRO HR
# Building with multi-stage for efficiency

# Stage 1: Build process
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first for caching purposes
COPY package.json package-lock.json* ./
RUN npm ci

# Copy the source code
COPY . .

# Build-time env (inlined into client/server bundles where Next reads process.env)
# - Leave NEXT_PUBLIC_API_URL empty for same-origin /api → rewrites use BACKEND_URL (recommended in Docker Compose).
# - Set NEXT_PUBLIC_API_URL to an absolute origin when the browser must call the API host directly.
ARG NEXT_PUBLIC_API_URL=
ARG BACKEND_URL=http://127.0.0.1:8000
ARG NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV BACKEND_URL=$BACKEND_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

RUN npm run build

# Stage 2: Production runner
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV production
ENV PORT 3000

# Copy necessary build artifacts from the builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules

# Expose the frontend port
EXPOSE 3000

# Start the Next.js production server
CMD ["npm", "start"]
