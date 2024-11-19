FROM python:3.11.9

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app

# Install any needed packages specified in requirements.txt
# RUN apt-get update && apt-get install libgl1  -y
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Make port 12030 available to the world outside this container
EXPOSE 12030

CMD ["python", "rest_server.py"]
