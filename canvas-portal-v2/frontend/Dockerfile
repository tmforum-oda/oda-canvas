FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

RUN npm run build

FROM nginx:1.27-alpine

ENV FRONTEND_PORT=80 \
    NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1 \
    BACKEND_UPSTREAM=http://canvas-portal-backend:8080 \
    KEYCLOAK_UPSTREAM=http://127.0.0.1:65535/auth \
    APP_API_BASE_URL= \
    APP_KEYCLOAK_URL=/auth \
    APP_KEYCLOAK_REALM=canvas \
    APP_KEYCLOAK_CLIENT_ID=canvas-portal

COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.d/30-runtime-config.sh /docker-entrypoint.d/30-runtime-config.sh
COPY --from=build /app/dist /usr/share/nginx/html

RUN chmod +x /docker-entrypoint.d/30-runtime-config.sh

EXPOSE 80
