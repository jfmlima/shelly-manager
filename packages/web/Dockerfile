FROM node:20-alpine AS builder

RUN apk update && apk upgrade && apk add --no-cache dumb-init

RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

WORKDIR /app

COPY package*.json ./

RUN npm ci --include=dev && npm cache clean --force

COPY --chown=nextjs:nodejs . .

ARG VITE_BASE_API_URL
ENV VITE_BASE_API_URL=$VITE_BASE_API_URL

RUN npm run build

FROM nginx:1.25-alpine AS runtime

RUN apk update && apk upgrade && \
    apk add --no-cache curl dumb-init && \
    rm -rf /var/cache/apk/*

RUN addgroup -g 1001 -S nginx-app && \
    adduser -S nginx-app -u 1001 -G nginx-app

COPY --from=builder --chown=nginx-app:nginx-app /app/dist /usr/share/nginx/html

COPY --chown=nginx-app:nginx-app nginx.conf /etc/nginx/conf.d/default.conf

RUN chown -R nginx-app:nginx-app /usr/share/nginx/html && \
    chown -R nginx-app:nginx-app /var/cache/nginx && \
    chown -R nginx-app:nginx-app /var/log/nginx && \
    chown -R nginx-app:nginx-app /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx-app:nginx-app /var/run/nginx.pid

USER nginx-app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || curl -f http://localhost:8080/ || exit 1

ENTRYPOINT ["dumb-init", "--"]

CMD ["nginx", "-g", "daemon off;"]
