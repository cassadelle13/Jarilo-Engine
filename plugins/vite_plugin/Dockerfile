FROM node:20-slim

# Set working directory
WORKDIR /workspace

# Copy the handler script
COPY run.sh /run.sh
RUN chmod +x /run.sh

# Default command
CMD ["/run.sh"]