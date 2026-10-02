FROM node:latest
WORKDIR /usr/src/app

# Copy package.json and install dependencies
COPY package.json .
RUN npm install

# Copy application files
COPY . .

# Build-time metadata
ARG SOURCE_DATE_EPOCH
ARG GIT_COMMIT_SHA
ARG CICD_BUILD_TIME
ENV SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH
ENV GIT_COMMIT_SHA=$GIT_COMMIT_SHA
ENV CICD_BUILD_TIME=$CICD_BUILD_TIME

# Expose the application port
EXPOSE 8628

# Start the application
CMD [ "node", "index.js" ]
