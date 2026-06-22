import os
import sys
import socket
import time
import platform
import subprocess
import webbrowser
from src.Manager import Manager


def is_server_running(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def run_manager() -> None:
    manager = Manager()
    manager.get_args()
    manager.parsing()
    manager.run()
    manager.create_json()


def start() -> None:
    if not os.path.isdir(os.curdir + '/maps'):
        print("Oh oh... you have forgotten to load the maps folder "
              "with the exercises... put it on root? Exiting.")
        exit(0)
    # if not is_server_running('server:app'):
    if not is_server_running(8000):
        print("About to start server...")
        system = platform.system()
        venv_name = ".venv"
        if system == "Windows":
            venv_python = os.path.join(venv_name, "Scripts", "python.exe")
        else:
            venv_python = os.path.join(venv_name, "bin", "python")

        # Check if venv truly exists
        if not os.path.exists(venv_python):
            print(f"Error: Python interpreter not found at {venv_python}")
            exit(1)

        port = 8000
        url = f"http://127.0.0.1:{port}"

        print(f"Server started at port {port}...")
        try:
            # We go directly for subprocess to prevent the broken comm error
            # in Windows
            if system == "Windows":
                subprocess.Popen(
                    ["cmd.exe", "/c", "start", "", venv_python, "-m",
                     "uvicorn", "server:app", "--port", str(port), "--reload"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    shell=True
                )
            else:
                command = f"{venv_python} -m uvicorn server:app "
                f"--port {str(port)} --reload; exec bash"
                subprocess.Popen(
                    # [c for c in command.split(' ')],
                    [
                        "gnome-terminal",
                        "--",
                        "bash",
                        "-c",
                        command],
                    # stdout=subprocess.DEVNULL,
                    # stderr=subprocess.DEVNULL,
                    # stdin=subprocess.DEVNULL,
                    # start_new_session=True
                )
        except Exception as e:
            print(f"Could not start the server: {e}")
            sys.exit(1)

        # A short wait to get the browser
        time.sleep(2)
        print(f"Browser opened at: {url}")
        webbrowser.open(url)
    time.sleep(2)
    run_manager()


if __name__ == "__main__":
    start()
