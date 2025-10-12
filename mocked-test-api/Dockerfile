FROM node:18-alpine

WORKDIR /app

RUN npm install -g @stoplight/prism-cli@4

COPY package.json /app/
RUN npm install --production

COPY . /app/

EXPOSE 8000

CMD ["node", "server.js"]
