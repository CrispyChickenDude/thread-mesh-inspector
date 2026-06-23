ARG BUILD_FROM
FROM $BUILD_FROM

# Install system dependencies
# - docker-cli: needed to exec ot-ctl into the house OTBR container
# - openssh-client: needed to SSH into the garage OTBR VM
# - iputils: ping6 for reachability checks
RUN apk add --no-cache \
    docker-cli \
    openssh-client \
    iputils \
    && rm -rf /var/cache/apk/*

# Install Python backend dependencies
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy pre-built frontend bundle
COPY frontend/dist/ ./frontend/dist/

# Copy add-on run script
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
