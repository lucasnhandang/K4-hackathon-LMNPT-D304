from __future__ import annotations

import argparse
import logging
import sys

from .config import ConfigError, load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect allowlisted Discord messages.")
    parser.add_argument("--env-file", default=".env", help="Path to the private .env file.")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate configuration without connecting to Discord.",
    )
    parser.add_argument(
        "--inspect-access",
        action="store_true",
        help="List servers visible to the bot, then exit.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        config = load_config(args.env_file)
    except ConfigError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        raise SystemExit(2) from error

    if args.validate_only:
        print(
            "Configuration valid: "
            f"{len(config.collect_channel_ids)} channels, "
            f"{config.retention_days}-day retention."
        )
        return

    if args.inspect_access:
        try:
            from .access import inspect_guilds
        except ModuleNotFoundError as error:
            if error.name == "discord":
                print(
                    "Missing dependency: run 'python -m pip install -r requirements.txt'.",
                    file=sys.stderr,
                )
                raise SystemExit(3) from error
            raise
        inspect_guilds(config.token)
        return

    try:
        from .bot import DiscordCollector
    except ModuleNotFoundError as error:
        if error.name == "discord":
            print(
                "Missing dependency: run 'python -m pip install -r requirements.txt'.",
                file=sys.stderr,
            )
            raise SystemExit(3) from error
        raise

    collector = DiscordCollector(config)
    collector.run(config.token, log_handler=None)


if __name__ == "__main__":
    main()
