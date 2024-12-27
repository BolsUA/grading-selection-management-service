# Use an official Python runtime as the base image
FROM python:3.9-slim

# Create a non-root user for running the application
RUN addgroup --system appgroup && adduser --system --group appuser

# Set the working directory
WORKDIR /grading

# Copy application source code and requirements
COPY ./app ./app
COPY ./requirements.txt ./
COPY ./wait_for_db.py ./

# Set proper permissions for the non-root user
RUN chown -R appuser:appgroup /grading

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 8003

# Set the default user to the non-root user
USER appuser

# Command to wait for the database to be ready and start the FastAPI app
CMD ["sh", "-c", "python3 wait_for_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8003"]
