import logging
import os

import click
import sentry_sdk

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def main(ctx):
    ctx.ensure_object(dict)
    env = os.getenv("WORKSPACE")
    logger.info(
        "Running transmogrifier with env=%s and log level=%s,",
        env,
        os.getenv("LOGGING_LEVEL", "DEBUG").upper(),
    )
    if sentry_dsn := os.getenv("SENTRY_DSN"):
        sentry_sdk.init(sentry_dsn, environment=env)
        logger.info(
            "Sentry DSN found, exceptions will be sent to Sentry with env=%s", env
        )


@main.command()
def zenodo():
    logger.info("Running zenodo")
