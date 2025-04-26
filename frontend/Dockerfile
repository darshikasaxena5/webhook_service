# frontend/Dockerfile

# Stage 1: Build the Next.js application
FROM node:18-alpine AS builder
WORKDIR /app

# Set environment variables if needed during build
# ARG NEXT_PUBLIC_API_BASE_URL
# ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

# Copy package manager files
COPY package.json package-lock.json* ./

# Install dependencies using npm ci for faster, reliable builds
RUN npm ci

# Copy the rest of the application source code
COPY . .

# Build the Next.js application
RUN npm run build


# Stage 2: Production image using standalone output
FROM node:18-alpine AS runner
WORKDIR /app

# Set environment variables
ENV NODE_ENV=production
# Railway injects the PORT environment variable. Next.js standalone output listens on $PORT.

# Disable telemetry
ENV NEXT_TELEMETRY_DISABLED 1

# Create a non-root user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files from the builder stage (thanks to output: 'standalone')
# Make sure you have output: 'standalone' in your next.config.js
COPY --from=builder /app/public ./public
# Copy the standalone server output
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
# Copy the static assets
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Expose port (informational, Vercel/Railway handle the actual port)
# EXPOSE 3000

# Set the user to run the application
USER nextjs

# Command to run the Next.js production server from standalone output
# server.js is the default entrypoint for standalone output and listens on $PORT (or 3000 if not set)
CMD ["node", "server.js"]
