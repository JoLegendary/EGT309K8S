# Use Python 3.12 base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /

# Copy the script and the test.txt file into the container's /app directory
COPY . .
RUN pip install -r requirements.txt
EXPOSE 6650
# Command to run the script.py
ENTRYPOINT ["python", "-u", "flask_preprocessing.py"]
