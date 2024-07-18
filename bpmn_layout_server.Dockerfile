FROM node:20

WORKDIR /app

COPY src/bpmn_layout_server/package*.json ./

RUN npm install

COPY src/bpmn_layout_server .

EXPOSE 3001

CMD ["node", "server.js"]