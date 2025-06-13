import subprocess
import os


GITHUB_REPO_URL = "git@github.com:genuinegaurav/repo_to_clone.git"
PROJECT_DIR = "repo_to_clone"
JAR_PATH = os.path.join(PROJECT_DIR, "build", "libs", "project.jar")
JAVA_PORT = 8080


def clone_repo():
    """Clones the GitHub repository."""
    print(f"Attempting to clone {GITHUB_REPO_URL}...")
    if os.path.exists(PROJECT_DIR):
        print(f"Directory {PROJECT_DIR} already exists. Skipping clone.")
        return
    try:
        subprocess.run(["git", "clone", GITHUB_REPO_URL], check=True)
        print("Repository cloned successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e}")
        exit(1)


def start_java_app():
    """Starts the Java application."""
    print(f"Attempting to start Java application from {JAR_PATH} on port {JAVA_PORT}...")
    if not os.path.exists(JAR_PATH):
        print(f"Error: JAR file not found at {JAR_PATH}. Please ensure the repository is cloned and the path is correct.")
        exit(1)
    try:
       
        process = subprocess.Popen(["java", "-jar", JAR_PATH])
        print(f"Java application started with PID: {process.pid}")
        print(f"Assuming Java application is now listening on port {JAVA_PORT}. You may need to verify this manually.")
    except FileNotFoundError:
        print("Error: 'java' command not found. Please ensure Java is installed and in your PATH.")
        exit(1)
    except Exception as e:
        print(f"Error starting Java application: {e}")
        exit(1)


if __name__ == "__main__":
    clone_repo()
    start_java_app() 