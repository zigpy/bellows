import logging

import click
import click_log
import zigpy.config

from . import opts


@click.group()
@click_log.simple_verbosity_option(logging.getLogger(), default="WARNING")
@opts.device
@opts.baudrate
@opts.flow_control
@click.pass_context
def main(ctx, device, baudrate, flow_control):
    ctx.obj = {
        zigpy.config.CONF_DEVICE_PATH: device,
        zigpy.config.CONF_DEVICE_BAUDRATE: baudrate,
        zigpy.config.CONF_DEVICE_FLOW_CONTROL: flow_control,
    }
    click_log.basic_config()


if __name__ == "__main__":
    main()
