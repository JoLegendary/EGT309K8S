import sys
from streamlit.web import cli as stcli
from streamlit import runtime
import platform
import time
import os

streamlit_args = ["streamlit", "run", "src/Get_Started.py"]






input = None
match(platform.system()):
    case "Windows":
        import msvcrt
        def input(prompt="", timeout=-1, timeIncrement=0.51, *, raise_err=True):
            while msvcrt.kbhit(): msvcrt.getwche()
            startPos = None
            sys.stdout.write(prompt)
            sys.stdout.flush()
            endtime = time.monotonic() + timeout
            result = ""
            while (curTime:=time.monotonic()) < endtime or timeout == -1:
                if not msvcrt.kbhit():
                    time.sleep(0.04) # just to yield to other processes/threads
                    continue

                in_read = msvcrt.getwch() #XXX can it block on multibyte characters?
                match(in_read):
                    case '\b':
                        in_read = ""
                        if len(result) > 0:
                            if result[-1] == "\n":	sys.stdout.write(f"\033M{(prompt+result).split("\n")[-2]}")
                            else:			sys.stdout.write("\b \b")
                            result = result[:-1]

                result += in_read
                sys.stdout.write(in_read)
                sys.stdout.flush()
                if result[-1:] == '\r': # One check is faster than checking len then last char. *its shorter too*
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    break

                endtime = min(endtime + timeIncrement, curTime + timeout)

            if result[-1:] == '\r': return result[:-1]
            ze_timeout = TimeoutError(f"User prompt has timed out. Entered: '{result}'")
            ze_timeout.value = result
            if raise_err: raise ze_timeout
            return ze_timeout
    case _:
        import termios, select, tty
        def input(prompt, timeout):
            sys.stdout.write(prompt)
            sys.stdout.flush()

            settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setraw(sys.stdin)
                output, _, _ = select.select([sys.stdin], [], [], timeout)
                if output:
                    return sys.stdin.read().rstrip()
                else:
                    raise TimeoutError("Timeout occurred.")
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)


if __name__ == '__main__':
    if runtime.exists():
        sys.stdout.write("There is already an active runtime!\n")
        sys.stdout.flush()
        sys.exit(0)
    else:
        sys.stdout.write("Running server...\n")
        sys.stdout.flush()
        default_mode = os.environ.get("STREAMLIT_APP_DEFAULT_MODE", 0)
        mode_names = {
            0: "Local",
            1: "Production",
        }
        if default_mode not in mode_names:
            sys.stdout.write("Environment Variable 'STREAMLIT_APP_DEFAULT_MODE' is invalid. Defaulting to default value.\n")
            sys.stdout.flush()
            default_mode = 0
        sys.stdout.write(f"The server will automatically run in '{mode_names[default_mode]}' mode if no input is given in 5 seconds.\n")
        sys.stdout.flush()
        try:
            while True:
                mode = input("Would you like to publish the server address? (y/n)", 5)
                yes_inputs = ["y","yes"]
                no_inputs = ["n","no"]
                default_input = [""]
                if mode.lower() not in yes_inputs + no_inputs + default_input:
                    sys.stdout.write(f"Invalid input '{mode}'. Accepted inputs: ({"/".join(yes_inputs + no_inputs)})\n")
                    sys.stdout.flush()
                    continue
                if mode in default_input: raise TimeoutError()
                mode = (mode in yes_inputs) * 1 + (mode in no_inputs) * 0
                break
        except TimeoutError:
            sys.stdout.write("Defaulting to default mode.\n")
            sys.stdout.flush()
            mode = default_mode

        sys.stdout.write(f"Starting server in {mode_names[mode]} mode.\n")
        sys.stdout.flush()

        sys.argv = streamlit_args
        match(mode):
            case 0:
                sys.argv += ["--server.address=localhost", "--browser.serverAddress=localhost"]
            case 1:
                sys.argv += [] # cant really unset values for some reason
        sys.exit(stcli.main())
