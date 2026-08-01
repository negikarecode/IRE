FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json pnpm-workspace.yaml ./
COPY packages ./packages
COPY gateway/api-gateway ./gateway/api-gateway
RUN npm install -g pnpm && pnpm install --frozen-lockfile=false && pnpm build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app ./
EXPOSE 8000
CMD ["node", "gateway/api-gateway/dist/index.js"]
