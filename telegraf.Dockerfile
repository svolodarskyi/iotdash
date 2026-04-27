FROM telegraf:1.33

# Install Python and pip for the execd processor decoder script
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies for MessagePack decoding
RUN pip3 install --no-cache-dir msgpack

# The decoder script will be mounted at runtime via docker-compose volumes
