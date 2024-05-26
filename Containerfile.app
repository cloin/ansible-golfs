FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY app/requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install bluez python3-bluez -y

# Copy application files
COPY app/ .

# Expose necessary ports (if any)
EXPOSE 1883

# Command to run the application
CMD ["python3", "main.py"]
