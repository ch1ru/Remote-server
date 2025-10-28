FROM node:20-alpine

WORKDIR /igv

COPY dist/ ./dist

# Serve static files
RUN npm install -g http-server

EXPOSE 8080

CMD ["http-server", "dist", "-p", "8080", "-c-1", "--cors"]
