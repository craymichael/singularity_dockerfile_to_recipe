# singularity_utils
Simple utilities for working singularity and docker

Dockerfile to recipe:
```bash
python dockerfile_to_recipe.py tensorflow.Dockerfile > tensorflow.recipe
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

### Internal/dev docs:
Build a test image (as root):
```bash
/opt/singularity/3.1.0/bin/singularity build tensorflow_1.13.1-gpu-py3_test.simg /home/zjc2920/singularity/recipes/tensorflow_1.13.1-gpu-py3_test
```

Convert Dockerfile to a singularity recipe:
```bash
spython recipe singularity/recipes/tensorflow_gpu.Dockerfile
```

### Nu.AI Server (kgcoe-nanolab.main.ad.rit.edu)
Build a recipe:
```bash
/opt/singularity/3.1.0/bin/singularity build <output>.simg <input_recipe>
```
