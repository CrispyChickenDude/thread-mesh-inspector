#!/usr/bin/with-contenv bashio

# Read add-on options
POLL_INTERVAL=$(bashio::config 'poll_interval_seconds')
LIVE_POLL_INTERVAL=$(bashio::config 'live_poll_interval_seconds')
LOG_LEVEL=$(bashio::config 'log_level')
MOCK_MODE=$(bashio::config 'mock_mode')

bashio::log.info "Starting Thread Mesh Inspector v0.1.0"
bashio::log.info "Poll interval: ${POLL_INTERVAL}s | Live poll: ${LIVE_POLL_INTERVAL}s | Mock: ${MOCK_MODE}"

# Export for the Python backend
export TMI_POLL_INTERVAL="${POLL_INTERVAL}"
export TMI_LIVE_POLL_INTERVAL="${LIVE_POLL_INTERVAL}"
export TMI_LOG_LEVEL="${LOG_LEVEL}"
export TMI_MOCK_MODE="${MOCK_MODE}"
export TMI_DATA_DIR="/data"
export TMI_CONFIG_FILE="/data/config.yaml"
export TMI_SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}"

# Start the FastAPI backend (also serves the frontend static bundle)
exec python3 -m backend.app
