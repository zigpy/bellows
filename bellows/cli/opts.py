import os

import click

from . import util

CHANNELS = list(range(11, 27))

channel = click.option(
    '-c', '--channel',
    type=click.IntRange(11, 26),
    required=True,
    default=15,
)

channels = click.option(
    '-C', '--channels',
    type=util.CSVParamType(11, 26),
    metavar='CHANNELS',
    default=','.join(map(str, CHANNELS)),
    show_default=True,
)

device = click.option(
    '-d', '--device',
    type=click.STRING,
    envvar='EZSP_DEVICE',
    required=True,
)

baudrate = click.option(
    '-b', '--baudrate',
    type=click.INT,
    envvar='EZSP_BAUDRATE',
    default=57600
)

database_file = click.option(
    '-D', '--database',
    type=click.Path(
        exists=True,
        dir_okay=False,
        writable=True,
    ),
    required=True,
    default=os.path.join(click.get_app_dir("bellows"), "app.db"),
)

duration_ms = click.option(
    '-t', '--duration', 'duration_ms',
    type=click.INT, metavar='MILLISECONDS',
    default=50,
    show_default=True,
)

duration_s = click.option(
    '-t', '--duration', 'duration_s',
    type=click.INT, metavar='SECONDS',
    default=30,
    show_default=True,
)

extended_pan = click.option(
    '-E', '--extended-pan-id',
    type=click.STRING,
)

pan = click.option(
    '-P', '--pan-id',
    type=click.IntRange(0, 65535),
)

manufacturer = click.option(
    '-m', '--manufacturer',
    type=click.IntRange(0, 0xFFFF),
    default=None,
    help='send a manufacturer specific command'
)
