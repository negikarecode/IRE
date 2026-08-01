FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json pnpm-workspace.yaml ./
COPY packages ./packages
COPY services/reasoning-engine-service ./services/reasoning-engine-service
RUN npm install -g pnpm && pnpm install --frozen-lockfile=false && pnpm build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app ./
EXPOSE 3004
CMD ["node", "services/reasoning-engine-service/dist/index.js"]
