"""Tests for device roster and entity state generation."""
from tests.synthetic.entities import Device, DeviceRoster, EntityStateGenerator
from tests.synthetic.people import Person, Schedule


class TestDevice:
    def test_device_has_required_fields(self):
        d = Device(entity_id="light.kitchen", domain="light", device_class=None,
                   watts=60, rooms=["kitchen"])
        assert d.entity_id == "light.kitchen"
        assert d.domain == "light"

    def test_device_state_for_light_on(self):
        d = Device(entity_id="light.kitchen", domain="light", device_class=None,
                   watts=60, rooms=["kitchen"])
        state = d.to_ha_state("on", brightness=180)
        assert state["entity_id"] == "light.kitchen"
        assert state["state"] == "on"
        assert state["attributes"]["brightness"] == 180
        assert state["attributes"]["friendly_name"] == "Kitchen Light"

    def test_device_state_for_sensor(self):
        d = Device(entity_id="sensor.power_consumption", domain="sensor",
                   device_class="power", watts=0, rooms=[])
        state = d.to_ha_state("156.5")
        assert state["state"] == "156.5"
        assert state["attributes"]["device_class"] == "power"
        assert state["attributes"]["unit_of_measurement"] == "W"


class TestDeviceRoster:
    def test_typical_home_has_entities(self):
        roster = DeviceRoster.typical_home()
        assert len(roster.devices) >= 40

    def test_typical_home_has_expected_domains(self):
        roster = DeviceRoster.typical_home()
        domains = {d.domain for d in roster.devices}
        assert "light" in domains
        assert "person" in domains
        assert "binary_sensor" in domains
        assert "climate" in domains
        assert "lock" in domains
        assert "sensor" in domains

    def test_get_devices_by_room(self):
        roster = DeviceRoster.typical_home()
        kitchen = roster.get_devices_in_room("kitchen")
        assert len(kitchen) > 0
        assert all("kitchen" in d.rooms for d in kitchen)

    def test_get_devices_by_domain(self):
        roster = DeviceRoster.typical_home()
        lights = roster.get_devices_by_domain("light")
        assert len(lights) >= 5
        assert all(d.domain == "light" for d in lights)


class TestEntityStateGenerator:
    def test_generates_states_for_time(self):
        roster = DeviceRoster.typical_home()
        people = [
            Person("justin", Schedule.weekday_office(6.5, 23), Schedule.weekend(8, 23.5)),
        ]
        gen = EntityStateGenerator(roster, people, seed=42)
        states = gen.generate_states(day=0, hour=12.0, is_weekend=False)
        assert len(states) > 0
        for s in states:
            assert "entity_id" in s
            assert "state" in s
            assert "attributes" in s

    def test_lights_on_when_occupied_and_dark(self):
        roster = DeviceRoster.typical_home()
        people = [
            Person("justin", Schedule.weekday_office(6.5, 23), Schedule.weekend(8, 23.5)),
        ]
        gen = EntityStateGenerator(roster, people, seed=42)
        states = gen.generate_states(day=5, hour=20.0, is_weekend=True)
        light_states = [s for s in states if s["entity_id"].startswith("light.")]
        on_lights = [s for s in light_states if s["state"] == "on"]
        assert len(on_lights) >= 1

    def test_person_away_during_work(self):
        roster = DeviceRoster.typical_home()
        people = [
            Person("justin", Schedule.weekday_office(6.5, 23), Schedule.weekend(8, 23.5)),
        ]
        gen = EntityStateGenerator(roster, people, seed=42)
        states = gen.generate_states(day=1, hour=12.0, is_weekend=False)
        person_states = [s for s in states if s["entity_id"] == "person.justin"]
        assert len(person_states) == 1
        assert person_states[0]["state"] == "not_home"

    def test_deterministic_with_seed(self):
        roster = DeviceRoster.typical_home()
        people = [Person("justin", Schedule.weekday_office(6.5, 23), Schedule.weekend(8, 23.5))]
        gen_a = EntityStateGenerator(roster, people, seed=42)
        gen_b = EntityStateGenerator(roster, people, seed=42)
        states_a = gen_a.generate_states(day=0, hour=12.0, is_weekend=False)
        states_b = gen_b.generate_states(day=0, hour=12.0, is_weekend=False)
        assert states_a == states_b
