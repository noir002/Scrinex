# Pins the exact Python version + stdlib nex/Scrinex run on, regardless of
# whatever Python (or lack of one) is on the host machine. Since nex.py and
# pygit_core.py use only the standard library, this image needs no pip
# install step at all -- it's just Python itself, made portable.
FROM python:3.11-slim

WORKDIR /nex

# The tool's own code (does NOT contain your repo -- that's mounted at runtime)
COPY nex.py pygit_core.py server.py ./
COPY scrinex ./scrinex

EXPOSE 8000

# Default action: run the Scrinex portal against whatever repo is mounted
# at /workspace. Override the command to run `nex` subcommands instead
# (see docker-compose.yml / README for both usages).
CMD ["python3", "server.py", "/workspace", "8000"]