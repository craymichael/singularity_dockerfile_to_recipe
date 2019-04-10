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
import textwrap
import os

if __name__ == '__main__':
    # Create and add script args
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Dockerfile to recipe conversion',
        epilog=textwrap.dedent('''\
        Examples:
            ./{script} ubuntu.Dockerfile > ubuntu.recipe
            ./{script} --arg CUDA 9.0 --arg TF_PACKAGE tf-nightly-gpu \\
                tensorflow.Dockerfile > tensorflow.recipe
        '''.format(script=__file__))
    )
    parser.add_argument('input_file', help='The input dockerfile')
    parser.add_argument('--arg', '-a', action='append', nargs=2,
                        metavar=('ARG_NAME', 'ARG_VAL'),
                        help='An ARG found in the Dockerfile. Can be specified '
                             'multiple times for multiple Docker ARGs.')
    # Parse the args
    args = parser.parse_args()
    custom_args = dict(args.arg or '')

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
    reg_var = regex.compile(pattern)

    reg_esc = regex.compile(r'(?:[^\\]|^)\\$')

    # Dockerfile args start with this string:
    arg_str = 'ARG '
    shell_str = 'SHELL '  # Ignore these lines (naive)


    def run_subprocess(cmd, env=None, shell=False, executable=None, cwd=None):
        output, _ = subprocess.Popen(cmd, env=env, shell=shell,
                                     executable=executable, cwd=cwd,
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
        for match in reg_var.finditer(string):
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


    skip_next = False  # Temp var to skip continued lines (with '\\')
    append_next = False  # Temp var to append lines (after '\\')
    appended = ''  # Appended line
    for line_orig in text.splitlines():
        if skip_next:
            skip_next = reg_esc.search(line_orig.rstrip()) is not None
            continue
        line = line_orig.lstrip()

        if not append_next:
            if line[:len(shell_str)].upper().startswith(shell_str):
                skip_next = reg_esc.search(line_orig.rstrip()) is not None
                continue  # Ignore shell lines

            if not line[:len(arg_str)].upper().startswith(arg_str):
                # Perform substitution if needed (not an ARG line)
                line_orig = bash_substitute(line_orig)
                filt_lines.append(line_orig)
                continue

        # Grab the docker argument (this is an ARG line)
        line_rstrip = line.rstrip()
        append_next = reg_esc.search(line_rstrip) is not None
        if append_next:
            appended += line_rstrip[:-1]
            continue  # Grab output
        else:
            line = appended + line
            appended = ''
        d_arg = line[len(arg_str):].strip().split('=', 1)
        if len(d_arg) == 1:
            continue  # ARG redeclared, likely after FROM statement. Ignore

        d_arg, d_arg_val = d_arg  # Otherwise expand
        # Perform substitution if needed
        d_arg_val = bash_substitute(d_arg_val)
        # Update env variables
        if d_arg in custom_args:
            env_vars[d_arg] = custom_args[d_arg]
        else:
            env_vars[d_arg] = d_arg_val

    out_file = args.input_file + '_filtered'
    if os.path.exists(out_file):  # Naive temporary file
        raise OSError('File already exists: {}'.format(out_file))

    with open(out_file, 'w') as f:
        f.write('\n'.join(filt_lines))

    # Run spython command in same directory as input file (in case it's looking
    # for Docker-specified COPY files
    print(run_subprocess(['spython', 'recipe', os.path.abspath(out_file)],
                         cwd=os.path.dirname(args.input_file)))

    os.remove(out_file)  # Remove temporary file
