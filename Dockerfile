FROM nginx:1.27-alpine

COPY deploy/schemas/nginx.conf /etc/nginx/conf.d/default.conf
COPY schemas /usr/share/nginx/html/schemas
COPY deploy/schemas/index.html /usr/share/nginx/html/index.html

RUN mkdir -p /usr/share/nginx/html/health \
    && echo '{"status":"ok"}' > /usr/share/nginx/html/health/index.json

EXPOSE 80
