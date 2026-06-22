# ─────────────────────────────────────────────────────────────
#  DevelopIndo — Frontend Dockerfile (development)
#  Next.js dev server with hot reload via volume mount
# ─────────────────────────────────────────────────────────────

FROM node:20-alpine

WORKDIR /app

# Install dependencies first (cached layer)
COPY package.json package-lock.json ./
RUN npm ci

# No COPY . . here — code is mounted via volume for hot reload
EXPOSE 3000
CMD ["npm", "run", "dev"]
