FROM telegraf:1.33

# Install Python for the execd processor decoder script
RUN apt-get update && apt-get install -y python3 && rm -rf /var/lib/apt/lists/*

# The decoder script will be mounted at runtime via docker-compose volumes
