# Multi-stage Docker build for Android APK generation
# This creates a complete Android build environment

FROM ubuntu:22.04 AS android-builder

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Set up environment variables for Android
ENV ANDROID_HOME=/opt/android-sdk
ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV PATH=${PATH}:${ANDROID_HOME}/tools:${ANDROID_HOME}/tools/bin:${ANDROID_HOME}/platform-tools
ENV PATH=${PATH}:${ANDROID_HOME}/cmdline-tools/latest/bin
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Essential build tools
    build-essential \
    git \
    curl \
    wget \
    unzip \
    zip \
    # Java development (Java 17 for Android SDK compatibility)
    openjdk-17-jdk \
    # Python development
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    # Build dependencies
    autoconf \
    libtool \
    pkg-config \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libtinfo5 \
    cmake \
    libffi-dev \
    libssl-dev \
    # Additional dependencies for Android builds
    libc6-dev \
    libstdc++6 \
    libpulse-dev \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Create android-sdk directory
RUN mkdir -p ${ANDROID_HOME} && \
    mkdir -p ${ANDROID_HOME}/cmdline-tools

# Download and install Android Command Line Tools
RUN cd /tmp && \
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-10406996_latest.zip && \
    unzip commandlinetools-linux-10406996_latest.zip && \
    mv cmdline-tools ${ANDROID_HOME}/cmdline-tools/latest && \
    rm commandlinetools-linux-10406996_latest.zip && \
    chmod +x ${ANDROID_HOME}/cmdline-tools/latest/bin/*

# Create licenses directory and accept all licenses
RUN mkdir -p ${ANDROID_HOME}/licenses && \
    echo "24333f8a63b6825ea9c5514f83c2829b004d1fee" > ${ANDROID_HOME}/licenses/android-sdk-license && \
    echo "84831b9409646a918e30573bab4c9c91346d8abd" > ${ANDROID_HOME}/licenses/android-sdk-preview-license && \
    echo "d975f751698a77b662f1254ddbeed3901e976f5a" > ${ANDROID_HOME}/licenses/intel-android-extra-license

# Install Android SDK components with proper error handling
RUN ${ANDROID_HOME}/cmdline-tools/latest/bin/sdkmanager --update && \
    ${ANDROID_HOME}/cmdline-tools/latest/bin/sdkmanager \
    "platform-tools" \
    "platforms;android-31" \
    "platforms;android-21" \
    "build-tools;31.0.0" \
    "ndk;25.2.9519653" \
    "cmake;3.22.1"

# Set NDK environment
ENV ANDROID_NDK_HOME=${ANDROID_HOME}/ndk/25.2.9519653
ENV PATH=${PATH}:${ANDROID_NDK_HOME}

# Create a non-root user for building
RUN useradd -m -s /bin/bash builder && \
    chown -R builder:builder ${ANDROID_HOME}

# Switch to builder user
USER builder
WORKDIR /home/builder

# Create virtual environment and install Python dependencies
RUN python3 -m venv /home/builder/buildenv && \
    /home/builder/buildenv/bin/pip install --upgrade pip

# Install buildozer and dependencies in virtual environment
RUN /home/builder/buildenv/bin/pip install \
    buildozer \
    cython \
    kivy \
    kivymd \
    plyer

# Set environment to use virtual environment
ENV PATH="/home/builder/buildenv/bin:${PATH}"

# Set working directory for the app
WORKDIR /app

# Copy project files (this will be done at build time)
COPY --chown=builder:builder . /app/

# Install project requirements
RUN pip install -r requirements.txt

# Create build script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🚀 Starting Android build in Docker..."\n\
echo "📋 Environment check:"\n\
echo "  Java: $(java -version 2>&1 | head -1)"\n\
echo "  Python: $(python --version)"\n\
echo "  Buildozer: $(buildozer --version)"\n\
echo "  Android SDK: ${ANDROID_HOME}"\n\
echo "  Android NDK: ${ANDROID_NDK_HOME}"\n\
echo ""\n\
echo "🧹 Cleaning previous builds..."\n\
rm -rf .buildozer bin\n\
echo ""\n\
echo "🏗️ Building APK (this may take 10-15 minutes)..."\n\
buildozer android debug\n\
echo ""\n\
echo "✅ Build completed!"\n\
if [ -d "bin" ] && [ -n "$(ls bin/*.apk 2>/dev/null)" ]; then\n\
    echo "📱 APK files generated:"\n\
    ls -la bin/*.apk\n\
    echo ""\n\
    for apk in bin/*.apk; do\n\
        echo "📊 Details for $apk:"\n\
        echo "   Size: $(du -h "$apk" | cut -f1)"\n\
        echo "   Type: $(file "$apk")"\n\
    done\n\
else\n\
    echo "❌ No APK files found!"\n\
    exit 1\n\
fi\n\
' > /app/docker_build.sh && chmod +x /app/docker_build.sh

# Default command
CMD ["/app/docker_build.sh"]