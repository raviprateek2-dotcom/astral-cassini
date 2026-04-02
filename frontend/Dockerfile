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

# Build the Next.js application
# Ensure we pass the backend URL as a build arg if needed for client-side
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

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
