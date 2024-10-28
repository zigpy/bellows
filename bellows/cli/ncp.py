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
        for config in t.EzspConfigId:
            v = await s.getConfigurationValue(config)
            if v[0] == t.EzspStatus.ERROR_INVALID_ID:
                continue
            click.echo(f"{config.name}={v[1]}")
        await s.disconnect()
        return

    if "=" in config:
        config, value = config.split("=", 1)
        if config.isdigit():
            try:
                config = t.EzspConfigId(int(config))
            except ValueError:
                raise click.BadArgumentUsage(f"Invalid config ID: {config}")
        else:
            try:
                config = t.EzspConfigId[config]
            except KeyError:
                raise click.BadArgumentUsage(f"Invalid config name: {config}")
        try:
            value = t.uint16_t(value)
            if not (0 <= value <= 65535):
                raise ValueError(f"{value} out of allowed range 0..65535")
        except ValueError as e:
            raise click.BadArgumentUsage(f"Invalid value: {e}")

        v = await s.setConfigurationValue(config, value)
        click.echo(v)
        await s.disconnect()
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

    await s.disconnect()


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
        await ezsp.disconnect()
        return

    click.echo(
        f"bootloader version: 0x{version:04x}, nodePlat: 0x{plat:02x}, "
        f"nodeMicro: 0x{micro:02x}, nodePhy: 0x{phy:02x}"
    )

    res = await ezsp.launchStandaloneBootloader(0x00)
    if res[0] != t.EmberStatus.SUCCESS:
        click.echo(f"Couldn't launch bootloader: {res[0]}")
    else:
        click.echo("bootloader launched successfully")
    await ezsp.disconnect()
