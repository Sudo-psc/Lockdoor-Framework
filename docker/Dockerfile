# 1. Base Image
FROM python:3.10-slim-bullseye

# MAINTAINER and LABELS from the original Dockerfile (can be updated later if needed)
MAINTAINER Sofiane Hamlaoui <s0fianehaml40u1@gmail.com> <https://github.com/SofianeHamlaoui>
LABEL org.label-schema.name="sofianehamlaoui/lockdoor"
LABEL org.label-schema.description="Lockdoor Framework : A Penetration Testing framework with Cyber Security Resources - Now with a Python Plugin System"
LABEL org.label-schema.usage="https://github.com/SofianeHamlaoui/Lockdoor-Framework" # Update if this is a fork
LABEL org.label-schema.url="https://lockdoor.sofianehamlaoui.fr/" # Update if this is a fork or new project site
LABEL org.label-schema.docker.cmd="docker run -it --name lockdoor-plugin-framework -p 5000:5000 sofianehamlaoui/lockdoor-plugin-framework" # Example updated cmd

# 2. Environment Variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=src.web_panel:app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# 3. Working Directory
WORKDIR /app

# 4. Copy application code and configuration files
# Copy pyproject.toml and setup.cfg first to leverage Docker layer caching for dependencies
COPY pyproject.toml setup.cfg ./

# 5. Install Python dependencies
# Ensure pip, setuptools, and wheel are up-to-date
RUN pip install --upgrade pip setuptools wheel
# Install dependencies specified in pyproject.toml
RUN pip install . --no-cache-dir

# Copy the rest of the application code
COPY src ./src
COPY plugins ./plugins
COPY run.py .
COPY README.md . # Included as it's good practice
COPY LICENSE .   # Included as it's good practice

# 6. Expose port that Flask will run on (matches FLASK_RUN_PORT)
EXPOSE 5000

# 7. Default command
CMD ["python", "run.py"]
