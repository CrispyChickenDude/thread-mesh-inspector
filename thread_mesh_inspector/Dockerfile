ARG BUILD_FROM
FROM $BUILD_FROM

# Install system dependencies
# - docker-cli: needed to exec ot-ctl into the house OTBR container
# - openssh-client: needed to SSH into the garage OTBR VM
# - iputils: ping6 for reachability checks
# - nodejs/npm: build the frontend bundle (removed after build)
RUN apk add --no-cache \
    docker-cli \
    openssh-client \
    iputils \
    nodejs \
    npm \
    && rm -rf /var/cache/apk/*

WORKDIR /app

# Build frontend bundle in place (produces /app/frontend/dist)
COPY frontend/package.json ./frontend/package.json
RUN cd frontend && npm install
COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# Install Python backend dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy add-on run script
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
