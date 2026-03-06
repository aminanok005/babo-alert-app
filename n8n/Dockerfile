# n8n/Dockerfile
FROM n8nio/n8n:latest

# Set environment variables
ENV N8N_HOST=0.0.0.0
ENV N8N_PORT=5678
ENV NODE_ENV=production

# Copy workflows if they exist
COPY workflows/*.json /home/node/.n8n/workflows/

# Expose port
EXPOSE 5678
