import logging

import click
import click_log

from bellows.config import CONF_DEVICE, CONF_DEVICE_BAUDRATE, CONF_FLOW_CONTROL

from . import opts


@click.group()
@click_log.simple_verbosity_option(logging.getLogger(), default="WARNING")
@opts.device
@opts.baudrate
@opts.flow_control
@click.pass_context
def main(ctx, device, baudrate, flow_control):
    ctx.obj = {
        CONF_DEVICE: device,
        CONF_DEVICE_BAUDRATE: baudrate,
        CONF_FLOW_CONTROL: flow_control,
    }
    click_log.basic_config()


if __name__ == "__main__":
    main()
