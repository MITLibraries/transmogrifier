import logging
import os

import click
import sentry_sdk

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def main(ctx):
    ctx.ensure_object(dict)
    sentry_sdk.init(os.getenv("SENTRY_DSN"), environment=os.getenv("ENV"))
    logger.info("Initializing app")


@main.command()
def zenodo():
    logger.info("Running zenodo")
