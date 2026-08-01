FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json pnpm-workspace.yaml ./
COPY packages ./packages
COPY services/ai-agent-service ./services/ai-agent-service
RUN npm install -g pnpm && pnpm install --frozen-lockfile=false && pnpm build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app ./
EXPOSE 3005
CMD ["node", "services/ai-agent-service/dist/index.js"]
