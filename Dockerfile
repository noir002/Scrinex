# Pins the exact Python version + stdlib nex/Scrinex run on, regardless of
# whatever Python (or lack of one) is on the host machine. Since nex.py and
# pygit_core.py use only the standard library, this image needs no pip
# install step at all -- it's just Python itself, made portable.
FROM python:3.11-slim

WORKDIR /nex

# The tool's own code (does NOT contain your repo -- that's mounted at
# runtime for local/docker-compose use; see docker-compose.yml).
COPY nex.py pygit_core.py server.py nex-portable.zip ./
COPY scrinex ./scrinex

# A small demo repo baked into the image so a registry/hosted deployment
# (GHCR image running on Render, no volume mount available) has something
# to show out of the box, instead of an empty "no repository initialized".
COPY demoRepo /workspace
RUN cd /workspace \
    && python3 /nex/nex.py init \
    && python3 /nex/nex.py add . \
    && python3 /nex/nex.py commit -m "Initial demo commit"

# Run as non-root -- good practice for anything that's actually deployed
# rather than just run locally.
RUN useradd --create-home --shell /usr/sbin/nologin nex \
    && chown -R nex:nex /nex /workspace
USER nex

# NEX_REPO_PATH / PORT are read by server.py when no CLI args are given
# (see server.py) -- Render injects its own $PORT at runtime, which
# overrides this default automatically.
ENV NEX_REPO_PATH=/workspace
ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python3 -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/api/status', timeout=2)" || exit 1

# No CLI args -- picks up NEX_REPO_PATH/PORT from the environment above (or
# whatever Render/docker-compose overrides them with). Override the command
# entirely to run `nex` subcommands instead (see README).
CMD ["python3", "server.py"]
