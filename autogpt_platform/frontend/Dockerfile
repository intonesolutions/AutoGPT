# Base stage for both dev and prod
FROM node:slim AS base
WORKDIR /app
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

ENV NODE_ENV=development
ENV HOSTNAME=0.0.0.0
COPY ./.next/standalone .
COPY ./.next/static ./.next/static
COPY ./public ./public
RUN rm -f node_modules
RUN npm install --legacy-peer-deps


EXPOSE 3000
CMD ["node", "server.js"]
# CMD ["/bin/sh", "-c", "sleep infinity"] 