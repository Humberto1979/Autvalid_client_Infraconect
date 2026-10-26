# syntax=docker/dockerfile:1.7

# ---------- build ----------
# F2 Dependencies: base fixada (idealmente por digest), nunca `latest`.
FROM python:3.13-slim AS build

WORKDIR /app

# Copia apenas o manifest de deps para aproveitar cache de camadas.
COPY src/requirements.txt ./

# DevSecOps: --no-cache-dir evita cache do pip na camada final.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- runtime ----------
# F2/F10: mesma base em dev e prod; imagem final enxuta (sem toolchain).
FROM python:3.13-slim AS runtime

# DevSecOps: usuario nao-root com UID/GID fixo.
RUN groupadd -g 1000 appgroup \
 && useradd -u 1000 -g appgroup -m -s /bin/false appuser

WORKDIR /app

# Dependencias do estagio de build, ja com chown.
COPY --from=build --chown=appuser:appgroup /install /usr/local

# DevSecOps: runtime minimo. O aplicativo nao instala pacotes em runtime;
# pip (e suas copias vendidas antigas: msgpack, urllib3) e setuptools nao
# sao necessarios e poluem o inventario do scanner de vulnerabilidades.
RUN python -m pip uninstall --yes pip setuptools \
 && rm -rf /usr/local/lib/python3.13/site-packages/pip* \
           /usr/local/lib/python3.13/site-packages/setuptools* \
           /usr/local/lib/python3.13/site-packages/pkg_resources \
           /usr/local/lib/python3.13/_distutils_hack \
           /usr/local/bin/pip*

# F1/F5: codigo da aplicacao entra imutavel no build.
COPY --chown=appuser:appgroup src/ ./

# F3 Config: ENV apenas para default inofensivo.
ENV APP_PORT=5000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# DevSecOps: drop de privilegios antes do CMD.
USER 1000:1000

# F7 Port binding: porta declarada; roteamento externo e do orquestrador.
# EXPOSE e apenas documentacao: o bind real vem de APP_PORT (gunicorn_conf).
# Se mudar APP_PORT, ajustar Compose/Service junto.
EXPOSE 5000

# F9 Disposability: Gunicorn como PID 1, graceful-timeout trata SIGTERM.
# F11 Logs: Gunicorn escreve em stdout/stderr por padrao.
CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]

# HEALTHCHECK nativo (Docker puro; no K8s prefira probes do Deployment).
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('APP_PORT','5000')+'/healthz',timeout=2).read()"