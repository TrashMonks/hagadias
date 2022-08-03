from __future__ import annotations

import logging
import math
from functools import cached_property
from typing import Tuple, List

from hagadias.character_codes import STAT_NAMES
from hagadias.constants import (
    BIT_TRANS,
    ITEM_MOD_PROPS,
    FACTION_ID_TO_NAME,
    CYBERNETICS_HARDCODED_INFIXES,
    CYBERNETICS_HARDCODED_POSTFIXES,
    HARDCODED_CHARGE_USE,
    CHARGE_USE_REASONS,
    ACTIVE_PARTS,
    STAT_DISPLAY_NAMES,
    BUTCHERABLE_POPTABLES,
    CHERUBIM_DESC,
    MECHANICAL_CHERUBIM_DESC,
)
from hagadias.dicebag import DiceBag
from hagadias.helpers import (
    cp437_to_unicode,
    int_or_none,
    strip_oldstyle_qud_colors,
    strip_newstyle_qud_colors,
    pos_or_neg,
    make_list_from_words,
    str_or_default,
    int_or_default,
    bool_or_default,
    float_or_none,
    float_or_default,
)
from hagadias.qudobject import QudObject
from hagadias.qudpopulation import QudPopulation
from hagadias.svalue import sValue

log = logging.getLogger(__name__)
# STATIC GROUPS
# Many combat properties can come from anything that inherits from either of these.
# Use For: self.active_or_inactive_character() == ACTIVE_CHAR
# ACTIVE: What is typically considered a Character, with an inventory and combat capabilities.
# INACTIVE: What would still be helpful to have combat related stats, but have things that
# for ALL_CHARS, use self.active_or_inactive_character() > 0
ACTIVE_CHAR = 1
INACTIVE_CHAR = 2
# make them different from active characters. Usually immobile and have no attributes.
BEHAVIOR_DESCRIPTION_PARTS = [
    "LatchesOn",
    "SapChargeOnHit",
    "TemperatureAdjuster",
    "Toolbox",
    "CyberneticsBaseItem",
    "FollowersGetTeleport",
    "IntPropertyChanger",
]


class QudObjectProps(QudObject):
    """Represents a Caves of Qud game object with properties to calculate derived stats.

    Inherits from QudObject which does all the lower level work.

    Properties should return Python types where possible (lists, bools, etc.) and leave specific
    representations to a subclass."""

    # PROPERTY HELPERS
    # Helper methods to simplify the calculation of properties, further below.
    # Sorted alphabetically.

    def attribute_helper(self, attr: str) -> str | None:
        """Helper for retrieving attributes (Strength, etc.)"""
        val = None
        if self.active_or_inactive_character() == ACTIVE_CHAR:
            if getattr(self, f"stat_{attr}_sValue"):
                try:
                    level = int(self.lv)
                except ValueError:
                    # levels can be very rarely given like "18-29"
                    level = int(self.lv.split("-")[0])
                val = str(sValue(getattr(self, f"stat_{attr}_sValue"), level=level))
            elif getattr(self, f"stat_{attr}_Value"):
                val = getattr(self, f"stat_{attr}_Value")
        elif self.part_Armor is not None:
            val = getattr(self, f"part_Armor_{attr}")
            if val == "0":
                return None
        return val

    def attribute_boost_factor(self, attr: str) -> float | None:
        """Returns the boost factor which is applied to this stat after it's calculated."""
        if self.active_or_inactive_character() == ACTIVE_CHAR:
            boost = int_or_none(getattr(self, f"stat_{attr}_Boost"))
            if boost is not None:
                if getattr(self, f"stat_{attr}_sValue"):  # Boost only applied if there's an sValue
                    if self.role == "Minion" and attr in STAT_NAMES:
                        boost -= 1
                    if boost > 0:
                        return 0.25 * float(boost) + 1.0
                    else:
                        return 0.20 * float(boost) + 1.0

    def attribute_helper_min_max_or_avg(self, attr: str, mode: str) -> int | None:
        """Return the minimum, maximum, or average stat value for the given stat. Specify
        one of the following modes: 'min', 'max', or 'avg'."""
        val_str = self.attribute_helper(attr)
        if val_str is not None:
            boost_factor = self.attribute_boost_factor(attr)
            dice = DiceBag(val_str)
            if boost_factor is None:
                if mode == "min":
                    return int(dice.minimum())
                return int(dice.maximum()) if mode == "max" else int(dice.average())
            min_val = int(math.ceil(dice.minimum() * boost_factor))
            if mode == "min":
                return min_val
            max_val = int(math.ceil(dice.maximum() * boost_factor))
            if mode == "max":
                return max_val
            # the game rounds up on each rolled dice value after applying a Boost. This also
            # modifies the average, so we need to calculate that average outside of the DiceBag.
            avg_val = (min_val + max_val) / 2.0
            return int(avg_val)  # truncated averages are used for character stats on the wiki

    def attribute_helper_avg(self, attr: str) -> int | None:
        """Return the average stat value for the given stat."""
        return self.attribute_helper_min_max_or_avg(attr, "avg")

    def attribute_helper_min(self, attr: str) -> int | None:
        """Return the minimum stat value for the given stat."""
        return self.attribute_helper_min_max_or_avg(attr, "min")

    def attribute_helper_max(self, attr: str) -> int | None:
        """Return the maximum stat value for the given stat."""
        return self.attribute_helper_min_max_or_avg(attr, "max")

    def attribute_helper_mod(self, attr: str, statmode: str = "avg") -> int | None:
        """Return the creature's attribute modifier for the given stat. Optionally, you may
        also specify a statmode ('min', 'max', or 'avg') to determine the modifier based on the
        creature's minimum, maximum, or average stat value. Average is used by default"""
        if statmode == "min":
            val = self.attribute_helper_min(attr)
        elif statmode == "max":
            val = self.attribute_helper_max(attr)
        else:
            val = self.attribute_helper_avg(attr)
        if val is not None:
            val = (val - 16) // 2  # return stat modifier for average roll
            return val

    def resistance(self, element: str) -> int | None:
        """The elemental resistance/weakness the equipment or NPC has.
        Helper function for properties."""
        val = getattr(self, f"stat_{element}Resistance_Value")
        if self.part_Armor:
            if element == "Electric":
                element = "Elec"  # short form in armor
            val = getattr(self, f"part_Armor_{element}")
        if self.part_Roboticized and self.part_Roboticized_ChanceOneIn == "1":
            if element in ["Heat", "Cold"]:
                val = 25
            elif element == "Electric":
                val = -50
        if self.mutation:
            for mutation, info in self.mutation.items():
                if mutation == "Carapace" and element in ["Heat", "Cold"]:
                    val = 0 if val is None else int(val)
                    val += int(info["Level"]) * 5 + 5
                if mutation == "SlogGlands" and element == "Acid":
                    val = 100
        return int_or_none(val)

    def projectile_object(self, part_attr: str = "") -> QudObjectProps | str | None:
        """Retrieve the projectile object for a MissileWeapon or Arrow.
        If part_attr specified, retrieve the specific part attribute
        value from that projectile object instead.

        Doesn't work for bows because their projectile object varies
        depending on the type of arrow loaded into them."""
        if self.part_MissileWeapon is not None or self.is_specified("part_AmmoArrow"):
            parts = [
                "part_BioAmmoLoader_ProjectileObject",
                "part_AmmoArrow_ProjectileObject",
                "part_MagazineAmmoLoader_ProjectileObject",
                "part_EnergyAmmoLoader_ProjectileObject",
                "part_LiquidAmmoLoader_ProjectileObject",
            ]
            for part in parts:
                attr = getattr(self, part)
                if attr is not None and attr != "":
                    item = self.qindex[attr]
                    if part_attr:
                        return getattr(item, part_attr, None)
                    else:
                        return item
        return None

    def active_or_inactive_character(self) -> int | None:
        """The character type of this object.
        0: NONE 1: ACTIVE_CHARS 2: INACTIVE_CHARS. for ALL_CHARS, do > 0 check.
        TODO: Consider caching this value, as it is used somewhat frequently"""
        if (
            (self.part_Physics_Takeable == "false" or self.part_Physics_Takeable == "False")
            and self.part_Gas is None
            and not self.inherits_from("MeleeWeapon")
            and not self.inherits_from("NaturalWeapon")
            and not self.is_specified("part_MeleeWeapon")
            and not self.inherits_from("MissileWeapon")
            and not self.is_specified("part_MissileWeapon")
        ):
            # This falls under ALL_CHARS
            if self.part_Combat is not None and self.part_Brain is not None:
                return 1  # ACTIVE_CHARS
            else:
                return 2  # INACTIVE_CHARS
        return 0

    def is_melee_weapon(self) -> bool:
        """True if this object can be considered a melee weapon."""
        if self.is_specified("part_MeleeWeapon"):
            return True
        if self.inherits_from("MeleeWeapon"):
            return True
        if self.inheritingfrom == "BaseForkHornedHelmet":
            # special case that should also get melee weapon stat info
            return True
        return False

    # PROPERTIES
    # These properties are the heart of hagadias. They make it easy to access attributes
    # buried in the XML, or which require some computation or translation.
    # Properties all return None implicitly if the property is not applicable to the current item.
    @cached_property
    def accuracy(self) -> int | None:
        """How accurate the gun is."""
        if self.part_MissileWeapon is not None:
            accuracy = self.part_MissileWeapon_WeaponAccuracy
            return 0 if accuracy is None else accuracy  # 0 is default if unspecified

    @cached_property
    def acid(self) -> int | None:
        """The elemental resistance/weakness the equipment or NPC has."""
        return self.resistance("Acid")

    @cached_property
    def agility(self) -> str | None:
        """The agility the mutation affects, or the agility of the creature."""
        return self.attribute_helper("Agility")

    @cached_property
    def agilitymult(self) -> float | None:
        """The stat Bonus multiplier for intrinsic agility, if specified."""
        return self.attribute_boost_factor("Agility")

    @cached_property
    def agilityextrinsic(self) -> int | None:
        """Extra agility for a creature from extrinsic factors, such as mutations or equipment."""
        if self.active_or_inactive_character() == ACTIVE_CHAR:
            if self.mutation:
                for mutation, info in self.mutation.items():
                    if mutation == "HeightenedAgility":
                        return (int(info["Level"]) - 1) // 2 + 2

    @cached_property
    def ammo(self) -> str | None:
        """What type of ammo is used."""
        ammo = None
        if self.part_MagazineAmmoLoader_AmmoPart:
            ammotypes = {
                "AmmoSlug": "lead slug",
                "AmmoShotgunShell": "shotgun shell",
                "AmmoGrenade": "grenade",
                "AmmoMissile": "missile",
                "AmmoArrow": "arrow",
                "AmmoDart": "dart",
            }
            ammo = ammotypes.get(self.part_MagazineAmmoLoader_AmmoPart)
        elif self.part_EnergyAmmoLoader_ChargeUse and int(self.part_EnergyAmmoLoader_ChargeUse) > 0:
            if self.part_EnergyCellSocket and self.part_EnergyCellSocket_SlotType == "EnergyCell":
                ammo = "energy"
            elif self.part_LiquidFueledPowerPlant:
                ammo = self.part_LiquidFueledPowerPlant_Liquid
        elif self.part_LiquidAmmoLoader:
            ammo = self.part_LiquidAmmoLoader_Liquid
        elif self.part_BioAmmoLoader:
            ammo = self.part_BioAmmoLoader_LiquidConsumed
        return ammo

    @cached_property
    def ammodamagetypes(self) -> list | None:
        """Damage attributes associated with the projectile.

        Example: ["Exsanguination", "Disintegrate"] for ProjectileBloodGradientHandVacuumPulse"""
        attributes = self.projectile_object("part_Projectile_Attributes")
        if attributes is not None:
            return attributes.split()
        elif self.part_ElectricalDischargeLoader is not None:
            return "Electric Shock".split()

    @cached_property
    def ammoperaction(self) -> int | None:
        """How much ammo this weapon uses per action. This sometimes differs from the
        shots per action."""
        return self.part_MissileWeapon_AmmoPerAction

    @cached_property
    def animatable(self) -> bool | None:
        """If the thing can be animated using spray a brain or nanoneuro animator."""
        if self.tag_Animatable is not None:
            return True

    @cached_property
    def aquatic(self) -> bool | None:
        """If the creature requires to be submerged in water."""
        if self.inherits_from("Creature"):
            if self.part_Brain_Aquatic is not None:
                return True if self.part_Brain_Aquatic == "true" else False

    @cached_property
    def av(self) -> int | None:
        """The AV that an item provides, or the AV that a creature has."""
        av = None
        if self.part_Armor_AV:  # the AV of armor
            av = self.part_Armor_AV
        if self.part_Shield_AV:  # the AV of a shield
            av = self.part_Shield_AV
        if self.active_or_inactive_character() > 0:
            # the AV of creatures and stationary objects
            try:
                av = int(self.stat_AV_Value)  # first, creature's intrinsic AV
            except TypeError:
                log.error(
                    "%s has no AV value (probably shouldn't be considered an inactive character?)",
                    self.name,
                )
                return None
            applied_body_av = False
            if self.mutation:
                for mutation, info in self.mutation.items():
                    match mutation:
                        case "Carapace":
                            av += int(info["Level"]) // 2 + 3
                            applied_body_av = True
                        case "Quills":
                            av += int(info["Level"]) // 3 + 2
                            applied_body_av = True
                        case "Horns":
                            av += (int(info["Level"]) - 1) // 3 + 1
                        case "MultiHorns":
                            av += (int(info["Level"]) + 1) // 4
                        case "SlogGlands":
                            av += 1
            if self.inventoryobject:
                # might be wearing armor
                for name in list(self.inventoryobject.keys()):
                    if name[0] in "*#@":
                        # special values like '*Junk 1'
                        continue
                    item = self.qindex[name]
                    if item.av and (not applied_body_av or item.wornon != "Body"):
                        av += int(item.av)
        return int_or_none(av)

    @cached_property
    def bits(self) -> str | None:
        """The bits you can get from disassembling the object.

        Example: "0034" for the spiral borer"""
        if self.part_TinkerItem and (
            self.part_TinkerItem_CanDisassemble != "false"
            or self.part_TinkerItem_CanBuild != "false"
        ):
            return self.part_TinkerItem_Bits.translate(BIT_TRANS)

    @cached_property
    def bleedliquid(self) -> str | None:
        """What liquid something bleeds. Only returns interesting liquids (not blood)"""
        robotic = self.part_Roboticized and self.part_Roboticized_ChanceOneIn == "1"
        if self.is_specified("part_BleedLiquid") or robotic:
            liquid = "oil" if robotic else self.part_BleedLiquid.split("-")[0]
            if liquid != "blood":  # it's interesting if they don't bleed blood
                return liquid

    @cached_property
    def bodytype(self) -> str | None:
        """Returns the BodyType tag of the creature."""
        return self.part_Body_Anatomy

    @cached_property
    def butcheredinto(self) -> List[dict] | None:
        """What a corpse item can be butchered into."""
        butcher_obj = self.part_Butcherable_OnSuccess
        if butcher_obj:
            if butcher_obj[:1] == "@":
                if butcher_obj[1:] not in BUTCHERABLE_POPTABLES:
                    log.error("Butcherable poptable %s not recognized.", butcher_obj)
                else:
                    outcomes = []
                    for butcherable, info in BUTCHERABLE_POPTABLES[butcher_obj[1:]].items():
                        outcomes.append({**{"Object": butcherable}, **info})
                    return outcomes
            return [{"Object": butcher_obj, "Number": 1, "Weight": 100}]

    @cached_property
    def canbuild(self) -> bool | None:
        """Whether the player can tinker up this item."""
        if self.part_TinkerItem_CanBuild == "true":
            return True
        elif self.part_TinkerItem_CanDisassemble == "true":
            return False  # it's interesting if an item can't be built but can be disassembled

    @cached_property
    def candisassemble(self) -> bool | None:
        """Whether the player can disassemble this item."""
        if self.part_TinkerItem_CanDisassemble == "true":
            return True
        elif self.part_TinkerItem_CanBuild == "true":
            return False  # it's interesting if an item can't be disassembled but can be built

    @cached_property
    def capacitorcharge(self) -> str | None:
        """If this object has a capacitor, the starting charge range of that capacitor."""
        if self.part_Capacitor is not None:
            return str_or_default(
                self.part_Capacitor_StartCharge, str_or_default(self.part_Capacitor_Charge, "0")
            )

    @cached_property
    def capacitormax(self) -> int | None:
        """If this object has a capacitor, the max charge the capacitor can hold."""
        if self.part_Capacitor is not None:
            return int_or_default(self.part_Capacitor_MaxCharge, 10000)

    @cached_property
    def capacitorrate(self) -> int | None:
        """If this object has a capacitor, the maximum rate of capacitor recharge per turn."""
        if self.part_Capacitor is not None:
            return int_or_default(self.part_Capacitor_ChargeRate, 5)

    @cached_property
    def carrybonus(self) -> int | None:
        """The carry weight bonus."""
        return int_or_none(self.part_Armor_CarryBonus)

    @cached_property
    def chairlevel(self) -> int | None:
        """The level of this chair, used to determine the power of the Sitting effect."""
        if self.part_Chair is not None:
            level = int_or_none(self.part_Chair_Level)
            return 0 if level is None else level

    @cached_property
    def chargeperdram(self) -> int | None:
        """How much charge is available per dram (for liquid-fueled cells or machines)."""
        chargeperdram = int_or_none(self.part_LiquidFueledEnergyCell_ChargePerDram)
        if chargeperdram is not None:
            return chargeperdram
        elif self.part_LiquidFueledPowerPlant is not None:
            chargeperdram = int_or_default(self.part_LiquidFueledPowerPlant_ChargePerDram, 10000)
            return chargeperdram

    @cached_property
    def chargeused(self) -> int | None:
        """How much charge is used for various item functions."""
        charge = 0
        for part in self.all_attributes["part"]:
            if part == "ProgrammableRecoiler":
                continue  # parts ignored or handled elsewhere
            if part == "Teleprojector":
                return int(self.part_Teleprojector_InitialChargeUse) + int(
                    self.part_Teleprojector_MaintainChargeUse
                )
            if part == "ForceProjector":
                return int_or_default(
                    self.part_ForceProjector_ChargePerProjection, 90
                ) + int_or_default(self.part_ForceProjector_BaseOperatingCharge, 1)
            chg = getattr(self, f"part_{part}_ChargeUse")
            if chg is not None and int(chg) > 0:
                charge += int(chg)
        if self.name in HARDCODED_CHARGE_USE:
            charge = HARDCODED_CHARGE_USE[self.name]
        if charge > 0:
            return charge

    @cached_property
    def chargefunction(self) -> str | None:
        """The features or functions that the charge is used for."""
        funcs = []
        detailedfuncs = []
        for part in self.all_attributes["part"]:
            if part == "ProgrammableRecoiler":
                continue  # parts ignored or handled elsewhere
            if part == "Teleprojector":
                return (
                    f"Initiate Domination [{self.part_Teleprojector_InitialChargeUse}], "
                    + f"Maintain Domination [{self.part_Teleprojector_MaintainChargeUse}]"
                )
            if part == "ForceProjector":
                basic = str_or_default(self.part_ForceProjector_BaseOperatingCharge, "1")
                projection = str_or_default(self.part_ForceProjector_ChargePerProjection, "90")
                return f"Basic Operation [{basic}], Per-Tile Projection [{projection}]"
            chg = getattr(self, f"part_{part}_ChargeUse")
            if chg is not None and int(chg) > 0:
                match part:
                    case "StunOnHit":
                        func = "Stun effect"
                    case "EnergyAmmoLoader" | "Gaslight" | "ElectricalDischargeLoader":
                        func = "Weapon Power"
                    case "VibroWeapon":
                        func = "Adaptive Penetration"
                    case "MechanicalWings":
                        func = "Flight"
                    case "RocketSkates":
                        func = "Power Skate"
                    case "GeomagneticDisc":
                        func = "Throw Effect"
                    case "Teleporter":
                        func = "Teleportation"
                    case "EquipStatBoost":
                        func = "Stat Boost"
                    case "PartsGas":
                        func = "Gas Dispersion"
                    case "ReduceCooldowns":
                        func = "Cooldown Reduction"
                    case "RealityStabilization":
                        func = "Reality Stabilization"
                    case "LatchesOn":
                        func = "Latch Effect"
                    case "Toolbox":
                        func = "Tinker Bonus"
                    case "ConversationScript":
                        func = "Audio Processing"
                    case _:
                        if getattr(self, f"part_{part}_NameForStatus") is not None:
                            func = getattr(self, f"part_{part}_NameForStatus")
                        elif part == "Chair":  # handle chairs without a NameForStatus
                            func = "Chair Effect"
                        else:
                            func = part  # default to part name if no other match
                if func is not None:
                    funcs.append(func)
                    detailedfuncs.append(func + " [" + chg + "]")
        if self.name in CHARGE_USE_REASONS:
            func = CHARGE_USE_REASONS[self.name]
            funcs.append(func)
            if self.name in HARDCODED_CHARGE_USE:
                detailedfuncs.append(f"{func} [{HARDCODED_CHARGE_USE[self.name]}]")
            else:
                detailedfuncs.append(func)
        if len(funcs) == 0:
            return None
        elif len(funcs) == 1:
            return funcs[0]  # if only one function, return the simple name
        else:
            return ", ".join(detailedfuncs)  # if multiple, return names with charge amount appended

    @cached_property
    def chargeconsumebroadcast(self) -> int | None:
        """If this object consumes charge from broadcast power, the max amount of charge
        it can potentially consume per turn."""
        if self.part_BroadcastPowerReceiver is not None:
            return int_or_default(self.part_BroadcastPowerReceiver_ChargeRate, 10)

    @cached_property
    def chargeconsumeelectrical(self) -> int | None:
        """If this object consumes charge from electric grids, the max amount of charge
        it can potentially consume per turn."""
        if self.part_ElectricalPowerTransmission_IsConsumer == "true":
            return int_or_default(self.part_ElectricalPowerTransmission_ChargeRate, 500)

    @cached_property
    def chargeconsumehydraulic(self) -> int | None:
        """If this object consumes charge from hydraulic grids, the max amount of charge
        it can potentially consume per turn."""
        if self.part_HydraulicPowerTransmission_IsConsumer == "true":
            return int_or_default(self.part_HydraulicPowerTransmission_ChargeRate, 2000)

    @cached_property
    def chargeconsumemechanical(self) -> int | None:
        """If this object consumes mechanical power, the max amount of charge
        it can potentially consume per turn."""
        if self.part_MechanicalPowerTransmission_IsConsumer == "true":
            return int_or_default(self.part_MechanicalPowerTransmission_ChargeRate, 100)

    @cached_property
    def chargeproducebroadcast(self) -> bool | None:
        """True if this object acts as a broadcast power source"""
        if self.part_BroadcastPowerTransmitter is not None:
            return True

    @cached_property
    def chargeproduceelectric(self) -> int | None:
        """If this object produces electric power, the amount of charge it produces per turn."""
        if self.part_ElectricalPowerTransmission_IsProducer == "true":
            return int_or_default(self.part_ElectricalPowerTransmission_ChargeRate, 500)

    @cached_property
    def chargeproducehydraulic(self) -> int | None:
        """If this object produces hydraulic power, the amount of charge it produces per turn."""
        if self.part_HydraulicPowerTransmission_IsProducer == "true":
            return int_or_default(self.part_HydraulicPowerTransmission_ChargeRate, 2000)

    @cached_property
    def chargeproducemechanical(self) -> int | None:
        """If this object produces mechanical power, the amount of charge it produces per turn."""
        if self.part_MechanicalPowerTransmission_IsProducer == "true":
            return int_or_default(self.part_MechanicalPowerTransmission_ChargeRate, 100)

    @cached_property
    def chargeproducesolar(self) -> int | None:
        """If this object has a solar array, the amount of solar energy it produces per turn."""
        if self.part_SolarArray is not None:
            return int_or_default(self.part_SolarArray_ChargeRate, 10)

    @cached_property
    def cold(self) -> int | None:
        """The elemental resistance/weakness the equipment or NPC has."""
        return self.resistance("Cold")

    @cached_property
    def colorstr(self) -> str | None:
        """The Qud color code associated with the RenderString."""
        if self.part_Render_ColorString:
            return self.part_Render_ColorString
        if self.part_Gas_ColorString:
            return self.part_Gas_ColorString

    @cached_property
    def commerce(self) -> float | None:
        """The value of the object."""
        if self.inherits_from("Item") or self.inherits_from("BaseThrownWeapon"):
            value = self.part_Commerce_Value
            if value is not None:
                return float(value)

    @cached_property
    def complexity(self) -> int | None:
        """The complexity of the object, used for psychometry."""
        if self.part_Examiner_Complexity is None:
            val = 0
        else:
            val = int(self.part_Examiner_Complexity)
        if self.part_AddMod_Mods is not None:
            modprops = ITEM_MOD_PROPS
            for mod in self.part_AddMod_Mods.split(","):
                if mod in modprops:
                    if (modprops[mod]["ifcomplex"] is True) and (val <= 0):
                        continue  # no change because the item isn't already complex
                    val += int(modprops[mod]["complexity"])
        for key in self.part.keys():
            if key.startswith("Mod"):
                modprops = ITEM_MOD_PROPS
                if key in modprops:
                    if (modprops[key]["ifcomplex"] is True) and (val <= 0):
                        continue  # ditto
                    val += int(modprops[key]["complexity"])
        if val > 0 or self.canbuild:
            return val

    @cached_property
    def cookeffect(self) -> list | None:
        """The possible cooking effects of an item."""
        ingred_type = self.part_PreparedCookingIngredient_type
        if ingred_type is not None:
            return ingred_type.split(",")

    @cached_property
    def corpse(self) -> str | None:
        """What corpse a character drops."""
        if (
            self.part_Corpse_CorpseBlueprint is not None
            and int(self.part_Corpse_CorpseChance) > 0
            and (self.part_Roboticized is None or self.part_Roboticized_ChanceOneIn != "1")
        ):
            return self.part_Corpse_CorpseBlueprint

    @cached_property
    def corpsechance(self) -> int | None:
        """The chance of a corpse dropping, if corpsechance is >0"""
        chance = self.part_Corpse_CorpseChance
        if (
            chance is not None
            and int(chance) > 0
            and (self.part_Roboticized is None or self.part_Roboticized_ChanceOneIn != "1")
        ):
            return int(chance)

    @cached_property
    def cursed(self) -> bool | None:
        """If the item cannot be removed by normal circumstances."""
        if self.part_Cursed is not None:
            return True

    @cached_property
    def damage(self) -> str | None:
        """The damage dealt by this object. Often a dice string."""
        val = None
        if self.is_melee_weapon():
            val = self.part_MeleeWeapon_BaseDamage
        if self.part_Gaslight:
            val = self.part_Gaslight_ChargedDamage
        if self.part_ThrownWeapon is not None:
            if self.is_specified("part_GeomagneticDisc"):
                val = self.part_GeomagneticDisc_Damage
            else:
                val = self.part_ThrownWeapon_Damage
                if val is None:
                    val = 1  # default damage for ThrownWeapon
        projectiledamage = self.projectile_object("part_Projectile_BaseDamage")
        if projectiledamage:
            val = projectiledamage
        if self.part_ElectricalDischargeLoader is not None:
            chargefactor = int_or_default(self.part_ElectricalDischargeLoader_ChargeFactor, 15)
            chargebasis = int_or_default(self.part_ElectricalDischargeLoader_ChargeUse, 300)
            dicecount = (chargefactor * chargebasis) // 1000
            val = f"{dicecount}d4"
        return val

    @cached_property
    def demeanor(self) -> str | None:
        """The demeanor of the creature."""
        if self.active_or_inactive_character() == ACTIVE_CHAR:
            if self.part_Brain_Calm is not None:
                return "docile" if self.part_Brain_Calm.lower() == "true" else "neutral"
            if self.part_Brain_Hostile is not None:
                return "aggressive" if self.part_Brain_Hostile.lower() == "true" else "neutral"

    @cached_property
    def desc(self) -> str | None:
        """The short description of the object, with color codes included (ampersands escaped)."""
        desc_txt = self.part_Description_Short

        # Handle empty descriptions first
        if desc_txt is None or len(desc_txt) < 1:
            if self.name[-7:] == " Cherub":
                is_mechanical = self.name[:11] == "Mechanical "
                txt = MECHANICAL_CHERUBIM_DESC if is_mechanical else CHERUBIM_DESC
                skintype = str_or_default(self.xtag_TextFragments_Skin, "skin")
                creaturetype = str_or_default(
                    self.tag_AlternateCreatureType_Value,
                    self.displayname.split()[1 if is_mechanical else 0],
                )
                features = self.xtag_TextFragments_PoeticFeatures.split(",")
                if is_mechanical:
                    features = "{}, and {}".format(", ".join(features[:-1]), features[-1])
                else:
                    features = "the {}".format(", the ".join(features))
                return (
                    txt.replace("*skin*", skintype)
                    .replace("*creatureType*", creaturetype)
                    .replace("*features*", features)
                )
            else:
                # Should be rare because most things without a descrip inherit 'A hideous specimen.'
                return None

        # TODO: Refactor or break into a separate file.
        # Note that the order of description rules below is meaningful - it attempts to do the
        # best job possible mimicking the order of rules on items in game. It is not perfect,
        # however. To perfectly represent everything, we would need to actually iterate over the
        # object's parts in XML order (and output associated rules in that same order)

        desc_extra = []
        is_item = False
        if self.inherits_from("Item"):  # append resistances, attributes, and other rules text
            is_item = True
            # reputation
            if self.part_AddsRep is not None:
                factions = self.part_AddsRep_Faction.split(",")
                rep_value = self.part_AddsRep_Value
                for faction in factions:
                    amt = rep_value
                    if ":" in faction:
                        vals = faction.split(":")
                        amt = vals[1]
                        faction = vals[0]
                    if amt[0] not in ["+", "-"]:
                        amt = f"+{amt}"
                    if faction == "*allvisiblefactions":
                        txt = f"{amt} reputation with every faction"
                    else:
                        if faction in FACTION_ID_TO_NAME:
                            faction = FACTION_ID_TO_NAME[faction]
                        txt = f"{amt} reputation with {faction}"
                    desc_extra.append("{{rules|" + txt + "}}")
            # missile weapon rules
            if self.part_MissileWeapon is not None:
                skill = str_or_default(self.part_MissileWeapon_Skill, "Rifle")
                if skill == "Rifle":
                    skill = "Bows & Rifles"
                elif skill == "HeavyWeapons":
                    skill = "Heavy Weapon"
                accuracy = int_or_default(self.part_MissileWeapon_WeaponAccuracy, 0)
                accuracy_str = "Very Low"
                if accuracy <= 0:
                    accuracy_str = "Very High"
                elif accuracy < 5:
                    accuracy_str = "High"
                elif accuracy < 10:
                    accuracy_str = "Medium"
                elif accuracy < 25:
                    accuracy_str = "Low"
                ammoper = int_or_default(self.part_MissileWeapon_AmmoPerAction, 1)
                shotsper = int_or_default(self.part_MissileWeapon_ShotsPerAction, 1)
                showshots = bool_or_default(self.part_MissileWeapon_bShowShotsPerAction, True)
                nowildfire = bool_or_default(self.part_MissileWeapon_NoWildfire, False)
                penstat = self.part_MissileWeapon_ProjectilePenetrationStat
                txt = "{{rules|"
                txt += f"Weapon Class: {skill}"
                txt += f"\nAccuracy: {accuracy_str}"
                if ammoper > 1:
                    txt += f"\nMultiple ammo used per shot: {ammoper}"
                if showshots and shotsper > 1:
                    txt += f"\nMultiple projectiles per shot: {shotsper}"
                if nowildfire:
                    txt += (
                        "\nSpray fire: This item can be fired while adjacent to multiple "
                        + "enemies without risk of the shot going wild."
                    )
                if skill == "Heavy Weapon":
                    txt += "\n-25 move speed"
                if penstat:
                    txt += (
                        "\nProjectiles fired with this weapon receive bonus penetration "
                        + f"based on the wielder's {penstat}."
                    )
                txt += "}}"
                desc_extra.append(txt)
            # resists
            resists = []
            # attributes [positiveColor, negativeColor, isResistance]
            attrs = {
                "heat": ["R", "R", True],
                "cold": ["C", "C", True],
                "electrical": ["W", "W", True],
                "acid": ["G", "G", True],
                "willpower": ["C", "R", False],
                "ego": ["C", "R", False],
                "agility": ["C", "R", False],
                "toughness": ["C", "R", False],
                "strength": ["C", "R", False],
                "intelligence": ["C", "R", False],
                "quickness": ["C", "R", False],
                "movespeedbonus": ["C", "R", False],
            }
            for attr in attrs:
                resist = getattr(self, f"{attr}")
                if resist:
                    if self.name in ["Stopsvaalinn", "Ruin of House Isner"] and attr == "ego":
                        continue  # These items' ego bonus is already displayed in their rule text
                    if self.name == "Cyclopean Prism":  # special handling for amaranthine prism
                        if attr == "ego":
                            resist = "+1"
                        elif attr == "willpower":
                            resist = "-1"
                    if str(resist)[0] not in ["+", "-"]:
                        resist_str = f"{pos_or_neg(resist)}{resist}"
                    else:
                        resist_str = str(resist)
                    attr_name = attr if attr != "movespeedbonus" else "move speed"
                    attr_color = attrs[attr][0] if resist_str[0] != "-" else attrs[attr][1]
                    resist_str = (
                        f"{resist_str} "
                        + attr_name.title()
                        + (" Resistance" if attrs[attr][2] is True else "")
                    )
                    resists.append(f"{{{{{attr_color}|{resist_str}}}}}")
            if len(resists) > 0:
                desc_extra.append("\n".join(resists))
            # EquipStatBoost attributes
            if self.part_EquipStatBoost_Boosts is not None:
                for boostinfo in self.part_EquipStatBoost_Boosts.split(";"):
                    stat, amt = boostinfo.split(":")
                    stat = stat if stat not in STAT_DISPLAY_NAMES else STAT_DISPLAY_NAMES[stat]
                    amt = int_or_none(amt)
                    if amt is not None:
                        symbol = "+" if amt > 0 else ""
                        desc_extra.append("{{" + f"rules|{symbol}{amt} {stat}" + "}}")
            # carrybonus
            carry_bonus = self.carrybonus
            if carry_bonus:
                if carry_bonus > 0:
                    carry_bonus = f"+{carry_bonus}"
                desc_extra.append("{{rules|" + carry_bonus + "% carry capacity}}")
            # armor rules
            if self.part_Armor is not None:
                # most armor bonuses are handled in attr block above, but MA needs special
                # handling, because we want to show its bonus in the description only for Armor
                if self.part_Armor_MA is not None:
                    desc_extra.append("{{rules|+" + self.part_Armor_MA + " MA}}")
                if self.part_Armor_ToHit is not None:
                    tohit = int(self.part_Armor_ToHit)
                    if tohit > 0:
                        desc_extra.append("{{rules|+" + tohit + " To-Hit}}")
                    else:
                        desc_extra.append(f"{{{{R|{tohit} To-Hit}}}}")
            # melee weapon rules
            if (
                self.is_melee_weapon()
                and self.tag_ShowMeleeWeaponStats is not None
                and not self.inherits_from("Projectile")
            ):
                # technically these stats are also shown for projectiles in game, but it seems
                # prudent to carve out an exception for wiki - feels misleading to show "Weapon
                # Class: Cudgel (dazes on critical hits)" in every wiki arrow description...
                weapon_stat = str_or_default(self.part_MeleeWeapon_Stat, "Strength")
                rule_lines = []
                # Ego bonus (part_MeleeWeapon_Ego) is already handled in the attr section above
                tohit = self.part_MeleeWeapon_HitBonus
                if tohit is not None and int(tohit) > 0:
                    rule_lines.append(f"+{tohit} To-Hit")
                maxpv = self.maxpv
                pv = self.pv
                if maxpv is not None and pv is not None and maxpv > pv:
                    if maxpv == 999:
                        rule_lines.append(f"{weapon_stat} Bonus Cap: no limit")
                    else:
                        rule_lines.append(f"{weapon_stat} Bonus Cap: {maxpv - pv}")
                skill = str_or_default(self.part_MeleeWeapon_Skill, "Cudgel")
                if skill == "Cudgel":
                    skill = "Cudgel (dazes on critical hit)"
                elif skill == "LongBlades":
                    skill = "Long Blades (increased penetration on critical hit)"
                elif skill == "ShortBlades":
                    skill = "Short Blades (causes bleeding on critical hit)"
                elif skill == "Axe":
                    skill = "Axe (cleaves armor on critical hit)"
                else:
                    skill = None
                if skill is not None:
                    rule_lines.append(f"Weapon Class: {skill}")
                if self.part_ElementalDamage is not None:
                    dmg = self.part_ElementalDamage_Damage
                    dmg = dmg if dmg is not None else "1d4"
                    typ = self.part_ElementalDamage_Attributes
                    typ = typ if typ is not None else "Heat"
                    chc = self.part_ElementalDamage_Chance
                    chc = int(chc) if chc is not None else 100
                    txt = f"Causes {dmg} {typ.lower()} damage on hit"
                    txt += "." if chc >= 100 else f" {chc}% of the time."
                    rule_lines.append(txt)
                if len(rule_lines) > 0:
                    desc_extra.append("{{rules|" + "\n".join(rule_lines) + "}}")
            # HornsProperties
            if self.part_HornsProperties is not None:
                level = int_or_default(self.part_HornsProperties_HornLevel, 1)
                damage = "1"
                if level > 3:
                    damage += "d2"
                    if level > 6:
                        damage += f"+{(level - 4) // 3}"
                savetarget = 20 + 3 * level
                desc_extra.append(
                    "{{rules|On penetration, this weapon causes bleeding: "
                    + f"{damage} damage per round, save difficulty {savetarget}"
                    + "}}"
                )
            # light-related effects
            if self.part_ModGlassArmor_Tier is not None:
                desc_extra.append(
                    "{{rules|"
                    + f"Reflects {self.part_ModGlassArmor_Tier}% damage "
                    + "back at your attackers, rounded up.}}"
                )
            if self.part_FlareCompensation is not None:
                shouldshow = self.part_FlareCompensation_ShowInShortDescription
                if shouldshow is None or shouldshow.lower() == "true":
                    desc_extra.append("{{rules|Offers protection against visual flash effects.}}")
            if self.part_RefractLight is not None:
                shouldshow = self.part_RefractLight_ShowInShortDescription
                if shouldshow is not None and shouldshow.lower() == "true":
                    chance = int_or_default(self.part_RefractLight_Chance)
                    variance = self.part_RefractLight_RetroVariance
                    txt = f"Has a {chance}% chance to refract light-based attacks, sending them "
                    if variance is None:
                        txt += "in a random direction."
                    else:
                        dice = DiceBag(variance)
                        dmin = dice.minimum()
                        dmax = dice.maximum()
                        if dmin == 0 and dmax == 0:
                            txt += "back the way they came."
                        else:
                            txt += f"back the way they came, plus or minus up to {dmax} degrees."
                    desc_extra.append("{{rules|" + txt + "}}")
            # shields
            if self.part_Shield is not None:
                desc_extra.append(
                    "{{rules|Shields only grant their AV when you "
                    + "successfully block an attack.}}"
                )
            # compute nodes
            if self.part_ComputeNode is not None:
                if self.part_ComputeNode_WorksOnEquipper == "true":
                    power = self.part_ComputeNode_Power
                    power = "20" if power is None else power
                    desc_extra.append(
                        "{{rules|When equipped and powered, provides "
                        + power
                        + " units of compute power to the local lattice.}}"
                    )
            # active light source
            if self.part_ActiveLightSource is not None:
                if self.part_ActiveLightSource_WorksOnEquipper == "true":
                    if (
                        self.part_ActiveLightSource_ShowInShortDescription is None
                        or self.part_ActiveLightSource_ShowInShortDescription == "true"
                    ):
                        radius = self.part_ActiveLightSource_Radius
                        radius = "5" if radius is None else radius
                        desc_extra.append(
                            "{{rules|When equipped, provides light in radius " + radius + ".}}"
                        )
            # add item-specific rules text, if applicable
            if self.name == "Rocket Skates":
                rule1 = "Replaces Sprint with Power Skate (unlimited duration)."
                rule2 = "Emits plumes of fire when the wearer moves while power skating."
                desc_extra.append("{{rules|" + rule1 + "}}")
                desc_extra.append("{{rules|" + rule2 + "}}")
            elif self.name == "Banner of the Holy Rhombus":
                desc_extra.append(
                    "{{rules|Bestows the {{r|war trance}} effect to the"
                    + " Putus Templar who can see this item."
                )
            # add rules text for save modifier, if applicable
            if self.part_SaveModifier is not None:
                if (
                    self.part_SaveModifier_ShowInShortDescription is None
                    or self.part_SaveModifier_ShowInShortDescription == "true"
                ):
                    amt = self.part_SaveModifier_Amount
                    amt = "1" if amt is None else amt
                    amt = amt if amt[:1] == "-" else f"+{amt}"
                    vs = self.part_SaveModifier_Vs
                    save_mod_str = f"{amt} on saves"
                    if vs is not None and vs != "":
                        save_mod_str += f' vs. {make_list_from_words(vs.split(","))}'
                    desc_extra.append("{{rules|" + save_mod_str + ".}}")
            # add rules text for point defense compute power
            if self.part_PointDefense is not None:
                val = float_or_default(self.part_PointDefense_ComputePowerFactor, 1.0)
                if val != 0.0:
                    desc_extra.append(
                        "{{rules|Compute power on the local lattice "
                        + ("decreases" if val < 0.0 else "increases")
                        + " this item's effectiveness.}}"
                    )
            # add rules text for bioloading compute power
            if self.part_BioAmmoLoader_TurnsToGenerateComputePowerFactor is not None:
                val = float_or_none(self.part_BioAmmoLoader_TurnsToGenerateComputePowerFactor)
                if val is not None and val != 0.0:
                    desc_extra.append(
                        "{{rules|Compute power on the local lattice "
                        + ("decreases" if val > 0.0 else "increases")
                        + " the"
                        + " time needed for this item to generate ammunition.}}"
                    )
            # mutation rules text
            if self.part_ModImprovedConfusion is not None:
                val = int_or_none(self.part_ModImprovedConfusion_Tier)
                if val is not None and val > 0:
                    desc_extra.append(
                        "{{rules|Grants you Confusion at level "
                        + str(val)
                        + ". "
                        + "If you already have Confusion, its level is increased by "
                        + str(val)
                        + ".}}"
                    )
            # gas tumbler
            if self.part_GasTumbler is not None:
                dispersalmod = int_or_default(self.part_GasTumbler_DispersalMultiplier, 25) - 100
                densitymod = int_or_default(self.part_GasTumbler_DensityMultiplier, 200) - 100
                pos = True if densitymod >= 0 else False
                densitystr = (
                    "Gases you release are "
                    + str(densitymod if pos else -densitymod)
                    + ("% denser." if pos else "% less dense.")
                )
                pos = True if dispersalmod >= 0 else False
                dispersalstr = (
                    "Gases you release disperse "
                    + str(dispersalmod if pos else -dispersalmod)
                    + ("% faster." if pos else "% slower.")
                )
                desc_extra.append("{{rules|" + f"{densitystr}\n{dispersalstr}" + "}}")
            # thermal amp
            if self.part_ThermalAmp is not None:
                heatdam = int_or_default(self.part_ThermalAmp_HeatDamage, 0)
                colddam = int_or_default(self.part_ThermalAmp_ColdDamage, 0)
                heatmod = int_or_default(self.part_ThermalAmp_ModifyHeat, 0)
                coldmod = int_or_default(self.part_ThermalAmp_ModifyCold, 0)
                if heatdam != 0 or colddam != 0 or heatmod != 0 or coldmod != 0:
                    txt = ""
                    if heatdam != 0:
                        txt += (
                            f'{"{{R|+" if heatdam > 0 else "{{r|-"}{heatdam}% '
                            + "heat damage dealt}}\n"
                        )
                    if colddam != 0:
                        txt += (
                            f'{"{{C|+" if colddam > 0 else "{{c|-"}{colddam}% '
                            + "cold damage dealt}}\n"
                        )
                    if heatmod != 0:
                        txt += (
                            f'{"{{R|+" if heatmod > 0 else "{{r|-"}{heatmod}% '
                            + "to the intensity of your heating effects}}\n"
                        )
                    if coldmod != 0:
                        txt += (
                            f'{"{{C|+" if coldmod > 0 else "{{c|-"}{coldmod}% '
                            + "to the intensity of your cooling effects}}\n"
                        )
                    desc_extra.append(txt[:-1])  # remove trailing line break
            if self.part_SlipRing is not None:
                savebonus = int_or_default(self.part_SlipRing_SaveBonus, 15)
                activationchance = int_or_default(self.part_SlipRing_ActivationChance, 5)
                desc_extra.append(
                    "{{rules|"
                    + f"+{savebonus} to saves vs. being grabbed\n"
                    + f"+{activationchance}% chance to slip away from natural melee"
                    + " attacks}}"
                )
            if self.part_Cursed_RevealInDescription == "true":
                desc_extra.append(
                    "{{rules|"
                    + str_or_default(
                        self.part_Cursed_DescriptionPostfix, "Cannot be removed once equipped."
                    )
                    + "}}"
                )
        # signs
        if self.part_Chat_ShowInShortDescription == "true":
            says = self.part_Chat_Says
            if says is not None and len(says) > 0:
                if says[0] == "[":
                    says = says.replace("[", "").replace("]", "")
                    desc_extra.append(f"It bears {says}")
                else:
                    desc_extra.append(f"It reads, '{says}'.")
        if self.part_MoltingBasilisk is not None:
            desc_txt = (
                "The basilisk is nature's statue; its scaled skin is the color of dull"
                + " quartz and it strikes as still a pose as an artist's mould."
            )
        if self.part_Roboticized and self.part_Roboticized_ChanceOneIn == "1":
            desc_postfix = (
                "There is a low, persistent hum emanating outward."
                if not self.part_Roboticized_DescriptionPostfix
                else self.part_Roboticized_DescriptionPostfix
            )
            desc_txt += f" {desc_postfix}"
        if self.part_PartsGas is not None:
            chance = self.part_PartsGas_Chance
            if chance is not None:
                rule = f"{chance}% chance per turn to repel gases near its"
            else:
                rule = "Repels gases near its"
            if is_item:
                rule += " wielder or wearer." if self.name == "Wrist Fan" else " user."
            else:
                rule += "elf."
            desc_extra.append("{{rules|" + rule + "}}")
        if self.intproperty_GenotypeBasedDescription:
            desc_extra.append(f"[True kin]\n{self.property_TrueManDescription_Value}")
            desc_extra.append(f"[Mutant]\n{self.property_MutantDescription_Value}")
        # cybernetics infixes
        cybernetic_rules = "{{rules|"
        for part in CYBERNETICS_HARDCODED_INFIXES:
            if self.is_specified(f"part_{part}"):
                cybernetic_rules += f"{CYBERNETICS_HARDCODED_INFIXES[part]}\n\n"
                break
        # BehaviorDescriptions (predominantly cybernetics, but also includes some other items)
        for part in BEHAVIOR_DESCRIPTION_PARTS:
            if self.is_specified(f"part_{part}"):
                behavior_desc = getattr(self, f"part_{part}_BehaviorDescription")
                if behavior_desc is not None and behavior_desc != "":
                    cybernetic_rules += behavior_desc
        # additional cybernetics postfixes
        if self.part_CyberneticsBaseItem_Slots is not None:
            body_parts = self.part_CyberneticsBaseItem_Slots
            body_parts = body_parts.replace(",", ", ")
            cost = self.part_CyberneticsBaseItem_Cost
            if len(desc_extra) > 0 or len(cybernetic_rules) > len("{{rules|"):
                cybernetic_rules += "\n\n"
            txt = ""
            if self.tag_CyberneticsDestroyOnRemoval is not None:
                txt += "Destroyed when uninstalled.\n"
            txt += f"Target body parts: {body_parts}\n"
            txt += f"License points: {cost}\n"
            txt += "Only compatible with True Kin genotypes"
            for part in CYBERNETICS_HARDCODED_POSTFIXES:
                if self.is_specified(f"part_{part}"):
                    txt += f"\n{CYBERNETICS_HARDCODED_POSTFIXES[part]}"
                    break
            cybernetic_rules += txt + "}}"
        # append rules if we found any
        if len(cybernetic_rules) > len("{{rules|"):
            desc_extra.append(cybernetic_rules)
        if self.part_RulesDescription:
            if self.part_RulesDescription_AltForGenotype == "True Kin":
                desc_extra.append(f"[Mutant]\n{{{{rules|{self.part_RulesDescription_Text}}}}}")
                desc_extra.append(
                    "[True Kin]\n{{rules|" + self.part_RulesDescription_GenotypeAlt + "}}"
                )
            else:
                desc_extra.append(f"{{{{rules|{self.part_RulesDescription_Text}}}}}")
        if self.part_AddsTelepathyOnEquip is not None:
            desc_extra.insert(0, "{{rules|Grants you Telepathy.}}")
        if self.part_ReduceEnergyCosts and (
            self.part_ReduceEnergyCosts_GenerateShortDescription is None
            or self.part_ReduceEnergyCosts_GenerateShortDescription == "true"
        ):
            num = int(self.part_ReduceEnergyCosts_PercentageReduction)
            pre = "" if (int(self.part_ReduceEnergyCosts_ChargeUse) == 0) else "when powered, "
            temp = (
                f"{pre}provides {num}% reduction in "
                f"{self.part_ReduceEnergyCosts_ScopeDescription}."
            )
            desc_extra.append("{{rules|" + temp[0].upper() + temp[1:] + "}}")
        if self.part_Description_Mark:
            desc_extra.append(self.part_Description_Mark)
        if self.part_BonusPostfix is not None:
            desc_extra.append(self.part_BonusPostfix_Postfix)

        # Finalize the description:
        if len(desc_extra) > 0:
            desc_txt += "\n\n" + "\n".join(desc_extra)
        desc_txt = desc_txt.replace("\r\n", "\n")  # currently, only the description for Bear

        return desc_txt

    @cached_property
    def destroyonunequip(self) -> bool | None:
        """If the object is destroyed on unequip."""
        if self.part_DestroyOnUnequip is not None:
            return True

    @cached_property
    def displayname(self) -> str | None:
        """The display name of the object, with color codes removed. Used in UI and wiki."""
        dname = ""
        if self.part_Render_DisplayName is not None:
            dname = self.part_Render_DisplayName
            dname = strip_oldstyle_qud_colors(dname)
            dname = strip_newstyle_qud_colors(dname)
        return dname

    @cached_property
    def dramsperuse(self) -> int | float | None:
        """The number of drams of liquid consumed by each shot action."""
        if self.is_specified("part_LiquidAmmoLoader"):
            return 1  # LiquidAmmoLoader always uses 1 dram per action
        elif self.is_specified("part_BioAmmoLoader"):
            val = int_or_none(self.part_BioAmmoLoader_ConsumeAmount)
            val = 1 if val is None else val
            chance = float_or_none(self.part_BioAmmoLoader_ConsumeChance)
            if chance is not None:
                return chance / 100.0 * float(val)
            return val

    @cached_property
    def dv(self) -> int | None:
        """The Dodge Value of this object."""
        dv = None
        if self.part_Armor_DV is not None:  # the DV of armor
            dv = int(self.part_Armor_DV)
        if self.part_Shield_DV is not None:  # the DV of a shield
            dv = int(self.part_Shield_DV)
        elif (char_type := self.active_or_inactive_character()) == INACTIVE_CHAR:
            dv = -10
        elif char_type == ACTIVE_CHAR:
            # the 'DV' here is the actual DV of the creature or NPC, after:
            # base of 6 plus any explicit DV bonus,
            # skills, agility modifier (which may be a range determined by
            # dice rolls, and which changes DV by 1 for every 2 points of agility
            # over/under 16), and any equipment that is guaranteed to be worn
            if self.is_specified("part_Brain_Mobile") and (
                self.part_Brain_Mobile == "false" or self.part_Brain_Mobile == "False"
            ):
                dv = -10
            else:
                dv = 6
                if self.stat_DV_Value is not None:
                    dv += int(self.stat_DV_Value)
                if self.skill_Acrobatics_Dodge:  # the 'Spry' skill
                    dv += 2
                if self.skill_Acrobatics_Tumble:  # the 'Tumble' skill
                    dv += 1
                dv += self.attribute_helper_mod("Agility")
                applied_body_dv = False
                # does this creature have mutations that affect DV?
                if self.mutation:
                    for mutation, info in self.mutation.items():
                        if mutation == "Carapace":
                            dv -= 2
                            applied_body_dv = True
                # does this creature have armor with DV modifiers to add?
                if self.inventoryobject:
                    for name in list(self.inventoryobject.keys()):
                        if name[0] in "*#@":
                            # special values like '*Junk 1'
                            continue
                        item = self.qindex[name]
                        if item.dv and (not applied_body_dv or item.wornon != "Body"):
                            dv += item.dv
        return int_or_none(dv)

    @cached_property
    def dynamictable(self) -> list | None:
        """What dynamic tables the object is a member of.

        Returns a list of strings, the dynamic tables."""
        if self.tag_ExcludeFromDynamicEncounters is not None:
            return None
        tables = []
        for key, val in self.tag.items():
            if key.startswith("DynamicObjectsTable"):
                if "Value" in val and val["Value"] == "{{{remove}}}":
                    continue  # explicitly disallowed from an inherited dynamic table
                tables.append(key.split(":")[1])
        return list(set(tables)) if len(tables) > 0 else None

    @cached_property
    def eatdesc(self) -> str | None:
        """The text when you eat this item."""
        return self.part_Food_Message

    @cached_property
    def ego(self) -> str | None:
        """The creature's ego stat or the ego bonus supplied by a piece of equipment."""
        if self.name in ["Stopsvaalinn", "Ruin of House Isner"]:
            return "1"
        val = self.attribute_helper("Ego")
        if val is None and self.is_melee_weapon():
            val = self.part_MeleeWeapon_Ego
        return f"{val}+3d1" if self.name == "Wraith-Knight Templar" else val

    @cached_property
    def egomult(self) -> float | None:
        """The stat Bonus multiplier for intrinsic ego, if specified."""
        return self.attribute_boost_factor("Ego")

    @cached_property
    def egoextrinsic(self) -> int | None:
        """Extra ego for a creature from extrinsic factors, such as mutations or equipment."""
        if self.active_or_inactive_character() == ACTIVE_CHAR:
            if self.mutation and "Beak" in self.mutation.keys():
                return 1

    @cached_property
    def electric(self) -> int | None:
        """The elemental resistance/weakness the equipment or NPC has."""
        return self.resistance("Electric")

    @cached_property
    def electrical(self) -> int | None:
        """The elemental resistance/weakness the equipment or NPC has.
        *egocarib 10/4/2020 - I am pretty sure this property is unused, but leaving it here
         just in case. Most things use 'electric' since that is our wiki template field name"""
        return self.resistance("Electric")

    @cached_property
    def elementaldamage(self) -> str | None:
        """The elemental damage dealt, if any, as a range."""
        if self.is_specified("part_ModFlaming"):
            tierstr = self.part_ModFlaming_Tier
            elestr = str(int(int(tierstr) * 0.8)) + "-" + str(int(int(tierstr) * 1.2))
        elif self.is_specified("part_ModFreezing"):
            tierstr = self.part_ModFreezing_Tier
            elestr = str(int(int(tierstr) * 0.8)) + "-" + str(int(int(tierstr) * 1.2))
        elif self.is_specified("part_ModElectrified"):
            tierstr = self.part_ModElectrified_Tier
            elestr = str(int(tierstr)) + "-" + str(int(int(tierstr) * 1.5))
        else:
            elestr = self.part_ElementalDamage_Damage
        return elestr

    @cached_property
    def elementaltype(self) -> str | None:
        """For elemental damage dealt, what the type of that damage is."""
        if self.is_specified("part_ModFlaming"):
            elestr = "Fire"
        elif self.is_specified("part_ModFreezing"):
            elestr = "Cold"
        elif self.is_specified("part_ModElectrified"):
            elestr = "Electric"
        else:
            elestr = self.part_ElementalDamage_Attributes
        return elestr

    @cached_property
    def empsensitive(self) -> bool | None:
        """Returns yes if the object is EMP-sensitive. This typically means that some feature of
        the object does not function as expected while pulsed by an EMP effect.
        Note that the game will show an "[EMP]" tag in the display name of more things than are
        actually empsensitive, including anything metal or robotic (like an iron long sword)."""
        all_parts = getattr(self, "part")
        if all_parts is not None:
            emp_sensitive = None
            # object is emp sensitive if any single part on the object is emp sensitive:
            for partname, partattribs in all_parts.items():
                if partname in ACTIVE_PARTS:
                    if partname == "ModHardened":
                        return None  # ModHardened overrides anything else, so we return early
                    if partattribs.get("IsEMPSensitive", ACTIVE_PARTS[partname]["IsEMPSensitive"]):
                        emp_sensitive = True
            return emp_sensitive

    @cached_property
    def enclosing(self) -> bool | None:
        """Returns True if the object is an Enclosing object."""
        return True if self.part_Enclosing is not None else None

    @cached_property
    def energycellrequired(self) -> bool | None:
        """Returns True if the object requires an energy cell to function."""
        if self.is_specified("part_EnergyCellSocket"):
            return True

    @cached_property
    def energyammoloader(self) -> bool | None:
        """Returns True if the object has the EnergyAmmoLoader part, which is used to control
        whether certain mods can apply to the item."""
        return True if self.part_EnergyAmmoLoader is not None else None

    @cached_property
    def exoticfood(self) -> bool | None:
        """When preserved, whether the player must explicitly agree to preserve it."""
        if self.tag_ChooseToPreserve is not None:
            return True

    @cached_property
    def filtersgas(self) -> bool | None:
        """Whether this object acts as a gas mask."""
        return True if self.part_GasMask is not None else None

    @cached_property
    def faction(self) -> list | None:
        """The factions this creature has loyalty to.

        Returned as a list of tuples of faction, value like
        [('Joppa', 100), ('Barathrumites', 100)]

        Example XML source:
        <part Name="Brain" Wanders="false" Factions="Joppa-100,Barathrumites-100" />
        """
        ret = None
        if self.part_Brain_Factions:
            ret = []
            for part in self.part_Brain_Factions.split(","):
                if "-" in part:
                    # has format like `Joppa-100,Barathrumites-100`
                    faction, value = part.split("-")
                    ret.append((faction, int(value)))
                else:
                    log.error("Unexpected faction format: %s in %s", part, self.name)
        return ret

    @cached_property
    def flametemperature(self) -> int | None:
        """The temperature at which this object ignites. Only for items."""
        if self.inherits_from("Item") and self.is_specified("part_Physics"):
            return int_or_none(self.part_Physics_FlameTemperature)

    @cached_property
    def flashprotection(self) -> bool | None:
        """True if this item offers protection against visual flash effects."""
        if self.part_FlareCompensation is not None or self.part_ModPolarized is not None:
            return True

    @cached_property
    def flyover(self) -> bool | None:
        """Whether a flying creature can pass over this object."""
        if self.inherits_from("Wall") or self.inherits_from("Furniture"):
            if self.tag_Flyover is not None:
                return True
            else:
                return False

    @cached_property
    def gasemitted(self) -> str | None:
        """The gas emitted by the weapon (typically missile weapon 'pumps')."""
        return self.projectile_object("part_GasOnHit_Blueprint")

    @cached_property
    def gender(self) -> str | None:
        """The gender of the object."""
        if (
            self.tag_Gender_Value is not None
            or (self.tag_RandomGender_Value is not None and "," not in self.tag_RandomGender_Value)
        ) and self.active_or_inactive_character() == ACTIVE_CHAR:
            gender = self.tag_Gender_Value
            if gender is None:
                gender = self.tag_RandomGender_Value
            return gender

    @cached_property
    def harvestedinto(self) -> str | None:
        """What an item produces when harvested."""
        return self.part_Harvestable_OnSuccess

    @cached_property
    def hasmentalshield(self) -> bool | None:
        """If a creature has a mental shield."""
        if self.active_or_inactive_character() == ACTIVE_CHAR:
            if (
                self.part_MentalShield is not None
                or "Mechanical" in self.name
                or (self.part_Roboticized and self.part_Roboticized_ChanceOneIn == "1")
            ):
                return True

    @cached_property
    def healing(self) -> str | None:
        """How much a food item heals when used.

        Example: "1d16+24" for Witchwood Bark"""
        return self.part_Food_Healing

    @cached_property
    def heat(self) -> int | None:
        """The elemental resistance/weakness the equipment or NPC has."""
        return self.resistance("Heat")

    @cached_property
    def hidden(self) -> int | None:
        """If hidden, what difficulty is required to find them.

        Example: 15 for Yonderbrush"""
        return int_or_none(self.part_Hidden_Difficulty)

    @cached_property
    def hp(self) -> str | None:
        """The hitpoints of a creature or object.

        Returned as a string because some hitpoints are given as sValues, which can be
        strings, although they currently are not using this feature."""
        if self.active_or_inactive_character() > 0:
            if self.stat_Hitpoints_sValue is not None:
                return self.stat_Hitpoints_sValue
            elif self.stat_Hitpoints_Value is not None:
                return self.stat_Hitpoints_Value

    @cached_property
    def hunger(self) -> str | None:
        """How much hunger it satiates.

        Example: "Snack" for Vanta Petals"""
        return self.part_Food_Satiation

    @cached_property
    def hurtbydefoliant(self) -> int | None:
        """If the thing is hurt by defoliant.
        0/None = no damage
        1 = normal damage
        2 = significant damage"""
        if self.tag_LivePlant is not None:
            if self.part_Combat is not None and self.tag_GasDamageAsIfInanimate is None:
                return 1
            else:
                return 2

    @cached_property
    def hurtbyfungicide(self) -> int | None:
        """If the thing is hurt by fungicide.
        0/None = no damage
        1 = normal damage
        2 = significant damage"""
        if self.tag_LiveFungus is not None:
            if self.part_Combat is not None and self.tag_GasDamageAsIfInanimate is None:
                return 1
            else:
                return 2

    @cached_property
    def id(self) -> str:
        """The name of the object in ObjectBlueprints.xml. Should always exist."""
        return self.name

    @cached_property
    def illoneat(self) -> bool | None:
        """If eating this makes you sick."""
        if not self.inherits_from("Corpse"):
            if self.part_Food_IllOnEat == "true":
                return True

    @cached_property
    def imprintchargecost(self) -> int | None:
        """How much charge is used to imprint a programmable recoiler."""
        if self.part_ProgrammableRecoiler is not None:
            charge = self.part_ProgrammableRecoiler_ChargeUse
            if charge is not None:
                return int_or_none(charge)
            return 10000  # default IProgrammableRecoiler charge use

    @cached_property
    def inhaled(self) -> str | None:
        """For gases, whether this gas is respiration-based."""
        if self.part_Gas is not None:
            if self.name in [
                "ConfusionGas",
                "Miasma",
                "MiasmaticAsh",
                "PoisonGas",
                "SleepGas",
                "StunGas",
            ]:
                return "yes"  # these are hard-coded
            return "no"

    @cached_property
    def inheritingfrom(self) -> str | None:
        """The ID of the parent object in the Qud object hierarchy.

        Only the root object ("Object") should return None for this."""
        return self.parent.name

    @cached_property
    def intelligence(self) -> str | None:
        """The intelligence the mutation affects, or the intelligence of the creature."""
        return self.attribute_helper("Intelligence")

    @cached_property
    def intelligencemult(self) -> float | None:
        """The stat Bonus multiplier for intrinsic intelligence, if specified."""
        return self.attribute_boost_factor("Intelligence")

    @cached_property
    def intelligenceextrinsic(self) -> int | None:
        """Extra INT for a creature from extrinsic factors, such as mutations or equipment."""
        return None  # nothing currently supported here

    @cached_property
    def inventory(self) -> List[Tuple[str, str, str, str, str]] | None:
        """The inventory of a character.

        Returns a list of tuples of strings: (name, count, equipped, chance, is_pop)."""
        ret = []
        inv = self.inventoryobject
        if inv is not None:
            for name in inv:
                if name[0] in "*#":  # Ignores stuff like '*Junk 1'
                    continue
                is_pop = "no"
                final_name = name
                if name[0] == "@":
                    is_pop = "yes"
                    final_name = name[1:]
                count = inv[name].get("Number", "1")
                equipped = "no"  # not yet implemented
                chance = inv[name].get("Chance", "100")
                ret.append((final_name, count, equipped, chance, is_pop))
        pop_name = self.tag_InventoryPopulationTable_Value
        if pop_name is not None:
            pop: QudPopulation = self.gameroot.get_populations().get(pop_name)
            if pop is not None:
                if pop.depth > 1:
                    # complex population - represent with parent pop name and quantity of '*'
                    ret.append((pop_name, "*", "no", "100", "yes"))
                elif pop.style != "pickeach":
                    # population with single 'pickone' group - for example "Artifact 6R"
                    group = pop.children[0]
                    ret.append((pop_name, group.number, "no", group.chance, "yes"))
                else:
                    for pop_item in pop.get_effective_children():
                        count = pop_item.number
                        chance = pop_item.chance
                        equipped = "no"  # not yet implemented
                        if pop_item.type == "object":  # noinspection PyUnresolvedReferences
                            ret.append((pop_item.blueprint, count, equipped, chance, "no"))
                        elif pop_item.type == "table":  # noinspection PyUnresolvedReferences
                            ret.append((pop_item.name, count, equipped, chance, "yes"))
                        elif pop_item.type == "group":
                            pass  # shouldn't happen bec. we only evaluate populations with depth 1
        return ret if len(ret) > 0 else None

    @cached_property
    def iscurrency(self) -> bool | None:
        """If the item is considered currency (price remains fixed while trading)."""
        if self.intproperty_Currency_Value == "1":
            return True

    @cached_property
    def isfungus(self) -> bool | None:
        """If the food item contains fungus."""
        if self.tag_Mushroom is not None:
            return True

    @cached_property
    def ismeat(self) -> bool | None:
        """If the food item contains meat."""
        if self.tag_Meat is not None:
            return True

    @cached_property
    def ismissile(self) -> bool | None:
        """If this item is a missile weapon"""
        if self.inherits_from("MissileWeapon"):
            return True
        if self.is_specified("part_MissileWeapon"):
            return True

    @cached_property
    def isthrown(self) -> bool | None:
        """If this item is a thrown weapon"""
        if self.part_ThrownWeapon is not None:
            return True

    @cached_property
    def isoccluding(self) -> bool | None:
        if self.part_Render_Occluding is not None:
            if self.part_Render_Occluding == "true" or self.part_Render_Occluding == "True":
                return True

    @cached_property
    def isplant(self) -> bool | None:
        """If the food item contains plants."""
        if self.tag_Plant is not None:
            return True

    @cached_property
    def isswarmer(self) -> bool | None:
        """Whether a creature is a Swarmer."""
        if self.inherits_from("Creature"):
            if self.part_Swarmer is not None:
                return True

    @cached_property
    def leakswhenbroken(self) -> str | None:
        """If this object leaks liquid when broken, the dice string for % amount per turn leaked."""
        if self.part_LeakWhenBroken is not None:
            amt = self.part_LeakWhenBroken_PercentPerTurn
            amt = "10-20" if amt is None else amt  # 10-20% is default
            return amt

    @cached_property
    def lightprojectile(self) -> bool | None:
        """If the gun fires light projectiles (heat immune creatures will not take damage)."""
        if self.tag_Light is not None:
            return True

    @cached_property
    def lightradius(self) -> int | None:
        """Radius of light the object gives off."""
        val = int_or_none(self.part_LightSource_Radius)
        if val is None:
            val = int_or_none(self.part_ActiveLightSource_Radius)
        return val

    @cached_property
    def liquidgenrate(self) -> int | None:
        """For liquid generators. how many turns it takes for 1 dram to generate."""
        if self.part_LiquidProducer:
            amount_range = self.part_LiquidProducer_VariableRate
            return amount_range if amount_range is not None else self.part_LiquidProducer_Rate

    @cached_property
    def liquidgentype(self) -> str | None:
        """For liquid generators, the type of liquid generated."""
        return self.part_LiquidProducer_Liquid

    @cached_property
    def liquidburst(self) -> str | None:
        """If it explodes into liquid, what kind?"""
        return self.part_LiquidBurst_Liquid

    @cached_property
    def lv(self) -> str | None:
        """The object's level.

        Returned as a string because it may be possible for it to be an sValue, as in
        Barathrumite_FactionMemberMale which has a level sValue of "18-29"."""
        level = self.stat_Level_sValue
        if level is None:
            level = self.stat_Level_Value
        return level

    @cached_property
    def ma(self) -> int | None:
        """The object's mental armor. For creatures, this is an averaged value.
        For items, this can be a bonus to MA as specified in the Armor part.

        We should still return MA for creatures with a mental shield, such as Robots, because those
        creatures' MA value is used in certain scenarios, such as to defend against Rebuke Robot."""
        if (char_type := self.active_or_inactive_character()) == INACTIVE_CHAR:
            return None
        elif char_type == ACTIVE_CHAR:
            # MA starts at base 4
            ma = 4
            # Add MA stat value if specified
            if self.stat_MA_Value:
                ma += int(self.stat_MA_Value)
            # add willpower modifier to MA
            ma += self.attribute_helper_mod("Willpower")
            return ma
        else:  # items (char_type == 0)
            return int_or_none(self.attribute_helper("MA"))

    @cached_property
    def marange(self) -> str | None:
        """The creature's full range of potential MA values"""
        if (char_type := self.active_or_inactive_character()) == INACTIVE_CHAR:
            return None
        elif char_type == ACTIVE_CHAR:
            ma = 4
            if self.stat_MA_Value:
                ma += int(self.stat_MA_Value)
            # add willpower modifier to MA
            minmod = self.attribute_helper_mod("Willpower", "min")
            maxmod = self.attribute_helper_mod("Willpower", "max")
            if minmod == maxmod:
                return str(ma + minmod)
            # returning this in a bit of a weird format so that our wiki dice parser can
            # parse it correctly (it doesn't do well with ranges like -2--1 [fire ant], so we
            # would output this instead as -3+1d2
            return f"{ma + minmod - 1}+1d{maxmod - minmod + 1}"

    @cached_property
    def maxammo(self) -> int | None:
        """How much ammo a gun can have loaded at once."""
        return int_or_none(self.part_MagazineAmmoLoader_MaxAmmo)

    @cached_property
    def maxcharge(self) -> int | None:
        """How much charge it can hold (usually reserved for cells)."""
        return int_or_none(self.part_EnergyCell_MaxCharge)

    @cached_property
    def maxvol(self) -> int | None:
        """The maximum liquid volume."""
        return int_or_none(self.part_LiquidVolume_MaxVolume)

    @cached_property
    def maxpv(self) -> int | None:
        """The max strength bonus + our base PV."""
        pv = self.pv
        if pv is not None:
            if self.is_melee_weapon():
                if self.part_MeleeWeapon_MaxStrengthBonus is not None:
                    pv += int(self.part_MeleeWeapon_MaxStrengthBonus)
        return pv

    @cached_property
    def metal(self) -> bool | None:
        """Whether the object is made out of metal."""
        if self.part_Metal is not None or (
            self.part_Roboticized and self.part_Roboticized_ChanceOneIn == "1"
        ):
            return True

    @cached_property
    def modcount(self) -> int | None:
        """The number of mods on the item, if applicable.

        Example: Svensword with
            <part Name="AddMod" Mods="ModCounterweighted,ModElectrified" Tiers="5,7" />
        will return 2.

        MasterworkCarbine with
            <part Name="ModScoped" />
            <part Name="ModMasterwork" />
        will likewise return 2.
        """
        val = 0
        if self.part_AddMod_Mods is not None:
            val += len(self.part_AddMod_Mods.split(","))
        for key in self.part.keys():
            if key.startswith("Mod"):
                val += 1
        return val if val > 0 else None

    @cached_property
    def mods(self) -> List[Tuple[str, int]] | None:
        """Mods that are attached to the current item.

        Returns a list of tuples like [(modid, tier), ...].
        """
        mods = []
        if self.part_AddMod_Mods is not None:
            names = self.part_AddMod_Mods.split(",")
            if self.part_AddMod_Tiers is not None:
                tiers = self.part_AddMod_Tiers.split(",")
                tiers = [int(tier) for tier in tiers]
            else:
                tiers = [1] * len(names)
            mods.extend(zip(names, tiers))
        for key in self.part.keys():
            if key.startswith("Mod"):
                if "Tier" in self.part[key]:
                    mods.append((key, int(self.part[key]["Tier"])))
                else:
                    mods.append((key, 1))
        return mods if len(mods) > 0 else None

    @cached_property
    def movespeed(self) -> int | None:
        """The movespeed of a creature."""
        if self.inherits_from("Creature"):
            ms = int_or_none(self.stat_MoveSpeed_Value)
            if ms is not None:
                # https://bitbucket.org/bbucklew/cavesofqud-public-issue-tracker/issues/2634
                ms = 200 - ms
                return ms

    @cached_property
    def movespeedbonus(self) -> int | None:
        """The movespeed bonus of an item."""
        if self.inherits_from("Item"):
            bonus = self.part_MoveCostMultiplier_Amount
            if bonus is not None:
                return -int(bonus)

    @cached_property
    def mutatedplant(self) -> bool | None:
        """Whether this object is a MutatedPlant"""
        if self.inherits_from("MutatedPlant"):
            return True

    @cached_property
    def mutations(self) -> List[Tuple[str, int]] | None:
        """The mutations the creature has along with their level.

        Returns a list of tuples like [(name, level), ...].
        """
        mutations = []
        if self.mutation is not None:  # direct reference to <mutation> XML tag - not a property
            for mutation, data in self.mutation.items():
                postfix = f"{data['GasObject']}" if "GasObject" in data else ""
                level = int(data["Level"]) if "Level" in data else 0
                mutations.append((mutation + postfix, level))
        if self.part_Roboticized and self.part_Roboticized_ChanceOneIn == "1":
            # additional mutations added to roboticized things
            if self.mutation is None or not any(
                mu in ["NightVision", "DarkVision"] for mu in self.mutation.keys()
            ):
                mutations.append(("DarkVision", 12))
        if len(mutations) > 0:
            return mutations

    @cached_property
    def noprone(self) -> bool | None:
        """Returns true if has part NoKnockdown."""
        if self.part_NoKnockdown is not None:
            return True

    @cached_property
    def omniphaseprojectile(self) -> bool | None:
        projectile = self.projectile_object()
        if projectile.is_specified("part_OmniphaseProjectile") or projectile.is_specified(
            "tag_Omniphase"
        ):
            return True

    @cached_property
    def oneat(self) -> List[str] | None:
        """Effects granted when the object is eaten.

        Returns a list of strings, which are the effects.
        Example:
            Transform <part Name="BreatheOnEat" Class="FireBreather" Level="5"></part>
            into ['BreatheOnEatFireBreather5']"""
        effects = []
        for key, val in self.part.items():
            if key.endswith("OnEat"):
                effect = key
                if "Class" in val:
                    effect += val["Class"]
                    effect += val["Level"]
                effects.append(effect)
        return effects if len(effects) > 0 else None

    @cached_property
    def penetratingammo(self) -> bool | None:
        """If the missile weapon's projectiles pierce through targets."""
        if self.projectile_object("part_Projectile_PenetrateCreatures") is not None:
            return True

    @cached_property
    def pettable(self) -> bool | None:
        """If the creature is pettable."""
        if self.part_Pettable is not None:
            return True

    @cached_property
    def phase(self) -> str | None:
        """What phase the object/creature is in, if not in phase."""
        if self.part_HologramMaterial or self.tag_Omniphase:
            return "omniphase"
        if self.tag_Nullphase:
            return "nullphase"
        if self.tag_Astral:
            return "out of phase"
        if self.mutation:
            for mutation, data in self.mutation.items():
                if mutation == "Spinnerets":
                    if f"{data['Phase']}" == "True":
                        return "out of phase"

    @cached_property
    def poisononhit(self) -> str | None:
        if self.part_PoisonOnHit:
            pct = self.part_PoisonOnHit_Chance
            save = self.part_PoisonOnHit_Strength
            dmg = self.part_PoisonOnHit_DamageIncrement
            duration = self.part_PoisonOnHit_Duration
            pct = pct if pct is not None else "100"
            save = save if save is not None else "15"
            dmg = dmg if dmg is not None else "3d3"
            duration = duration if duration is not None else "6-9"
            return (
                f"{pct}% to poison on hit, toughness save {save}."
                + f" {dmg} damage for {duration} turns."
            )

    @cached_property
    def powerloadsensitive(self) -> bool | None:
        """Returns yes if the object is power load sensitive. This means that the object can support
        the overloaded item mod."""
        all_parts = getattr(self, "part")
        if all_parts is not None:
            # object is powerload sensitive if any single part on the object is powerload sensitive:
            for partname, partattribs in all_parts.items():
                if partname in ACTIVE_PARTS:
                    if partattribs.get(
                        "IsPowerLoadSensitive", ACTIVE_PARTS[partname]["IsPowerLoadSensitive"]
                    ):
                        return True

    @cached_property
    def preservedinto(self) -> str | None:
        """When preserved, what a preservable item produces."""
        return self.part_PreservableItem_Result

    @cached_property
    def preservedquantity(self) -> int | None:
        """When preserved, how many preserves a preservable item produces."""
        return int_or_none(self.part_PreservableItem_Number)

    @cached_property
    def primarydamageelement(self) -> str | None:
        """If a weapon's primary damage is elemental, this returns the type of element.
        This is distinct from elementaldamage/elementaltype - those properties are used when a
        weapon has secondary elemental damage (in addition to its "normal" damage)."""
        if self.part_ElectricalDischargeLoader is not None:
            return "Electric"

    @cached_property
    def pronouns(self) -> str | None:
        """Return the pronounset of a creature, if [they] have any."""
        if self.tag_PronounSet_Value is not None and self.inherits_from("Creature"):
            return self.tag_PronounSet_Value

    @cached_property
    def pv(self) -> int | None:
        """The base PV, which is by default 4 if not set. Optional.
        The game adds 4 to internal PV values for display purposes, so we also do that here."""
        pv = None
        if self.is_melee_weapon():
            pv = 4
            if self.part_Gaslight_ChargedPenetrationBonus is not None:
                pv += int(self.part_Gaslight_ChargedPenetrationBonus)
            elif self.part_MeleeWeapon_PenBonus is not None:
                pv += int(self.part_MeleeWeapon_PenBonus)
        missilepv = self.projectile_object("part_Projectile_BasePenetration")
        if missilepv is not None:
            pv = int(missilepv) + 4
        if self.part_ThrownWeapon is not None:
            pv = int_or_none(self.part_ThrownWeapon_Penetration)
            if pv is None:
                pv = 1
            pv = pv + 4
        if pv is not None:
            return pv

    @cached_property
    def pvpowered(self) -> bool | None:
        """Whether the object's PV changes when it is powered."""
        is_vibro = self.vibro and self.vibro is not None
        if is_vibro and self.is_specified("part_MissileWeapon"):
            return None
        if is_vibro and (not self.part_VibroWeapon or int(self.part_VibroWeapon_ChargeUse) > 0):
            return True
        if self.part_Gaslight and int(self.part_Gaslight_ChargeUse) > 0:
            return True
        if self.part_Projectile_Attributes == "Vorpal":
            # FIXME: this seems like it won't actually works [use projectile_object() instead?]
            return True

    @cached_property
    def quickness(self) -> int | None:
        """Return quickness of a creature"""
        if self.active_or_inactive_character() == ACTIVE_CHAR:
            mutation_val = 0
            if self.mutation:
                for mutation, info in self.mutation.items():
                    if mutation == "ColdBlooded":
                        mutation_val -= 10
                    if mutation == "HeightenedSpeed":
                        mutation_val += int(info["Level"]) * 2 + 13
            if mutation_val != 0:
                return (
                    mutation_val + 100
                    if self.stat_Speed_Value is None
                    else int(self.stat_Speed_Value)
                )
            return int_or_none(self.stat_Speed_Value)
        if self.part_Armor:
            return int_or_none(self.part_Armor_SpeedBonus)

    @cached_property
    def realitydistortionbased(self) -> bool | None:
        projectile = self.projectile_object()
        if projectile is not None:
            projectile_rd_info = projectile.part_TreatAsSolid_RealityDistortionBased
            if projectile_rd_info is not None and projectile_rd_info == "true":
                return True
            projectile_vamp_rd_info = projectile.part_VampiricWeapon_RealityDistortionBased
            if projectile_vamp_rd_info is not None and projectile_vamp_rd_info == "true":
                return True
        if self.part_MechanicalWings_IsRealityDistortionBased is not None:
            if self.part_MechanicalWings_IsRealityDistortionBased == "true":
                return True
        if self.part_DeploymentGrenade_UsabilityEvent is not None:
            if self.part_DeploymentGrenade_UsabilityEvent == "CheckRealityDistortionUsability":
                return True
        if self.part_Displacer is not None:
            return True
        if self.part_SpaceTimeVortex is not None:
            return True
        if self.part_EngulfingClones is not None:
            return True
        if self.part_GreaterVoider is not None:
            return True

    @cached_property
    def reflect(self) -> int | None:
        """If it reflects, what percentage of damage is reflected."""
        return int_or_none(self.part_ModGlassArmor_Tier)

    @cached_property
    def refractive(self) -> bool | None:
        """True if this object or creature refracts light."""
        if self.part_RefractLight is not None or self.part_ModRefractive is not None:
            return True

    @cached_property
    def renderstr(self) -> str | None:
        """The character used to render this object in ASCII mode."""
        render = None
        if self.part_Render_RenderString and len(self.part_Render_RenderString) > 1:
            # some RenderStrings are given as CP437 character codes in base 10
            render = cp437_to_unicode(int(self.part_Render_RenderString))
        elif self.part_Gas is not None:
            render = "▓"
        elif self.part_Render_RenderString is not None:
            render = self.part_Render_RenderString
        return render

    @cached_property
    def reputationbonus(self) -> List[Tuple[str, int]] | None:
        """Reputation bonuses granted by the object.

        Returns a list of tuples like [(faction, value), ...].
        """
        # Examples of XML source formats:
        # <part Name="AddsRep" Faction="Apes" Value="-100" />
        # <part Name="AddsRep" Faction="Antelopes,Goatfolk" Value="100" />
        # <part Name="AddsRep" Faction="Fungi:200,Consortium:-200" />
        if self.part_AddsRep:
            reps = []
            for part in self.part_AddsRep_Faction.split(","):
                if ":" in part:
                    # has format like `Fungi:200,Consortium:-200`
                    faction, value = part.split(":")
                else:
                    # has format like `Antelopes,Goatfolk` and Value `100`
                    # or is a single faction, like `Apes` and Value `-100`
                    faction = part
                    value = self.part_AddsRep_Value
                value = int(value)
                reps.append((faction, value))
            return reps

    @cached_property
    def role(self) -> str | None:
        """What role a creature or object has assigned.

        Example: Programmable Recoiler has "Uncommon"
        Albino ape has "Brute"
        """
        return self.property_Role_Value

    @cached_property
    def savemodifier(self) -> str | None:
        """Returns save modifier type"""
        return self.part_SaveModifier_Vs

    @cached_property
    def savemodifieramt(self) -> str | None:
        """returns amount of the save modifer."""
        if self.part_SaveModifier_Vs is not None:
            val = int_or_none(self.part_SaveModifier_Amount)
            if val is not None:
                return str(val) if val < 0 else f"+{val}"

    @cached_property
    def seeping(self) -> str | None:
        if self.part_Gas is not None:
            if self.is_specified("part_Gas_Seeping"):
                if self.part_Gas_Seeping == "true":
                    return "yes"
            if self.is_specified("tag_GasGenerationAddSeeping"):
                if self.tag_GasGenerationAddSeeping_Value == "true":
                    return "yes"
            return "no"

    @cached_property
    def shotcooldown(self) -> str | None:
        """Cooldown before weapon can be fired again, typically a dice string."""
        return self.part_CooldownAmmoLoader_Cooldown

    @cached_property
    def shots(self) -> int | None:
        """How many shots are fired in one round."""
        return int_or_none(self.part_MissileWeapon_ShotsPerAction)

    @cached_property
    def shrinelike(self) -> bool | None:
        """Whether this object has the 'Shrine' part, which affects behavior such as descration."""
        return True if self.part_Shrine is not None else None

    @cached_property
    def skills(self) -> str | None:
        """The skills that certain creatures have."""
        if self.skill is not None:
            return self.skill

    @cached_property
    def solid(self) -> bool | None:
        if self.is_specified("part_Physics_Solid"):
            if self.part_Physics_Solid == "true" or self.part_Physics_Solid == "True":
                return True
            # add some if-exclusions for things that shouldn't say 'can be walked over/through':
            if self.inheritingfrom == "Door":  # security doors
                return None
            if self.part_ThrownWeapon is not None:
                # thrown weapons for some reason often specify Solid="false"
                if "Boulder" not in self.name:
                    return None
            return False

    @cached_property
    def spectacles(self) -> bool | None:
        """If the item corrects vision."""
        return True if self.part_Spectacles is not None else None

    @cached_property
    def strength(self) -> str | None:
        """The strength the mutation affects, or the strength of the creature."""
        return self.attribute_helper("Strength")

    @cached_property
    def strengthmult(self) -> float | None:
        """The stat Bonus multiplier for intrinsic strength, if specified."""
        return self.attribute_boost_factor("Strength")

    @cached_property
    def strengthextrinsic(self) -> int | None:
        """Extra strength for a creature from extrinsic factors, such as mutations or equipment."""
        if self.active_or_inactive_character() == ACTIVE_CHAR:
            if self.mutation:
                val = 0
                for mutation, info in self.mutation.items():
                    if mutation == "HeightenedStrength":
                        val += (int(info["Level"]) - 1) // 2 + 2
                    if mutation == "SlogGlands":
                        val += 6
                if val != 0:
                    return val

    @cached_property
    def supportedmods(self) -> str | None:
        """The categories of mods that are supported by this item"""
        val = self.tag_Mods_Value
        if val is not None and val != "None":
            return val

    @cached_property
    def swarmbonus(self) -> int | None:
        """The additional bonus that Swarmers receive."""
        return int_or_none(self.part_Swarmer_ExtraBonus)

    @cached_property
    def temponenter(self) -> str | None:
        """Temperature change caused to objects when weapon/projectile passes through cell.

        Can be a dice string."""
        var = self.projectile_object("part_TemperatureOnEntering_Amount")  # projectiles
        return var or self.part_TemperatureOnEntering_Amount  # melee weapons, etc.

    @cached_property
    def temponhit(self) -> str | None:
        """Temperature change caused by weapon/projectile hit.

        Can be a dice string."""
        var = self.projectile_object("part_TemperatureOnHit_Amount")
        return var or self.part_TemperatureOnHit_Amount

    @cached_property
    def temponhitmax(self) -> int | None:
        """Temperature change effect does not occur if target has already reached MaxTemp."""
        temp = self.projectile_object("part_TemperatureOnHit_MaxTemp")
        if temp is not None:
            return int(temp)
        temp = self.part_TemperatureOnHit_MaxTemp
        if temp is not None:
            return int(temp)

    @cached_property
    def thirst(self) -> int | None:
        """How much thirst it slakes."""
        return int_or_none(self.part_Food_Thirst)

    @cached_property
    def tier(self) -> int | None:
        """Returns tier. Returns the Specified tier if it isn't inherited. Else it will return
        the highest value bit (if tinkerable) or its FLOOR(Level/5), if neither of these exist,
        it will return the inherited tier value."""
        if not self.is_specified("tag_Tier_Value"):
            if self.is_specified("part_TinkerItem_Bits"):
                val = self.part_TinkerItem_Bits[-1]
                if val.isdigit():
                    return int(val)
                else:
                    return 0
            elif self.lv is not None:
                try:
                    level = int(self.lv)
                except ValueError:
                    # levels can be very rarely given like "18-29"
                    level = int(self.lv.split("-")[0])
                return level // 5
        return int_or_none(self.tag_Tier_Value)

    @cached_property
    def tilecolors(self) -> str | None:
        """The primary color and detail color used by this object's main image"""
        tile = self.tile
        if tile is not None and tile.tilecolor_letter is not None:
            val = tile.tilecolor_letter
            val += tile.detailcolor_letter if tile.detailcolor_letter is not None else ""
            return val

    @cached_property
    def title(self) -> str | None:
        """The display name of the item."""
        val = self.name
        predefs = {
            "Wraith-Knight Templar": "&MWraith-Knight Templar of the Binary Honorum",
            "TreeSkillsoft": "&YSkillsoft plus",
            "SingleSkillsoft1": "&YSkillsoft [&Wlow sp&Y]",
            "SingleSkillsoft2": "&YSkillsoft [&Wmedium sp&Y]",
            "SingleSkillsoft3": "&YSkillsoft [&Whigh sp&Y]",
            "Schemasoft2": "&YSchemasoft [&Wlow-tier&Y]",
            "Schemasoft3": "&YSchemasoft [&Wmid-tier&Y]",
            "Schemasoft4": "&YSchemasoft [&Whigh-tier&Y]",
        }
        if self.name in predefs:
            val = predefs[self.name]
        elif self.builder_GoatfolkHero1_ForceName:
            val = self.builder_GoatfolkHero1_ForceName  # for Mamon
        elif self.part_Render_DisplayName:
            val = self.part_Render_DisplayName
        if self.part_Roboticized and self.part_Roboticized_ChanceOneIn == "1":
            name_prefix = self.part_Roboticized_NamePrefix
            name_prefix = "{{c|mechanical}}" if not name_prefix else name_prefix
            val = f"{name_prefix} {val}"
        return val

    @cached_property
    def tohit(self) -> int | None:
        """The bonus or penalty to hit."""
        if self.inherits_from("Armor"):
            return int_or_none(self.part_Armor_ToHit)
        if self.is_melee_weapon():
            return int_or_none(self.part_MeleeWeapon_HitBonus)

    @cached_property
    def toughness(self) -> str | None:
        """The toughness the mutation affects, or the toughness of the creature."""
        return self.attribute_helper("Toughness")

    @cached_property
    def toughnessmult(self) -> float | None:
        """The stat Bonus multiplier for intrinsic toughness, if specified."""
        return self.attribute_boost_factor("Toughness")

    @cached_property
    def toughnessextrinsic(self) -> int | None:
        """Extra toughness for a creature from extrinsic factors, such as mutations or equipment."""
        if self.active_or_inactive_character() == ACTIVE_CHAR:
            if self.mutation:
                for mutation, info in self.mutation.items():
                    if mutation == "HeightenedToughness":
                        return (int(info["Level"]) - 1) // 2 + 2

    @cached_property
    def twohanded(self) -> bool | None:
        """Whether this is a two-handed item."""
        if self.inherits_from("MeleeWeapon") or self.inherits_from("MissileWeapon"):
            if self.tag_UsesSlots and self.tag_UsesSlots != "Hand":
                return None  # exclude things like Slugsnout Snout
            if self.part_Physics_bUsesTwoSlots or self.part_Physics_UsesTwoSlots:
                return True
            return False

    @cached_property
    def unidentifiedimage(self) -> str | None:
        """The filename of the object's 'unidentified' tile variant."""
        meta = self.unidentified_metadata()
        if meta is not None:
            return meta.filename

    @cached_property
    def unidentifiedname(self) -> str | None:
        """The name of the object when unidentified, such as 'weird artifact'."""
        complexity = self.complexity
        if complexity is not None and complexity > 0:
            understanding = self.part_Examiner_Understanding
            if understanding is None or int(understanding) < complexity:
                unknown_name = self.part_Examiner_UnknownDisplayName
                unknown_name = "weird artifact" if unknown_name is None else unknown_name
                if unknown_name != "*med":
                    return unknown_name

    @cached_property
    def unidentifiedaltname(self) -> str | None:
        """The name of the object when partially identified, such as 'backpack'."""
        complexity = self.complexity
        if complexity is not None and complexity > 0:
            understanding = self.part_Examiner_Understanding
            if understanding is None or int(understanding) < complexity:
                alt_name = self.part_Examiner_AlternateDisplayName
                alt_name = "device" if alt_name is None else alt_name
                if alt_name != "*med":
                    return alt_name

    @cached_property
    def unpowereddamage(self) -> str | None:
        """For weapons that use charge, the damage dealt when unpowered.

        Given as a dice string."""
        return self.part_Gaslight_UnchargedDamage

    @cached_property
    def unreplicable(self) -> bool | None:
        """True if this object can NOT be replicated by items such as metamorphic polygel."""
        if self.part_Unreplicable is not None or self.part_Polygel is not None:
            return True

    @cached_property
    def usesslots(self) -> List[str] | None:
        """Return the body slots taken up by equipping this item.

        This is not the same as the slot the item is equipped "to", which is given by wornon

        Example: Portable Beehive returns ["Back", "Floating Nearby"].
        """
        if self.tag_UsesSlots_Value is not None:
            return self.tag_UsesSlots_Value.split(",")

    @cached_property
    def vibro(self) -> bool | None:
        """Whether this is a vibro weapon."""
        # if self.is_specified('part_ThrownWeapon'):
        if self.is_specified("part_GeomagneticDisc"):
            return True
        elif self.is_specified("part_MissileWeapon"):
            attributes = self.projectile_object("part_Projectile_Attributes")
            if attributes is not None:
                if "Vorpal" in attributes.split(" "):
                    return True
        elif self.inherits_from("MeleeWeapon") or self.inherits_from("NaturalWeapon"):
            if self.part_VibroWeapon:
                return True

    @cached_property
    def waterritualable(self) -> bool | None:
        """Whether the creature is waterritualable."""
        if self.is_specified("xtag_WaterRitual") or self.part_GivesRep is not None:
            return True

    @cached_property
    def waterritualskill(self) -> str | None:
        """What skill that individual teaches, if they have any."""
        if self.is_specified("xtag_WaterRitual") or self.part_GivesRep is not None:
            return self.xtag_WaterRitual_SellSkill

    @cached_property
    def weaponskill(self) -> str | None:
        """The skill tree required for use."""
        val = None
        if self.is_melee_weapon():
            val = self.part_MeleeWeapon_Skill
        if self.inherits_from("MissileWeapon"):
            if self.part_MissileWeapon_Skill is not None:
                val = self.part_MissileWeapon_Skill
        if self.part_Gaslight:
            val = self.part_Gaslight_ChargedSkill
        # disqualify various things from showing the 'cudgel' skill:
        if self.inherits_from("Projectile"):
            val = None
        if self.inherits_from("Shield"):
            val = "Shield"
        return val

    @cached_property
    def weight(self) -> int | None:
        """The weight of the object."""
        if (
            self.inherits_from("InertObject")
            or self.inherits_from("CosmeticObject")
            or (self.part_Physics_IsReal is not None and self.part_Physics_IsReal == "false")
            or self.tag_IgnoresGravity is not None
            or self.tag_ExcavatoryTerrainFeature is not None
        ):
            return None
        return int_or_none(self.part_Physics_Weight)

    @cached_property
    def willpower(self) -> str | None:
        """The willpower the mutation affects, or the willpower of the creature."""
        return self.attribute_helper("Willpower")

    @cached_property
    def willpowermult(self) -> float | None:
        """The stat Bonus multiplier for intrinsic willpower, if specified."""
        return self.attribute_boost_factor("Willpower")

    @cached_property
    def willpowerextrinsic(self) -> int | None:
        """Extra willpower for a creature from extrinsic factors, such as mutations or equipment."""
        return None  # nothing currently supported here

    @cached_property
    def wornon(self) -> str | None:
        """The body slot that an item gets equipped to.

        Not the same as the body slots it occupies once equipped, which is given by usesslots."""
        wornon = None
        if self.part_Shield_WornOn:
            wornon = self.part_Shield_WornOn
        if self.part_Armor_WornOn:
            wornon = self.part_Armor_WornOn
        if self.name == "Hooks":
            wornon = "Feet"  # manual fix
        return wornon

    @cached_property
    def xpvalue(self) -> int | None:
        level = self.lv
        try:
            # there's one object that uses an sValue for "Level" ('Barathrumite Tinker' => '18-29')
            # that object and its children are not wiki-enabled, but would raise an exception here.
            level = int_or_none(level)
        except ValueError:
            level = None
        if level is None:
            return None
        xp_value = getattr(self, "stat_XPValue_sValue")
        if not xp_value:
            xp_value = getattr(self, "stat_XPValue_Value")
        if not xp_value:
            return None
        xp = xp_value
        if xp == "*XP":
            role = self.role
            role = "Minion" if role is None else role
            match role:
                case "Minion":
                    xp = level * 10
                case "Leader":
                    xp = level * 50
                case "Hero":
                    xp = level * 100
                case _:
                    xp = level * 25
        else:
            xp = int_or_none(xp)
            if xp is None:
                return None
        return xp

    @cached_property
    def xptier(self) -> int | None:
        level = self.lv
        try:
            # there's one object that uses an sValue for "Level" ('Barathrumite Tinker' => '18-29')
            # that object and its children are not wiki-enabled, but would raise an exception here.
            level = int_or_none(level)
        except ValueError:
            return None
        if level is not None:
            return level // 5
