FROM node:22-alpine

WORKDIR /app

RUN apk add --no-cache openssl

COPY package*.json ./
RUN npm install

COPY . .

# Generate HTTPS cert once at build time
RUN npm run cert:dev

EXPOSE 5173 5174

# Start both HTTP and HTTPS servers in parallel
CMD ["sh", "-lc", "VITE_DEV_HTTPS=false npx vite --port 5173 --host 0.0.0.0 & VITE_DEV_HTTPS=true npx vite --port 5174 --host 0.0.0.0 & wait"]