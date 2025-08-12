FROM postgres:17

# Install build tools and server dev headers to build HypoPG
RUN set -eux; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        build-essential \
        git \
        make \
        gcc \
        libc6-dev \
        libssl-dev \
        pkg-config \
        postgresql-server-dev-17 \
        postgresql-contrib;  \
    rm -rf /var/lib/apt/lists/*

# Build and install HypoPG from source
# If a newer tag exists and is needed, adjust the tag below accordingly

RUN set -eux;
RUN git clone --depth 1 https://github.com/HypoPG/hypopg.git /tmp/hypopg;
RUN make -C /tmp/hypopg;
RUN make -C /tmp/hypopg install;
RUN rm -rf /tmp/hypopg

# Default image entrypoint/cmd are kept from postgres base image

