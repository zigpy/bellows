import logging

import click
import click_log

from . import opts


LOGGER = logging.getLogger(__name__)


@click.group()
@click_log.simple_verbosity_option()
@click_log.init()
@opts.device
@click.pass_context
def main(ctx, device):
    ctx.obj = {'device': device}
    root = logging.getLogger('root')
    root.handlers = [click_log.ClickHandler()]
    root.setLevel(click_log.get_level())


if __name__ == '__main__':
    main()
