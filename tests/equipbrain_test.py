"""pytest tests to test functions in equipbrain.py.

The qindex fixture is supplied by tests/conftest.py."""

from hagadias.equipbrain import EquipBrain


def test_create(qindex):
    creature = qindex['Q Girl']
    brain = EquipBrain(creature, qindex)
