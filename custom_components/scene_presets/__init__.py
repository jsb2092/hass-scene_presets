import voluptuous as vol
import os
import homeassistant.helpers.config_validation as cv
import json
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN


SERVICE_APPLY_SCENE = "apply_scene"
ATTR_SCENE_PRESET_ID = "preset_id"
ATTR_LIGHT_ENTITIES = "light_entities"
ATTR_BRIGHTNESS = "brightness"
PRESETS_JSON_FILE = os.path.join(os.path.dirname(__file__), "./presets.json")

with open(PRESETS_JSON_FILE, "r") as file:
    SCENES_DATA = json.load(file)

SCENE_SCHEMA = vol.Schema({
    vol.Required(ATTR_SCENE_PRESET_ID): cv.string,
    vol.Required(ATTR_LIGHT_ENTITIES): cv.ensure_list,
    vol.Optional(ATTR_BRIGHTNESS): vol.Coerce(int),
})


_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    async def apply_scene_service(call):
        scene_id = call.data.get(ATTR_SCENE_PRESET_ID)
        light_entities = call.data.get(ATTR_LIGHT_ENTITIES)
        brightness_override = call.data.get(ATTR_BRIGHTNESS)

        # Retrieve the scene data by ID (if found)
        scene_data = None
        for scene_set in SCENES_DATA.get("sets", []):
            for scene in scene_set.get("scenes", []):
                if scene.get("name") == scene_id:
                    scene_data = scene
                    break
            if scene_data:
                break

        if not scene_data:
            raise ValueError(f"Scene '{scene_id}' not found in the JSON file.")

        # Apply the scene to the selected light entities
        light_index = 0
        for light_entity in light_entities:
            if light_index >= len(scene_data["lights"]):
                light_index = 0  # Start back at the beginning

            light_params = {
                "xy_color": [
                    scene_data["lights"][light_index]["x"],
                    scene_data["lights"][light_index]["y"]
                ],
                "brightness": brightness_override if brightness_override is not None else scene_data.get("bri", 255)
            }

            # Call the light.turn_on service to set the light's state
            await hass.services.async_call(
                "light",
                "turn_on",
                {
                    "entity_id": light_entity,
                    "xy_color": light_params["xy_color"],
                    "brightness": light_params["brightness"],
                },
                blocking=True,
            )

            light_index += 1

    hass.services.async_register(
        DOMAIN,
        SERVICE_APPLY_SCENE,
        apply_scene_service,
        schema=SCENE_SCHEMA,
    )

    return True

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    hass.data.setdefault(DOMAIN, {})

    return True