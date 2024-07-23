import logging

import click
import click_log

from . import opts


@click.group()
@click_log.simple_verbosity_option(logging.getLogger(), default="WARNING")
@opts.device
@opts.baudrate
@opts.flow_control
@click.pass_context
def main(ctx, device, baudrate, flow_control):
    ctx.obj = {
        "device": device,
        "baudrate": baudrate,
        "flow_control": flow_control if flow_control != "none" else None,
    }
    click_log.basic_config()


if __name__ == "__main__":
    main()
