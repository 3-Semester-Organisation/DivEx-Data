# Use an official Python runtime as a base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any dependencies (if you have a requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# If no dependencies are required, you can skip the above RUN step.

# Make the script executable
RUN chmod +x your_script.py

# Set the default command to run the script
CMD ["python", "your_script.py"]
