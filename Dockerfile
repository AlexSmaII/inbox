# Use Debian 12 as a base
FROM python:3.13-slim-bookworm AS backend

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install Microsoft tooling including ODBC Driver 18
# to communicate with Microsoft SQL Server databases
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && curl -fsSL -o /tmp/prod.deb \
      https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
 && dpkg -i /tmp/prod.deb \
 && rm /tmp/prod.deb \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc \
 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.11.23 /uv /uvx /bin/

COPY backend /app

WORKDIR /app

RUN uv sync --locked

COPY run_docker.sh /run_docker.sh
RUN chmod +x /run_docker.sh

EXPOSE 8080
CMD ["/run_docker.sh"]