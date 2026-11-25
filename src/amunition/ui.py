import sys
import shlex
from rich import print
from rich.console import Console
from . import *
from .api import *

MUNI_METRO: dict[str, str] = {
    "J": "bold bright_white on #c85a00",
    "K": "bold bright_white on #2b7296",
    "L": "bold bright_white on #8d188f",
    "M": "bold bright_white on #007748",
    "N": "bold bright_white on #1e4a7e",
    "T": "bold bright_white on #d50f41",
    "F": "bold bright_white on #e17b10",
    "E": "bold bright_white on #e17b10"
}

help_doc: str = """[white]A([red]muni[/])tion commands:
    [cyan]help[/]: prints this message
    [cyan]exit[/]: exits A([red]muni[/])tion
    [cyan]quit[/]: same as exit
    [cyan]get[/] <op> <routes/stops>: gets that agencies routes/stops
    [cyan]line-get[/] <op> <line number> <stops/name/mode>: gets the info of the line queried
    [cyan]stop-get[/] <op> <stop number>: gets the info of the line queried
    [cyan]search-stops[/] <op> <query>: gets the stops tied to the query
    [cyan]operators[/]: lists valid operators
    [cyan]pager/less/more[/]: turns on pager for next command only
    [cyan]about[/]: credits
    [cyan]search-lines[/] <op> <query>: searches for the route number tied to that query
    [cyan]key[/] <your-key>: sets your 511 key"""

welcome: str = f"""[white]Welcome to A([red]muni[/])tion ({VERSION})!
(Type '[cyan]help[/]' to see commands, '[cyan]about[/]' for credits)"""

about: str = f"""[white]A[/]([red]muni[/])tion is powered by 511.org data, and is not affiliated with the SFMTA, MTC, or any other transit authority.
(c) 2026 goldcoin10 (LICENSE is available at https://raw.githubusercontent.com/goldcoin10/amunition/refs/heads/master/LICENSE)
(you are on version {VERSION})
"""

console = Console()

def sh_511(pager: bool = False) -> None:
    if pager:
        raw = input("pager> ").strip()
    else:
        raw = input("> ").strip()
    if raw == "":
        sh_511()
    else:
        term_arr: list[str] = shlex.split(raw)
        if term_arr[0] == "pager" or term_arr[0] == "less" or term_arr[0] == "more":
            sh_511(True)
        else:
            result = check_command(term_arr)
            if pager == False:
                print(result)
            else:
                with console.pager(): 
                    console.print(result)


def check_command(command: list[str]) -> str:
    len_com: int = len(command)
    ret: str = ""
    
    if command[0] == "help":
        return help_doc
    elif command[0] == "exit" or command[0] == "quit":
        sys.exit(0)
    elif command[0] == "operators":
        for id, name in get_operator_list().items():
            ret = f"{ret}\n{id} {name}"
    elif command[0] == "about":
        return about
    elif command[0] == "get":
        if len_com < 2:
            return "too few arguments"
        elif not api_key:
            return "invalid api key"

        if command[1].upper() in get_operator_list():
            operator_id = command[1].upper()
            operator_name = get_operator_list()[command[1].upper()]
        else:
            return "operator not found"

        if len_com < 3:
            return operator_name
        elif command[2] == "routes":
            for line_num, line_nom, line_frm, line_prv in get_operator_routes(operator_id):
                ret = f"{ret}\n{line_num} {line_nom}"
        elif command[2] == "stops":
            for stop_num, stop_nom, stop_prv in get_operator_stops(operator_id):
                ret = f"{ret}\n{stop_num} {stop_nom}"
        else:
            ret = "wrong syntax"
    elif command[0] == "line-get":
        if len_com < 4:
            return "too few arguments"
        elif not api_key:
            return "invalid api key"

        operator_id = command[1].upper()
        if operator_id not in get_operator_list():
            return "operator not found"

        operator_routes = get_operator_routes(operator_id)
        line_id = command[2]
        valid_lines = {num.upper(): num for num, _, _, _ in operator_routes}
        if line_id.upper() not in valid_lines:
            return "line not found"

        canonical_line_id = valid_lines[line_id.upper()]

        if command[3].strip().lower() == "stops":
            stop_data = get_route_stops(canonical_line_id, operator_id)
            for stop_num, stop_nom, _ in stop_data:
                ret = f"{ret}\n{stop_num} {stop_nom}"
        elif command[3].strip().lower() == "name":
            for num, nom, _, _ in operator_routes:
                if canonical_line_id == num:
                    ret = nom
        elif command[3].strip().lower() == "mode":
            for num, _, mode, _ in operator_routes:
                if canonical_line_id == num:
                    ret = mode
        else:
            return "wrong syntax"
    elif command[0] == "stop-get":
        if len_com < 3:
            return "too few arguments"
        elif not api_key:
            return "invalid api key"

        operator_id = command[1].upper()
        if operator_id not in get_operator_list():
            return "operator not found"

        operator_stops = get_operator_stops(operator_id)
        stop_id = command[2]
        valid_stops = {num.upper(): (num, nom) for num, nom, _ in operator_stops}
        if stop_id.upper() not in valid_stops:
            return "stop not found"

        canonical_stop_id, stop_nom = valid_stops[stop_id.upper()]
        ret = f"\n{ret}\n{display_sign(canonical_stop_id, operator_id)}"

        if not ret.strip():
            ret = f"\n{stop_nom} ({canonical_stop_id})\n\nNo upcoming departures."
        else:
            ret = f"\n{stop_nom} ({canonical_stop_id}){ret}"

    elif command[0] == "search-stops":
        if len_com < 3:
            return "too few arguments"
        elif not api_key:
            return "invalid api key"
        
        operator_id = command[1].upper()
        if operator_id not in get_operator_list():
            return "operator not found"

        search: str = " ".join(command[2:])

        stops = query(get_operator_stops(operator_id), search, 5)

        for stop_id, stop_name, *_ in stops:
            ret = f"{ret}\n{stop_id} {stop_name}"

    elif command[0] == "search-lines":
        if len_com < 3:
            return "too few arguments"
        elif not api_key:
            return "invalid api key"

        operator_id = command[1].upper()
        if operator_id not in get_operator_list():
            return "operator not found"

        search = " ".join(command[2:])
        if operator_id == "SF":

            # fuck you muni

            lines = query(get_operator_routes(operator_id), search.upper(), 5)
        else:
            lines = query(get_operator_routes(operator_id), search, 5)

        for line_id, line_name, _, _ in lines:
            ret = f"{ret}\n{line_id} {line_name}"
    elif command[0] == "key":
        if len_com < 2:
            if api_key:
                return f"your api key is {api_key}"
            else:
                return "no api key found"
        try:
            operators_raw = requests.get("http://api.511.org/transit/operators", params={"api_key": command[1]}, timeout=10)
            operators_raw.raise_for_status()
        except Exception:
            return "an error occured"
        else:
            with open(CONFIG, "w") as file:
                file.write(f"KEY_511={command[1]}\n")
            os.chmod(CONFIG, 0o600)
            print("key has been changed successfully, exiting")
            sys.exit(0)
    else:
        return "wrong syntax"
    return ret

def cls() -> None:
    print("\033c", end="", flush=True) # stupid ass hack

def display_sign(stop_id: str, private_code: str) -> str:
    nb_list = get_next_bus(stop_id, private_code)
    line_color: str = "cyan bold"
    ret: str = ""
    for stop_num, stop_name, next_time, line_num, line_name, terminus in nb_list:
        if private_code == "SF":
            line_color = MUNI_METRO.get(line_num, "cyan bold")
        ret = f"{ret}\n[{line_color}]{line_num}[/] [yellow]{line_name}[/] to [green]{terminus}[/] {next_time}"
    return ret

def debug():
    print("---DEBUG---")
    ro_list = get_operator_routes("BA")
    for route_id, name, mode, _ in ro_list:
        if mode == "OP":
            print(name)
        else:
            print(f"{route_id} {name}: {mode}")
    op_list = get_operator_list()
    print("OPERATORS")
    print(op_list)
    print("STOP 15781 (MUNI)")
    nb_list = get_next_bus("15781", "SF")
    print(nb_list)
    print("L TARAVAL")
    st_list = get_route_stops("L", "SF")
    for stop_id, stop_name, operator in st_list:
        print(stop_id, stop_name)
def main() -> None:
    #routes: list[Route] = get_operator_routes("BA")
    #for route in routes:
    #    print(str(route))
    #debug()
    print(welcome)
    while True:
        sh_511()