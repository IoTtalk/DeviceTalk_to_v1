FROM python:3.7.10-slim

RUN apt update && \
# Install build dependencies
    apt install -y --no-install-recommends python3-dev default-libmysqlclient-dev build-essential zip && \
    pip install --no-cache-dir -U pip
    
WORKDIR /devicetalk

COPY . /devicetalk

# Install requirements
RUN pip install --no-cache-dir -r /devicetalk/requirements.txt

# Remove build dependencies, unused packages and the packages index
# Ref: https://unix.stackexchange.com/questions/217369/clear-apt-get-list
RUN apt autoremove -y && \
    rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash"]
