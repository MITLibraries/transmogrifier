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
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.INFO,
        handlers=[logging.StreamHandler()],
    )
    logger.info("Initializing app")


@main.command()
def zenodo():
    print("Running zenodo")


def check_sentry():
    if os.getenv("SENTRY_DSN"):
        logger.info("Sending a Zero Division Error to Sentry")
        1 / 0
    else:
        logger.info("No Sentry DSN found")
