# Build React app
FROM node:18 AS build
WORKDIR /app

COPY package*.json ./
RUN npm install --no-audit --no-fund

COPY . ./
RUN npm run build

# Serve static files only (no API proxy)
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80
