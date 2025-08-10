FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install -e .

# Set Python to run in unbuffered mode to see logs immediately
ENV PYTHONUNBUFFERED=1

EXPOSE 10001

# Run the main module directly now that we have proper logging
CMD ["python", "-m", "wingetupdatesinstaller.main"]
