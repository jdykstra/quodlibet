FROM ubuntu:rolling

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# JWD - Tell Debian package utilities there's no one to talk to.
ENV DEBIAN_FRONTEND noninteractive

# JWD - Workaround to get environment variable to app.
ENV DISPLAY=192.168.221.9:0

# JWD - Install ALSA for audio.
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        alsa-base \
        alsa-utils \
        libsndfile1-dev

ENV ALSA_CARD=hw:0

# JWD - Install python3 and pip3
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3             \
        python-is-python3   \
        python3-pip

# JWD - Install graphics
RUN apt-get install -y --no-install-recommends \
        libx11-6 \
        libxt6 \
        libxfixes3 


# JWD - X utilities just for bringup
RUN apt-get install -y --no-install-recommends \
        x11-apps \
        net-tools \
        iputils-ping \
        telnet

# JWD - Install quodlibet dependencies
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
    python3-gi-cairo \
    libcairo2-dev \
    python3-feedparser \
    python3-musicbrainzngs \
    python3-mutagen \
    python3-gi \
    python3-pyinotify \
    python3-requests \
    gir1.2-gdkpixbuf-2.0 \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    gir1.2-gtk-3.0 \
    python3-bs4 \
    gir1.2-soup-2.4 \
    libmodplug-dev

# jwd - Clean up after apt-get
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# JWD Quiet OpenGL errors.
ENV LIBGL_ALWAYS_INDIRECT=1

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "quodlibet.py"]
