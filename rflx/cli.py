import argparse
import logging
import os
from pathlib import Path
from typing import List, Union

from rflx import __version__
from rflx.common import flat_name
from rflx.error import RecordFluxError, Severity, Subsystem, fail
from rflx.generator import Generator
from rflx.graph import Graph
from rflx.model import Model, ModelError
from rflx.parser import Parser, ParserError

logging.basicConfig(level=logging.INFO, format="%(message)s")

DEFAULT_PREFIX = "RFLX"


def main(argv: List[str]) -> Union[int, str]:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="disable logging to standard output"
    )
    parser.add_argument("--version", action="store_true")

    subparsers = parser.add_subparsers(dest="subcommand")

    parser_check = subparsers.add_parser("check", help="check specification")
    parser_check.add_argument(
        "files", metavar="FILE", type=str, nargs="+", help="specification file"
    )
    parser_check.set_defaults(func=check)

    parser_generate = subparsers.add_parser("generate", help="generate code")
    parser_generate.add_argument(
        "-p",
        "--prefix",
        type=str,
        default="RFLX",
        help=("add prefix to generated packages " f"(default: {DEFAULT_PREFIX})"),
    )
    parser_generate.add_argument(
        "-n", "--no-library", help="omit generating library files", action="store_true"
    )
    parser_generate.add_argument(
        "-d", "--directory", help="output directory", default=".", type=str
    )
    parser_generate.add_argument(
        "files", metavar="FILE", type=str, nargs="*", help="specification file"
    )
    parser_generate.set_defaults(func=generate)

    parser_graph = subparsers.add_parser("graph", help="generate graphs")
    parser_graph.add_argument(
        "-f",
        "--format",
        type=str,
        default="svg",
        choices=["dot", "jpg", "pdf", "png", "raw", "svg"],
        help=("output format (default: svg)"),
    )
    parser_graph.add_argument(
        "files", metavar="FILE", type=str, nargs="+", help="specification file"
    )
    parser_graph.add_argument("-d", "--directory", help="output directory", default=".", type=str)
    parser_graph.set_defaults(func=graph)

    args = parser.parse_args(argv[1:])

    if args.version:
        print(__version__)
        return 0

    if not args.subcommand:
        parser.print_usage()
        return 2

    if args.quiet:
        logging.disable(logging.CRITICAL)

    try:
        args.func(args)
    except RecordFluxError as e:
        return f"{e}"
    except ParserError as e:
        return f"{parser.prog}: parser error: {e}"
    except ModelError as e:
        return f"{parser.prog}: model error: {e}"
    except OSError as e:
        return f"{parser.prog}: error: {e}"

    return 0


def check(args: argparse.Namespace) -> None:
    parse(args.files)


def generate(args: argparse.Namespace) -> None:
    # WORKAROUND: Componolit/Workarounds#28
    args.prefix = args.prefix if args.prefix != " " else ""

    if args.prefix and "" in args.prefix.split("."):
        fail(f'invalid prefix: "{args.prefix}"', Subsystem.CLI)

    directory = Path(args.directory)
    if not directory.is_dir():
        fail(f'directory not found: "{directory}"', Subsystem.CLI)

    generator = Generator(args.prefix, reproducible=os.environ.get("RFLX_REPRODUCIBLE") is not None)

    model = parse(args.files)
    generator.generate(model)

    generator.write_units(directory)
    if not args.no_library:
        generator.write_library_files(directory)
    if args.prefix == DEFAULT_PREFIX:
        generator.write_top_level_package(directory)


def parse(files: List) -> Model:
    parser = Parser()

    error = RecordFluxError()
    for f in files:
        if not Path(f).is_file():
            error.append(f'file not found: "{f}"', Subsystem.CLI, Severity.ERROR)
        else:
            # pylint: disable=fixme
            # FIXME: Add test with missing file and parse error
            parser.parse(Path(f))
    error.propagate()

    return parser.create_model()


def graph(args: argparse.Namespace) -> None:
    directory = Path(args.directory)
    if not directory.is_dir():
        fail(f'directory not found: "{directory}"', Subsystem.GRAPH)

    model = parse(args.files)

    for m in model.messages:
        message = flat_name(m.full_name)
        filename = Path(directory).joinpath(message).with_suffix(f".{args.format}")
        Graph(m).write(filename, fmt=args.format)
