FROM python:3.11.9

ENV HTTP_PROXY=http://10.98.12.18:7890
ENV HTTPS_PROXY=http://10.98.12.18:7890
ENV http_proxy=http://10.98.12.18:7890
ENV https_proxy=http://10.98.12.18:7890
ENV NO_PROXY=localhost,127.0.0.1
ENV no_proxy=localhost,127.0.0.1

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app

# Install any needed packages specified in requirements.txt
# RUN apt-get update && apt-get install libgl1  -y
RUN pip install --no-cache-dir -r requirements.txt

# Make port 12030 available to the world outside this container
EXPOSE 12030

# Unset the proxy
RUN unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy NO_PROXY no_proxy

CMD ["python", "rest_server.py"]