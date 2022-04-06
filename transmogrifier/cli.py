import logging
import os

import click
import sentry_sdk

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def main(ctx):
    ctx.ensure_object(dict)
    sentry_sdk.init(os.getenv("SENTRY_DSN"), environment=os.getenv("WORKSPACE"))
    logger.info(
        "Configuring transmogrifier for current env: %s", os.getenv("LOGGING_LEVEL")
    )
    logger.info(
        "Initializing transmogrifier with logging level: %s", os.getenv("LOGGING_LEVEL")
    )


@main.command()
def zenodo():
    logger.info("Running zenodo")
