import click

from . import util
from .main import main


@main.command()
@click.pass_context
@util.background
async def backup(ctx):
    """Backup NCP config to stdio."""
    click.echo(
        "The bellows backup/restore command set has been removed. Please use zigpy-cli instead: https://github.com/zigpy/zigpy-cli#network-backup"
    )


@main.command()
@click.option(
    "--i-understand-i-can-update-eui64-only-once-and-i-still-want-to-do-it",
    is_flag=True,
    required=False,
    default=False,
    help=(
        "EUI64 can be overridden using a manufacturer token only once and will not "
        "accept new changes once it is set"
    ),
)
@click.option("-f", "--force", is_flag=True, required=False, default=False)
@click.option("-B", "--backup-file", type=str, required=True)
@click.option(
    "-U", "--upgrade-to-hashed-tc-link-key", is_flag=True, required=False, default=False
)
@click.pass_context
@util.background
async def restore(
    ctx,
    backup_file,
    force,
    i_understand_i_can_update_eui64_only_once_and_i_still_want_to_do_it,
    upgrade_to_hashed_tc_link_key,
):
    """Backup NCP config to stdio."""
    click.echo(
        "The bellows backup/restore command set has been removed. Please use zigpy-cli instead: https://github.com/zigpy/zigpy-cli#network-backup"
    )
