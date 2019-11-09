import logging

import click
import click_log

from . import opts


@click.group()
@click_log.simple_verbosity_option(logging.getLogger())
@opts.device
@opts.baudrate
@click.pass_context
def main(ctx, device, baudrate):
    ctx.obj = {"device": device, "baudrate": baudrate}
    click_log.basic_config()


if __name__ == "__main__":
    main()
