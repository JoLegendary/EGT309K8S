# Use Python 3.12 base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /

# Copy the script and the test.txt file into the container's /app directory
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8080
ENTRYPOINT ["python", "Test.py"]