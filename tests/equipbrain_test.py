"""pytest tests to test functions in equipbrain.py.

The qindex fixture is supplied by tests/conftest.py."""

from hagadias.equipbrain import EquipBrain


def test_create(qindex):
    creature = qindex['Q Girl']  # multiple potential armors, quills
    brain = EquipBrain(creature, qindex)
    creature = qindex['Lulihart']  # m-arms, m-legs
    brain = EquipBrain(creature, qindex)
    creature = qindex['Two-Headed Slugsnout']  # 2 head slots
    brain = EquipBrain(creature, qindex)
    creature = qindex['Worm of the Earth']  # burrowing claws
    brain = EquipBrain(creature, qindex)
    creature = qindex['Warden Ualraig']  # horns
    brain = EquipBrain(creature, qindex)
    creature = qindex['Scorpiock']  # stinger
    brain = EquipBrain(creature, qindex)


def test_get_items_for_slot(qindex):
    creature = qindex['Q Girl']  # multiple potential armors, quills
    brain = EquipBrain(creature, qindex)
    assert brain.get_items_for_slot('Body') == ['Plastifer Jerkin', 'Strength Exo']


def test_can_equip_armor(qindex):
    creature = qindex['Q Girl']  # multiple potential armors, quills
    brain = EquipBrain(creature, qindex)
    assert brain.can_equip_armor(qindex['Plastifer Jerkin']) is True


def test_armor_score(qindex):
    creature = qindex['Q Girl']  # multiple potential armors, quills
    brain = EquipBrain(creature, qindex)
    assert brain.armor_score('Plastifer Jerkin') == 1  # standin value


def test_weapon_score(qindex):
    creature = qindex['Q Girl']  # multiple potential armors, quills
    brain = EquipBrain(creature, qindex)
    assert brain.weapon_score(qindex['Dagger2']) == 1  # standin value


def test_is_new_weap_better_for_primary_hand(qindex):
    creature = qindex['Q Girl']  # multiple potential armors, quills
    brain = EquipBrain(creature, qindex)
    weap_bad = qindex['Dagger2']  # iron dagger
    weap_good = qindex['Dagger3']  # carbide dagger
    assert brain.new_weap_better_primary(weap_good, weap_bad) is True
    assert brain.new_weap_better_primary(weap_bad, weap_good) is False
