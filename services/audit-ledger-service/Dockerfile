FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json pnpm-workspace.yaml ./
COPY packages ./packages
COPY services/audit-ledger-service ./services/audit-ledger-service
RUN npm install -g pnpm && pnpm install --frozen-lockfile=false && pnpm build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app ./
EXPOSE 3006
CMD ["node", "services/audit-ledger-service/dist/index.js"]
