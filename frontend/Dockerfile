# Vite bakes VITE_* env vars into the built JS at build time, not runtime --
# so the API URL has to be a build ARG here, not a docker-compose
# `environment:` entry (which would have no effect on an already-built
# static bundle served by nginx).
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL=http://localhost:8010
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
