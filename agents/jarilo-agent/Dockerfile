FROM python:3.11-slim

WORKDIR /app

# Install bash and other tools
RUN apt-get update && apt-get install -y bash gawk && rm -rf /var/lib/apt/lists/*

# Create workspace directory
RUN mkdir -p /workspace

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent script
COPY agent.sh /app/agent.sh

RUN chmod +x /app/agent.sh

CMD ["/app/agent.sh"]