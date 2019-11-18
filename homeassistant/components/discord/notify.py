"""Discord platform for notify component."""
import logging
import os.path

import discord
import voluptuous as vol

from homeassistant.const import CONF_TOKEN
import homeassistant.helpers.config_validation as cv

from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_TARGET,
    PLATFORM_SCHEMA,
    BaseNotificationService,
)

_LOGGER = logging.getLogger(__name__)

ATTR_IMAGES = "images"


def get_service(hass, config, discovery_info=None):
    """Get the Discord notification service."""
    return DiscordNotificationService(hass)


class DiscordNotificationService(BaseNotificationService):
    """Implement the notification service for Discord."""

    def __init__(self, hass):
        """Initialize the service."""
        self.hass = hass

    def file_exists(self, filename):
        """Check if a file exists on disk and is in authorized path."""
        if not self.hass.config.is_allowed_path(filename):
            return False

        return os.path.isfile(filename)

    async def async_send_message(self, message, **kwargs):
        """Using a discord webhook, post a message to specified target(s)."""

        images = None

        if ATTR_TARGET not in kwargs:
            _LOGGER.error("No target specified")
            return None

        data = kwargs.get(ATTR_DATA) or {}

        if ATTR_IMAGES in data:
            images = list()

            for image in data.get(ATTR_IMAGES):
                image_exists = await self.hass.async_add_executor_job(
                    self.file_exists, image
                )

                if image_exists:
                    images.append(discord.File(image))
                else:
                    _LOGGER.warning("Image not found: %s", image)

        try:
            for url in kwargs[ATTR_TARGET]:
                try:
                    webhook = discord.Webhook.from_url(url, adapter=discord.AsyncWebhookAdapter(session))
                    webhook.send(message, files=files)
                except (discord.errors.InvalidArgument, ) as error:
                    _LOGGER.warning("Invalid webhook url: %s", url)
                    continue
                except (discord.errors.Forbidden, discord.errors.NotFound) as error:
                    _LOGGER.warning("Webhook is no longer valid or has been deleted: %s\n%s", url, error)
                    continue

                webhook.send(message, files=files)
        except (discord.errors.HTTPException, ) as error:
            _LOGGER.warning("Communication error: %s", error)
        
