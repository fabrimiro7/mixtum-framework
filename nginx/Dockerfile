# syntax=docker/dockerfile:1
FROM node:20-alpine AS build

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build -- --configuration production

FROM nginx:alpine
COPY --from=build /app/frontend/dist/ /usr/share/nginx/html
