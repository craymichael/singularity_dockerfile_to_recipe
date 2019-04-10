from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# noinspection PyCompatibility
from builtins import (ascii, bytes, chr, dict, filter, hex, input,
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import subprocess
import regex
import argparse
import os

if __name__ == '__main__':
    # Create and add script args
    parser = argparse.ArgumentParser(
        description='dockerfile to recipe conversion')
    parser.add_argument('input_file', help='The input dockerfile')
    # Parse the args
    args = parser.parse_args()

    # Open provided file
    with open(args.input_file, 'r') as f:
        text = f.read()

    # Pattern for grabbing groups of "${...}" format strings recursively
    pattern = (r'('  # Capturing group
               r'\$\{'  # Match "${"
               r'(?>'  # Atomic grouping
               r'[^\$\{\}]+'  # 1 or more of not '$', '{', or '}'
               r'|(?R)'  # OR sub-pattern contains regex (recurse)
               r')*'  # 0 or more of positive lookahead matched
               r'\}'  # Terminating "}"
               r')')  # End capturing group
    reg = regex.compile(pattern)

    # Dockerfile args start with this string:
    arg_str = 'ARG '
    shell_str = 'SHELL '  # Ignore these lines (naive)


    def run_subprocess(cmd, env=None, shell=False, executable=None):
        output, _ = subprocess.Popen(cmd, env=env, shell=shell,
                                     executable=executable,
                                     stdout=subprocess.PIPE).communicate()
        return output.decode()


    bash_path = run_subprocess(['which', 'bash']).strip()
    if not bash_path:
        raise OSError('`bash` not found! Exiting.')

    filt_lines = []  # Filtered lines (args removed)
    env_vars = {}  # Environmental variables (to populate)


    def bash_substitute(string):
        new_string = ''
        idx = 0
        for match in reg.finditer(string):
            # Grab captured string
            matched_str = match.captures()
            if len(match.captures()) != 1:
                raise ValueError('Matched string does not capture a single '
                                 'substring: {}'.format(matched_str))
            matched_str = matched_str[0]
            # Grab string matched indices
            start, finish = match.span()

            subst_str = run_subprocess('echo {}'.format(matched_str),
                                       env=env_vars, shell=True,
                                       executable=bash_path).strip()
            # Update the new string with up to start and replacement
            new_string += string[idx:start]
            new_string += subst_str
            # Update current running index
            idx = finish
        # Append remainder of string
        new_string += string[idx:]
        return new_string


    for line_orig in text.splitlines():
        line = line_orig.lstrip()

        if line[:len(shell_str)].upper().startswith(shell_str):
            continue  # Ignore shell lines (1-line ignore is Naive)

        if not line[:len(arg_str)].upper().startswith(arg_str):
            # Perform substitution if needed
            line_orig = bash_substitute(line_orig)
            filt_lines.append(line_orig)
            continue

        # Grab the docker argument
        d_arg = line[len(arg_str):].strip().split('=', 1)
        if len(d_arg) == 1:
            continue  # ARG redeclared, likely after FROM statement. Ignore

        d_arg, d_arg_val = d_arg  # Otherwise expand
        # Perform substitution if needed
        d_arg_val = bash_substitute(d_arg_val)
        # Update env variables
        env_vars[d_arg] = d_arg_val

    out_file = args.input_file + '_filtered'
    if os.path.exists(out_file):  # Naive temporary file
        raise OSError('File already exists: {}'.format(out_file))

    with open(out_file, 'w') as f:
        f.write('\n'.join(filt_lines))

    print(run_subprocess(['spython', 'recipe', out_file]))

    os.remove(out_file)  # Remove temporary file
