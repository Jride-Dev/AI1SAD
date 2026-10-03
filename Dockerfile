FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=7860

RUN useradd --create-home --uid 1000 user
WORKDIR /home/user/app

COPY --chown=user:user requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user:user app ./app
COPY --chown=user:user providers ./providers
COPY --chown=user:user docs/assets ./docs/assets

RUN mkdir -p data/public data/media_attachments && chown -R user:user data

USER user
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/health', timeout=4)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
