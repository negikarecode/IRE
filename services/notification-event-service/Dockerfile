FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json pnpm-workspace.yaml ./
COPY packages ./packages
COPY services/notification-event-service ./services/notification-event-service
RUN npm install -g pnpm && pnpm install --frozen-lockfile=false && pnpm build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app ./
EXPOSE 3007
CMD ["node", "services/notification-event-service/dist/index.js"]
