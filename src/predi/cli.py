"""This begins a basic cli. In its current state, bem calls these commands if predi.repo/tests is True"""
from pathlib import Path

import click
import pytest

from . import core, edi, transactions
from .tests import generate_fixtures

context_settings = {"help_option_names": ["-h", "--help"]}


@click.group(context_settings=context_settings)
@click.pass_context
def cli(ctx):
    pass


@click.group(name="system")
def system_group():
    pass


@system_group.command(name="selftest")
def selftest_cli():
    pytest.main(["."])


@click.command(name="load")
@click.option("--lang", default=None, help="EDI langauge of source")
@click.argument("filepath")
def load_cli(lang: str, filepath: str):
    if lang:
        decoder = edi.Standards[lang].value.decoder
    else:
        decoder = None
    click.echo(core.load(Path(filepath).open(), decoder=decoder))


@click.command(name="translate")
@click.option("-f", default=None, help="EDI langauge of source")
@click.argument("source")
@click.option("-t", default=None, help="EDI langauge of destination")
@click.argument("destination")
def translate_cli(f: str, source: str, t: str, destination):
    if f:
        decoder = edi.get_standard(f).decoder
    else:
        decoder = None
    doc = core.load(Path(source).open("r"), decoder=decoder)
    if t:
        encoder = edi.get_standard(t).encoder
    else:
        encoder = None
    core.dump(doc, Path(destination).open("w"), encoder=encoder)


@click.command(name="generate-fixtures")
def generate_fixtures_cli():
    generate_fixtures.main()


cli.add_command(load_cli)
cli.add_command(translate_cli)
cli.add_command(generate_fixtures_cli)
cli.add_command(system_group)
main = cli

if __name__ == "__main__":
    main()
