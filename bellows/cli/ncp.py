import click

import bellows.types as t

from . import util
from .main import main


@main.command()
@click.argument("config", required=False)
@click.option("-a", "--all", "all_", is_flag=True)
@click.pass_context
@util.background
async def config(ctx, config, all_):
    """Get/set configuration on the NCP"""
    click.secho("NOTE: Configuration changes do not persist across resets", fg="red")
    if config and all_:
        raise click.BadOptionUsage("Specify a config or --all, not both")

    if not (config or all_):
        raise click.BadOptionUsage("One of config or --all must be specified")

    s = await util.setup(
        ctx.obj["device"], ctx.obj["baudrate"], util.print_cb, configure=False
    )

    if all_:
        for config in s.types.EzspConfigId:
            v = await s.getConfigurationValue(config)
            if v[0] == t.EzspStatus.ERROR_INVALID_ID:
                continue
            click.echo("%s=%s" % (config.name, v[1]))
        s.close()
        return

    if "=" in config:
        config, value = config.split("=", 1)
        if config.isdigit():
            try:
                config = s.types.EzspConfigId(int(config))
            except ValueError:
                raise click.BadArgumentUsage("Invalid config ID: %s" % (config,))
        else:
            try:
                config = s.types.EzspConfigId[config]
            except KeyError:
                raise click.BadArgumentUsage("Invalid config name: %s" % (config,))
        try:
            value = t.uint16_t(value)
            if not (0 <= value <= 65535):
                raise ValueError("%s out of allowed range 0..65535" % (value,))
        except ValueError as e:
            raise click.BadArgumentUsage("Invalid value: %s" % (e,))

        v = await s.setConfigurationValue(config, value)
        click.echo(v)
        s.close()
        return

    v = await s.getConfigurationValue(config)
    click.echo(v)


@main.command()
@click.pass_context
@util.background
async def info(ctx):
    """Get NCP information"""
    s = await util.setup(ctx.obj["device"], ctx.obj["baudrate"])
    await util.network_init(s)

    commands = [
        "getEui64",
        "getNodeId",
        "networkState",
        "getNetworkParameters",
        "getCurrentSecurityState",
    ]

    for c in commands:
        v = await getattr(s, c)()
        click.echo(v)

    brd_manuf, brd_name, version = await s.get_board_info()
    click.echo(f"Manufacturer: {brd_manuf}")
    click.echo(f"Board name: {brd_name}")
    click.echo(f"EmberZNet version: {version}")

    s.close()


@main.command()
@click.pass_context
@util.background
async def bootloader(ctx):
    """Start bootloader"""

    ezsp = await util.setup(ctx.obj["device"], ctx.obj["baudrate"], configure=False)

    brd_manuf, brd_name, version = await ezsp.get_board_info()
    click.echo(f"Manufacturer: {brd_manuf}")
    click.echo(f"Board name: {brd_name}")
    click.echo(f"Current EmberZNet version: {version}")

    version, plat, micro, phy = await ezsp.getStandaloneBootloaderVersionPlatMicroPhy()
    if version == 0xFFFF:
        click.echo("No boot loader installed")
        ezsp.close()
        return

    click.echo(
        (
            f"bootloader version: 0x{version:04x}, nodePlat: 0x{plat:02x}, "
            f"nodeMicro: 0x{micro:02x}, nodePhy: 0x{phy:02x}"
        )
    )

    res = await ezsp.launchStandaloneBootloader(0x00)
    if res[0] != t.EmberStatus.SUCCESS:
        click.echo(f"Couldn't launch bootloader: {res[0]}")
    else:
        click.echo("bootloader launched successfully")
    ezsp.close()
