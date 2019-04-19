# singularity_utils
Simple utilities for working singularity and docker. `spython` does not work
with Docker `ARG`s, so this script strips those and uses `bash` for string
substitution often found in Dockerfiles. These `ARG`s can be passed in at
recipe creation time to redefine values.

Dockerfile to recipe:
```bash
python dockerfile_to_recipe.py tensorflow.Dockerfile > tensorflow.recipe
# With ARGs:
python dockerfile_to_recipe.py --arg CUDA 9.0 --arg TF_PACKAGE tf-nightly-gpu tensorflow.Dockerfile > tensorflow.recipe
```

### Requirements:
- Linux with bash support (/bin/bash)
- [spython](https://vsoch.github.io/singularity-cli/install)
```bash
git clone https://www.github.com/singularityhub/singularity-cli.git
cd singularity-cli
python3 setup.py install
```
- Python pypi packages (install with pip3):
  - future
  - regex

### Container Building Example:
Build a test image:
```bash
singularity build tensorflow_gpu.simg tensorflow_gpu.recipe
```
