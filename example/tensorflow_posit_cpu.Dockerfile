# Copyright 2018 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
#
# Please refer to the TensorFlow dockerfiles documentation
# for more information.
# https://github.com/tensorflow/tensorflow/tree/master/tensorflow/tools/dockerfiles

ARG UBUNTU_VERSION=16.04

ARG ARCH=
FROM ubuntu:${UBUNTU_VERSION} as base
# ARCH is specified again because the FROM directive resets ARGs
# (but their default value is retained if set previously)
ARG ARCH

# Needed for string substitution
SHELL ["/bin/bash", "-c"]
# Pick up some TF, universal, and bazel dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libfreetype6-dev \
        libhdf5-serial-dev \
        libzmq3-dev \
        pkg-config \
        software-properties-common \
        unzip \
        git \
        pkg-config \
        zip \
        g++ \
        zlib1g-dev \
        cmake \
        unzip \
        vim \
        nano

ARG _PY_SUFFIX=3.6
ARG PYTHON=python${_PY_SUFFIX}
ARG PIP=pip${_PY_SUFFIX}

# See http://bugs.python.org/issue19846
ENV LANG C.UTF-8

# Install universal
RUN git clone https://github.com/stillwater-sc/universal \
    && mkdir universal/build \
    && cd universal/build/ \
    && cmake .. \
    && make -j 4 \
    && sed -i -e 's/universal\/universal/universal/g' cmake_install.cmake \
    && make install \
    && cd ../.. \
    && rm -rf universal/

RUN add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    ${PYTHON} \
    ${PYTHON}-dev \
    && curl https://bootstrap.pypa.io/get-pip.py | ${PYTHON} \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Pip/setuptools and https://kgcoe-git.rit.edu/sf3052/Posit-Project-Code
RUN if [ "$(${PYTHON} -c "import sys;print(sys.byteorder == 'little')")" = "True" ] ; then \
    EXTRA="grpcio"; else EXTRA=""; fi \
    && ${PIP} --no-cache-dir install --upgrade \
    pip \
    setuptools \
    absl-py \
    astor \
    gast \
    six \
    protobuf \
    tensorboard \
    termcolor \
    wheel \
    mock \
    cython \
    matplotlib \
    scipy \
    h5py \
    softposit \
    graphviz \
    pydot \
    future \
    $EXTRA \
    && pip --no-cache-dir install --upgrade --no-deps \
    keras_applications \
    keras_preprocessing \
    keras

# NumPy-Posit
RUN pip uninstall -y numpy \
    && git clone https://github.com/xman/numpy-posit.git \
    && cd numpy-posit/ \
    && git submodule update --init --recursive \
    && ${PYTHON} setup.py install \
    && cd .. \
    && rm -rf numpy-posit/

# Install bazel
ARG BAZEL_VERSION=0.17.2
ARG _BAZEL_EXEC=bazel-${BAZEL_VERSION}-installer-linux-x86_64.sh
RUN curl -L \
    https://github.com/bazelbuild/bazel/releases/download/${BAZEL_VERSION}/${_BAZEL_EXEC} \
    > ${_BAZEL_EXEC} \
    && chmod +x ${_BAZEL_EXEC} \
    && ./${_BAZEL_EXEC} \
    && rm ${_BAZEL_EXEC}

# Some TF tools expect a "python" binary
RUN ln -s $(which ${PYTHON}) /usr/local/bin/python

# Install TensorFlow
ARG TENSORFLOW_VERSION=1.11.0
# https://gist.github.com/PatWie/0c915d5be59a518f934392219ca65c3d
RUN git clone https://github.com/xman/tensorflow.git \
    && cd tensorflow/ \
    && git checkout posit-${TENSORFLOW_VERSION} \
    && export PYTHON_BIN_PATH=$(which ${PYTHON}) \
    && export PYTHON_LIB_PATH="$($PYTHON_BIN_PATH -c 'import site; print(site.getsitepackages()[0])')" \
    && export TF_NEED_GCP=0 \
    && export TF_NEED_CUDA=0 \
    && export TF_NEED_HDFS=0 \
    && export TF_NEED_OPENCL=0 \
    && export TF_NEED_JEMALLOC=1 \
    && export TF_ENABLE_XLA=0 \
    && export TF_NEED_VERBS=0 \
    && export TF_NEED_MKL=0 \
    && export TF_DOWNLOAD_MKL=0 \
    && export TF_NEED_AWS=0 \
    && export TF_NEED_MPI=0 \
    && export TF_NEED_GDR=0 \
    && export TF_NEED_S3=0 \
    && export TF_NEED_OPENCL_SYCL=0 \
    && export TF_SET_ANDROID_WORKSPACE=0 \
    && export TF_NEED_COMPUTECPP=0 \
    && export GCC_HOST_COMPILER_PATH=$(which gcc) \
    && export CC_OPT_FLAGS="-march=native" \
    && export TF_SET_ANDROID_WORKSPACE=0 \
    && export TF_NEED_KAFKA=0 \
    && export TF_NEED_TENSORRT=0 \
    && export TF_NEED_NGRAPH=0 \
    && export TF_DOWNLOAD_CLANG=0 \
    && export CC_OPT_FLAGS="-march=native" \
    && ./configure \
    && TMP=/tmp bazel build --config=opt //tensorflow/tools/pip_package:build_pip_package --verbose_failures \
    && bazel-bin/tensorflow/tools/pip_package/build_pip_package /tmp/tensorflow_pkg \
    && pip install --no-deps /tmp/tensorflow_pkg/tensorflow-${TENSORFLOW_VERSION}*.whl \
    && cd .. \
    && rm -rf tensorflow/

COPY bashrc /etc/bash.bashrc
RUN chmod a+rwx /etc/bash.bashrc
