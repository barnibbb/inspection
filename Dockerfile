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

FROM nvidia/cuda:11.3.1-cudnn8-devel-ubuntu20.04
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

#basic dependencies for everything
USER root
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive\
    apt-get install -y\
    netbase\
    git\
    build-essential\    
    wget\
    curl\
    gdb\
    lsb-release\
    sudo

# colmap dependencies
USER root
RUN apt-get update && \ 
    DEBIAN_FRONTEND=noninteractive\
    apt-get install -y\
    git \
    cmake \
    ninja-build \
    build-essential \
    libboost-program-options-dev \
    libboost-graph-dev \
    libboost-system-dev \
    libeigen3-dev \
    libflann-dev \
    libfreeimage-dev \
    libmetis-dev \
    libgoogle-glog-dev \
    libgtest-dev \
    libgmock-dev \
    libsqlite3-dev \
    libglew-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libcgal-dev \
    python3 \
    python3-pip \
    python3-venv \
    exiftool \
    libexempi-dev
    
# visualization
USER root
RUN apt-get update && \ 
    DEBIAN_FRONTEND=noninteractive\
    apt-get install -y\
    libgl1-mesa-glx \
    libx11-6 \
    libglu1-mesa \
    python3-tk


# install ceres
USER appuser
RUN cd /home/appuser && \
    git clone https://github.com/ceres-solver/ceres-solver.git && \
    cd ceres-solver && \
    git checkout tags/2.1.0 && \
    mkdir build && \
    cd build && \
    cmake .. -DBUILD_TESTING=OFF -DBUILD_EXAMPLES=OFF -DCXX_STANDARD=17 -DUSE_CUDA=1 && \
    make -j$(nproc)
USER root
RUN cd /home/appuser/ceres-solver/build && \
    make install

USER appuser
RUN python3 -m pip install pandas

ARG CUDA_ARCHITECTURES=native

# install colmap
USER appuser
RUN cd /home/appuser && \
    git clone https://github.com/colmap/colmap.git && \
    cd colmap && \
    git checkout tags/3.11.1 && \
    mkdir build && \
    cd build && \
    cmake .. -GNinja -DCMAKE_CUDA_ARCHITECTURES=${CUDA_ARCHITECTURES} && \
    ninja -j$(nproc)

USER root
RUN cd /home/appuser/colmap/build && \
    ninja install

# install image filtering dependencies
USER appuser
RUN pip install imagehash pillow tqdm open3d scipy open3d



