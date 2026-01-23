# Frontend Dockerfile for Multi-Agent Intelligence Platform
# Using Node 22 for Vite 7.2.4 compatibility (requires Node 20.19+ or 22.12+)
FROM node:22-alpine

# Set working directory
WORKDIR /app

# Copy package files first (for better caching)
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Run development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
