FROM node:18

WORKDIR /usr/src/app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source
COPY . .

EXPOSE 5000

CMD ["npm", "start"]