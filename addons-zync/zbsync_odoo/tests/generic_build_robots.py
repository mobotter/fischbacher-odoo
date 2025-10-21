# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import yaml
from pathlib import Path
import inspect
import os
from pathlib import Path
from itertools import islice

current_dir = Path(
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)

os.chdir(current_dir)

tests_per_robot = 3
output_file = "dumper.tests"
template_header_file = Path("header.robot.template")
template_file = Path("dumper.robot.template")

yaml_tests = Path("test_cases.yaml").read_text()

data = yaml.safe_load(yaml_tests)
result = []
methods = []


def safe_fstring(template, **kwargs):
    return eval(f'f"""{template}"""', {}, kwargs)


def format_data(data):
    data = data or ""
    while "  " in data:
        data = data.replace("  ", " ")
    data = "\n".join(
        filter(
            lambda x: not x.startswith("#"), map(lambda x: x.strip(), data.splitlines())
        )
    )
    data += "\n"
    data = data.replace("\n", "  ")
    return data


def _get_pre_steps(record):
    if record.get("continue_from"):
        for item in data["dumper"]:
            if item["name"].strip() == record["continue_from"].strip():
                yield from _get_pre_steps(item)
                yield f"${{instance_id}}=  Dumper Core {item['i']} {item['name']}  remote=${{remote}}  prev_instance_id=${{instance_id}}"
                break
        else:
            raise Exception(f"Not found: {record['continue_from']}")


for i, record in enumerate(data["dumper"], 1000):
    record["i"] = i

for record in data["dumper"]:
    template = template_file.read_text()
    robot_test_name = f"Odoo Dumper {i} {record['name']}"
    print("Robot test name: ", robot_test_name)
    try:
        record["input_data"] = format_data("res = " + record["input"] + "\nres")
        prep = format_data(record.get("prep"))
        record["check"] = format_data(record["check"]) + "  True"
        if prep:
            record["input_data"] = f"{prep} {record['input_data']}"

        record["presteps"] = (
            "\n".join(map(lambda x: "\t" + x.strip(), _get_pre_steps(record)))
        )[1:]
        if record["presteps"]:
            record["presteps"] = f"# preparation steps\n\t" + record["presteps"]

        test = safe_fstring(template, **record)
    except Exception as ex:
        print(f"Error formatting data for {robot_test_name}: {ex}")
        raise
    methods.append((f"{robot_test_name}  prefix=${{prefix}}", test))
    print(f"method: {methods[-1][0]}\ntest: {methods[-1][1][:50]}\n\n\n\n\n")


def strip_testcases(tests_and_keywords):
    lines = tests_and_keywords.splitlines()
    lines2 = []

    tc = False
    for line in lines:
        if "*** Test Cases ***" in line:
            tc = True
        if "*** Keywords ***" in line:
            tc = False
        if not tc:
            lines2.append(line)

    return "\n".join(lines2)


def split_every(n, iterable, piece_maker=tuple):
    """Splits an iterable into length-n pieces. The last piece will be shorter
    if ``n`` does not evenly divide the iterable length.

    :param int n: maximum size of each generated chunk
    :param Iterable iterable: iterable to chunk into pieces
    :param piece_maker: callable taking an iterable and collecting each
                        chunk from its slice, *must consume the entire slice*.
    """
    iterator = iter(iterable)
    piece = piece_maker(islice(iterator, n))
    while piece:
        yield piece
        piece = piece_maker(islice(iterator, n))


header = template_header_file.read_text()

OUTPUT_FILE = str(output_file)
methods_by_now = []
for i, chunk in enumerate(split_every(tests_per_robot, methods), start=1):
    methods = [x[0] for x in chunk]
    tests = [x[1] for x in chunk]
    output_file = Path(OUTPUT_FILE + f".{i}.robot")
    output_file.write_text(
        header.format(
            methods="\n\t".join(methods),
        )
        + "\n".join(tests)
        + "\n\n*** Keywords ***\n#Keywords from previous files\n"
        + "\n".join(methods_by_now)
    )
    methods_by_now.append(strip_testcases("\n\t".join(tests)))
