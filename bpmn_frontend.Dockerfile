FROM node:20 AS build-stage
WORKDIR /app

COPY src/bpmn_frontend/package*.json ./
RUN npm install
COPY src/bpmn_frontend .

RUN npm run build

FROM nginx:stable-alpine AS production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]