ARG BUILD_FROM
FROM $BUILD_FROM AS base

# Install system dependencies
# - docker-cli: needed to exec ot-ctl into the house OTBR container
# - openssh-client: needed to SSH into the garage OTBR VM
# - iputils: ping6 for reachability checks
# - nodejs/npm: build the frontend bundle
RUN apk add --no-cache \
    docker-cli \
    openssh-client \
    iputils \
    nodejs \
    npm \
    && rm -rf /var/cache/apk/*

# Build frontend
WORKDIR /build/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Install Python backend dependencies
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend bundle from build stage
COPY --from=base /build/frontend/dist/ ./frontend/dist/

# Copy add-on run script
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
