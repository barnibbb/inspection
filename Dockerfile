###Setup base
#
#Base image can be tricky. In my oppinion you should only use a few base images. Complex ones with 
#everything usually have special use cases, an in my experience they take more time to understand, 
#than building one from the ground up.
#The base iamges I suggest you to use:
#- ubuntu: https://hub.docker.com/_/ubuntu
#- osrf/ros:version-desktop-full: https://hub.docker.com/r/osrf/ros
#- nvidia/cuda: https://hub.docker.com/r/nvidia/cuda
#
#We are mostly not space constrained so a little bigger image with everything is usually better,
#than a stripped down version.

FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04
#this is a small but basic utility, missing from osrf/ros. It is not trivial to know that this is
#missing when an error occurs, so I suggest installing it just to bes sure.
RUN apt-get update && apt-get install -y netbase
#set shell 
SHELL ["/bin/bash", "-c"]
#set colors
ENV BUILDKIT_COLORS=run=green:warning=yellow:error=red:cancel=cyan
#start with root user
USER root

###Create new user
#
#Creating a user inside the container, so we won't work as root.
#Setting all setting all the groups and stuff.
#
###

#expect build-time argument
ARG HOST_USER_GROUP_ARG
#create group appuser with id 999
#create group hostgroup with ID from host. This is needed so appuser can manipulate the host files without sudo.
#create appuser user with id 999 with home; bash as shell; and in the appuser group
#change password of appuser to admin so that we can sudo inside the container
#add appuser to sudo, hostgroup and all default groups
#copy default bashrc and add ROS sourcing
RUN groupadd -g 999 appuser && \
    groupadd -g $HOST_USER_GROUP_ARG hostgroup && \
    useradd --create-home --shell /bin/bash -u 999 -g appuser appuser && \
    echo 'appuser:admin' | chpasswd && \
    usermod -aG sudo,hostgroup,plugdev,video,adm,cdrom,dip,dialout appuser && \
    cp /etc/skel/.bashrc /home/appuser/ 

###Install the project
#
#If you install multiple project, you should follow the same 
#footprint for each:
#- dependencies
#- pre install steps
#- install
#- post install steps
#
###

# Basic dependencies for everything
USER root
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y \
    acl \
    build-essential \
    curl \    
    gdb \ 
    git \
    lsb-release \
    netbase \
    sudo \
    tmux \
    udev \
    wget \
    && rm -rf /var/lib/apt/lists/* 


# Basic dependencies for everything
USER root
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y \
    ca-certificates \ 
    curl \
    ffmpeg \
    git \
    libgl1-mesa-dri \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ninja-build \
    python3-pip \
    python-is-python3 \
    wget \
    && rm -rf /var/lib/apt/lists/* 


# Install nerfstudio
# USER appuser
# RUN pip install --no-cache-dir nerfstudio

# Install gsplat
# USER appuser
# RUN pip install --no-cache-dir --upgrade gsplat


# Colmap dependencies
USER root
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y \
    build-essential \
    cmake \
    gcc-10 \
    g++-10 \
    git \
    libboost-graph-dev \
    libboost-program-options-dev \
    libboost-system-dev \
    libceres-dev \
    libcgal-dev \
    libcurl4-openssl-dev \
    libeigen3-dev \
    libflann-dev \
    libfreeimage-dev \
    libglew-dev \
    libgmock-dev \
    libgoogle-glog-dev \
    libgtest-dev \
    libmetis-dev \
    libmkl-full-dev \
    libopenimageio-dev \
    libqt6opengl6-dev \
    libqt6openglwidgets6 \
    libqt6svg6-dev \
    libsqlite3-dev \
    libssl-dev \
    libsuitesparse-dev \
    ninja-build \
    openimageio-tools \
    qt6-base-dev \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/include/opencv4


# Colmap Ubuntu 22.04 issue
ENV CC=/usr/bin/gcc-10
ENV CXX=/usr/bin/g++-10
ENV CUDAHOSTCXX=/usr/bin/g++-10



# Install colmap
ARG CUDA_ARCHITECTURES=61
# install colmap
USER appuser
RUN cd /home/appuser && \
    git clone https://github.com/colmap/colmap.git && \
    cd colmap && \
    git checkout tags/3.12.6 && \
    mkdir build && \
    cd build && \
    cmake .. -GNinja -DCMAKE_CUDA_ARCHITECTURES=${CUDA_ARCHITECTURES} && \
    ninja -j$(nproc)

USER root
RUN cd /home/appuser/colmap/build && \
    ninja install

# Pyhton dependencies
USER root
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

USER appuser 
RUN python -m pip install imagehash pillow tqdm open3d scipy open3d pandas PyYAML numpy==1.26.4


# Install torch and torchvision
USER appuser
RUN python -m pip install --no-cache-dir \
    torch==2.4.0 \
    torchvision==0.19.0 \
    torchaudio==2.4.0 \
    --index-url https://download.pytorch.org/whl/cu124

# Install gsplat
USER appuser
RUN python -m pip install --no-cache-dir rich
RUN python -m pip install --no-cache-dir \
    gsplat==1.3.0+pt24cu124 \
    --extra-index-url https://docs.gsplat.studio/whl/pt24cu124

# Clone gsplat for examples
USER appuser
RUN cd /home/appuser && \
    git clone --depth 1 --branch v1.3.0 \
    https://github.com/nerfstudio-project/gsplat.git

    

USER appuser
RUN git clone https://github.com/rmbrualla/pycolmap.git /home/appuser/pycolmap \
    && cd /home/appuser/pycolmap \
    && git checkout cc7ea4b7301720ac29287dbe450952511b32125e \
    && python -m pip install -v . \
    && python -c "import pycolmap; print('pycolmap:', pycolmap.__file__); print('SceneManager:', hasattr(pycolmap, 'SceneManager'))"



# Regular PyPI dependencies
USER appuser
RUN python -m pip install --no-cache-dir \
    viser \
    "imageio[ffmpeg]" \
    "numpy<2.0.0" \
    scikit-learn \
    tqdm \
    "torchmetrics[image]" \
    opencv-python \
    "tyro>=0.8.8" \
    Pillow \
    tensorboard \
    tensorly \
    pyyaml \
    matplotlib \
    splines

# Git dependencies separately
USER appuser
RUN python -m pip install --no-cache-dir nerfview

# CUDA extensions
USER appuser
RUN python -m pip install --no-cache-dir \
    "git+https://github.com/rahul-goel/fused-ssim@328dc9836f513d00c4b5bc38fe30478b4435cbb5"

USER appuser
RUN python -m pip install --no-cache-dir \
    "git+https://github.com/harry7557558/fused-bilagrid@90f9788e57d3545e3a033c1038bb9986549632fe"


ENV PYTHONPATH=/home/appuser/pycolmap:$PYTHONPATH

