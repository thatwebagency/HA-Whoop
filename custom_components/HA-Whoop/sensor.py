"""Support for Whoop sensors."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import DOMAIN, SENSOR_TYPES
from . import WhoopDataUpdateCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Whoop sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = []
    for sensor_type in SENSOR_TYPES:
        sensors.append(WhoopSensor(coordinator, sensor_type))

    async_add_entities(sensors)

class WhoopSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Whoop sensor."""

    def __init__(
        self,
        coordinator: WhoopDataUpdateCoordinator,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = SENSOR_TYPES[sensor_type]["name"]
        self._attr_unique_id = f"whoop_{sensor_type}"
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit"]
        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]
        
        # Set device class based on sensor type
        if "heart_rate" in sensor_type:
            self._attr_device_class = SensorDeviceClass.HEART_RATE
        elif sensor_type.endswith("_score"):
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        if self._sensor_type == "recovery_score":
            return self.coordinator.data.get("recovery", {}).get("score")
        elif self._sensor_type == "resting_heart_rate":
            return self.coordinator.data.get("recovery", {}).get("resting_heart_rate")
        elif self._sensor_type == "sleep_score":
            return self.coordinator.data.get("sleep", {}).get("score")
        elif self._sensor_type == "sleep_duration":
            sleep_duration = self.coordinator.data.get("sleep", {}).get("duration")
            if sleep_duration:
                return round(sleep_duration / 3600, 2)  # Convert seconds to hours
        elif self._sensor_type == "strain_score":
            return self.coordinator.data.get("cycle", {}).get("strain")
            
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {}
        
        if self._sensor_type == "recovery_score":
            recovery_data = self.coordinator.data.get("recovery", {})
            attrs["hrv"] = recovery_data.get("hrv")
            attrs["spo2"] = recovery_data.get("spo2")
        elif self._sensor_type == "sleep_score":
            sleep_data = self.coordinator.data.get("sleep", {})
            attrs["efficiency"] = sleep_data.get("efficiency")
            attrs["disturbances"] = sleep_data.get("disturbances")
            
        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self.coordinator.data is not None