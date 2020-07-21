from __future__ import annotations

from typing import Union, Tuple, List

from hagadias.constants import BIT_TRANS, ITEM_MOD_PROPS
from hagadias.helpers import cp437_to_unicode, int_or_none,\
    strip_oldstyle_qud_colors, strip_newstyle_qud_colors
from hagadias.dicebag import DiceBag
from hagadias.qudobject import QudObject
from hagadias.svalue import sValue

# STATIC GROUPS
# Many combat properties can come from anything that inherits from either of these.
# Use For: any(self.inherits_from(character) for character in ACTIVE_CHAR).
# ACTIVE: What is typically considered a Character, with an inventory and combat capabilities.
ACTIVE_CHARS = ['Creature', 'ActivePlant']
# INACTIVE: What would still be helpful to have combat related stats, but have things that
# make them different from active characters. Usually immobile and have no attributes.
INACTIVE_CHARS = ['BaseFungus', 'Baetyl', 'Wall', 'Furniture']
ALL_CHARS = ACTIVE_CHARS + INACTIVE_CHARS


class QudObjectProps(QudObject):
    """Represents a Caves of Qud game object with properties to calculate derived stats.

    Inherits from QudObject which does all the lower level work.

    Properties should return Python types where possible (lists, bools, etc.) and leave specific
    representations to a subclass."""
    # PROPERTY HELPERS
    # Helper methods to simplify the calculation of properties, further below.
    # Sorted alphabetically.

    def attribute_helper(self, attr: str, mode: str = '') -> Union[str, None]:
        """Helper for retrieving attributes (Strength, etc.)"""
        val = None
        if any(self.inherits_from(character) for character in ACTIVE_CHARS):
            if getattr(self, f'stat_{attr}_sValue'):
                try:
                    level = int(self.lv)
                except ValueError:
                    # levels can be very rarely given like "18-29"
                    level = int(self.lv.split('-')[0])
                val = str(sValue(getattr(self, f'stat_{attr}_sValue'), level=level))
            elif getattr(self, f'stat_{attr}_Value'):
                val = getattr(self, f'stat_{attr}_Value')
            boost = getattr(self, f'stat_{attr}_Boost')
            if boost:
                val += f'+{boost}'
        elif self.inherits_from('Armor'):
            val = getattr(self, f'part_Armor_{attr}')
        return val

    def attribute_helper_avg(self, attr: str) -> Union[int, None]:
        """Return the average stat value for the given stat."""
        val_str = self.attribute_helper(attr)
        if val_str is not None:
            val = DiceBag(val_str).average()  # calculate average stat value
            val = int(val * (0.8 if self.role == 'Minion' else 1))  # Minions lose 20% to all stats
        else:
            val = None
        return val

    def attribute_helper_mod(self, attr: str) -> Union[int, None]:
        """Return the modifier for the average stat value for the given stat."""
        val = self.attribute_helper_avg(attr)
        val = (val - 16) // 2  # return stat modifier for average roll
        return val

    def resistance(self, element: str) -> Union[int, None]:
        """The elemental resistance/weakness the equipment or NPC has.
        Helper function for properties."""
        val = getattr(self, f'stat_{element}Resistance_Value')
        if self.part_Armor:
            if element == "Electric":
                element = "Elec"  # short form in armor
            val = getattr(self, f'part_Armor_{element}')
        return int_or_none(val)

    def projectile_object(self, part_attr: str = '') -> Union[QudObjectProps, str, None]:
        """Retrieve the projectile object for a MissileWeapon or Arrow.
        If part_attr specified, retrieve the specific part attribute
        value from that projectile object instead.

        Doesn't work for bows because their projectile object varies
        depending on the type of arrow loaded into them."""
        if self.part_MissileWeapon is not None or self.is_specified('part_AmmoArrow'):
            parts = ['part_BioAmmoLoader_ProjectileObject',
                     'part_AmmoArrow_ProjectileObject',
                     'part_MagazineAmmoLoader_ProjectileObject',
                     'part_EnergyAmmoLoader_ProjectileObject',
                     'part_LiquidAmmoLoader_ProjectileObject']
            for part in parts:
                attr = getattr(self, part)
                if attr is not None and attr != '':
                    item = self.qindex[attr]
                    if part_attr:
                        return getattr(item, part_attr, None)
                    else:
                        return item
        return None

    # PROPERTIES
    # These properties are the heart of hagadias. They make it easy to access attributes
    # buried in the XML, or which require some computation or translation.
    # Properties all return None implicitly if the property is not applicable to the current item.
    @property
    def accuracy(self) -> Union[int, None]:
        """How accurate the gun is."""
        return int_or_none(self.part_MissileWeapon_WeaponAccuracy)

    @property
    def acid(self) -> Union[int, None]:
        """The elemental resistance/weakness the equipment or NPC has."""
        return self.resistance('Acid')

    @property
    def agility(self) -> Union[str, None]:
        """The agility the mutation affects, or the agility of the creature."""
        return self.attribute_helper('Agility')

    @property
    def ammo(self) -> Union[str, None]:
        """What type of ammo is used."""
        ammo = None
        if self.part_MagazineAmmoLoader_AmmoPart:
            ammotypes = {'AmmoSlug': 'lead slug',
                         'AmmoShotgunShell': 'shotgun shell',
                         'AmmoGrenade': 'grenade',
                         'AmmoMissile': 'missile',
                         'AmmoArrow': 'arrow',
                         'AmmoDart': 'dart',
                         }
            ammo = ammotypes.get(self.part_MagazineAmmoLoader_AmmoPart)
        elif self.part_EnergyAmmoLoader_ChargeUse and int(self.part_EnergyAmmoLoader_ChargeUse) > 0:
            if self.part_EnergyCellSocket and self.part_EnergyCellSocket_SlotType == 'EnergyCell':
                ammo = 'energy'
            elif self.part_LiquidFueledPowerPlant:
                ammo = self.part_LiquidFueledPowerPlant_Liquid
        elif self.part_LiquidAmmoLoader:
            ammo = self.part_LiquidAmmoLoader_Liquid
        return ammo

    @property
    def ammodamagetypes(self) -> Union[list, None]:
        """Damage attributes associated with the projectile.

        Example: ["Exsanguination", "Disintegrate"] for ProjectileBloodGradientHandVacuumPulse"""
        attributes = self.projectile_object('part_Projectile_Attributes')
        if attributes is not None:
            return attributes.split()

    @property
    def aquatic(self) -> Union[bool, None]:
        """If the creature requires to be submerged in water."""
        if self.inherits_from('Creature'):
            if self.part_Brain_Aquatic is not None:
                return True if self.part_Brain_Aquatic == "true" else False

    @property
    def av(self) -> Union[int, None]:
        """The AV that an item provides, or the AV that a creature has."""
        av = None
        if self.part_Armor_AV:  # the AV of armor
            av = self.part_Armor_AV
        if self.part_Shield_AV:  # the AV of a shield
            av = self.part_Shield_AV
        if any(self.inherits_from(character) for character in ALL_CHARS):
            # the AV of creatures and stationary objects
            av = int(self.stat_AV_Value)  # first, creature's intrinsic AV
            if self.inventoryobject:
                # might be wearing armor
                for name in list(self.inventoryobject.keys()):
                    if name[0] in '*#@':
                        # special values like '*Junk 1'
                        continue
                    item = self.qindex[name]
                    if item.av:
                        av += int(item.av)
        return int_or_none(av)

    @property
    def bits(self) -> Union[str, None]:
        """The bits you can get from disassembling the object.

        Example: "0034" for the spiral borer"""
        if self.part_TinkerItem and (self.part_TinkerItem_CanDisassemble != 'false' or
                                     self.part_TinkerItem_CanBuild != 'false'):
            return self.part_TinkerItem_Bits.translate(BIT_TRANS)

    @property
    def bleedliquid(self) -> Union[str, None]:
        """What liquid something bleeds. Only returns interesting liquids (not blood)"""
        if self.is_specified('part_BleedLiquid'):
            liquid = self.part_BleedLiquid.split('-')[0]
            if liquid != "blood":  # it's interesting if they don't bleed blood
                return liquid

    @property
    def bookid(self) -> Union[str, None]:
        """The id of this object in books.xml."""
        return self.part_Book_ID

    @property
    def butcheredinto(self) -> Union[str, None]:
        """What a corpse item can be butchered into."""
        return self.part_Butcherable_OnSuccess

    @property
    def canbuild(self) -> Union[bool, None]:
        """Whether or not the player can tinker up this item."""
        if self.part_TinkerItem_CanBuild == 'true':
            return True
        elif self.part_TinkerItem_CanDisassemble == 'true':
            return False  # it's interesting if an item can't be built but can be disassembled

    @property
    def candisassemble(self) -> Union[bool, None]:
        """Whether or not the player can disassemble this item."""
        if self.part_TinkerItem_CanDisassemble == 'true':
            return True
        elif self.part_TinkerItem_CanBuild == 'true':
            return False  # it's interesting if an item can't be disassembled but can be built

    @property
    def carrybonus(self) -> Union[int, None]:
        """The carry weight bonus."""
        return int_or_none(self.part_Armor_CarryBonus)

    @property
    def chargeperdram(self) -> Union[int, None]:
        """How much charge is available per dram (for liquid-fueled cells or machines)."""
        return int_or_none(self.part_LiquidFueledEnergyCell_ChargePerDram)

    @property
    def chargeused(self) -> Union[int, None]:
        """How much charge is used per shot."""
        charge = None
        if self.part_VibroWeapon and int(self.part_VibroWeapon_ChargeUse) > 0:
            charge = self.part_VibroWeapon_ChargeUse
        if self.part_Gaslight and int(self.part_Gaslight_ChargeUse) > 0:
            charge = self.part_Gaslight_ChargeUse
        parts = ['StunOnHit',
                 'EnergyAmmoLoader',
                 'MechanicalWings',
                 'GeomagneticDisc',
                 'ProgrammableRecoiler',
                 'Teleporter',
                 'LatchesOn']
        for part in parts:
            if getattr(self, f'part_{part}'):
                charge = getattr(self, f'part_{part}_ChargeUse')
        return int_or_none(charge)

    @property
    def chargefunction(self) -> Union[str, None]:
        """The features or functions that the charge is used for.

        Intended to provide clarity for items like Prayer Rod, where charge only affects one of
        its features (stun) and not the other (elemental damage)."""
        funcs = []
        if self.part_StunOnHit:
            funcs.append('stun effect')
        if self.part_EnergyAmmoLoader or self.part_Gaslight:
            funcs.append('weapon power')
        if self.part_VibroWeapon and int(self.part_VibroWeapon_ChargeUse) > 0:
            funcs.append('adaptive penetration')
        if self.part_MechanicalWings:
            funcs.append('flight')
        if self.part_GeomagneticDisk:
            funcs.append('disc effect')
        if self.part_ProgrammableRecoiler or self.part_Teleporter:
            funcs.append('teleportation')
        if len(funcs) == 0:
            return None
        else:
            return ', '.join(funcs).capitalize()

    @property
    def cold(self) -> Union[int, None]:
        """The elemental resistance/weakness the equipment or NPC has."""
        return self.resistance('Cold')

    @property
    def colorstr(self) -> Union[str, None]:
        """The Qud color code associated with the RenderString."""
        if self.part_Render_ColorString:
            return self.part_Render_ColorString
        if self.part_Gas_ColorString:
            return self.part_Gas_ColorString

    @property
    def commerce(self) -> Union[float, None]:
        """The value of the object."""
        if self.inherits_from('Item') or self.inherits_from('BaseThrownWeapon'):
            value = self.part_Commerce_Value
            if value is not None:
                return float(value)

    @property
    def complexity(self) -> Union[int, None]:
        """The complexity of the object, used for psychometry."""
        if self.part_Examiner_Complexity is None:
            val = 0
        else:
            val = int(self.part_Examiner_Complexity)
        if self.part_AddMod_Mods is not None:
            modprops = ITEM_MOD_PROPS
            for mod in self.part_AddMod_Mods.split(','):
                if mod in modprops:
                    if (modprops[mod]['ifcomplex'] is True) and (val <= 0):
                        continue  # no change because the item isn't already complex
                    val += int(modprops[mod]['complexity'])
        for key in self.part.keys():
            if key.startswith('Mod'):
                modprops = ITEM_MOD_PROPS
                if key in modprops:
                    if (modprops[key]['ifcomplex'] is True) and (val <= 0):
                        continue  # ditto
                    val += int(modprops[key]['complexity'])
        if val > 0 or self.canbuild:
            return val

    @property
    def cookeffect(self) -> Union[list, None]:
        """The possible cooking effects of an item."""
        ingred_type = self.part_PreparedCookingIngredient_type
        if ingred_type is not None:
            return ingred_type.split(',')

    @property
    def corpse(self) -> Union[str, None]:
        """What corpse a character drops."""
        if self.part_Corpse_CorpseBlueprint is not None and int(self.part_Corpse_CorpseChance) > 0:
            return self.part_Corpse_CorpseBlueprint

    @property
    def corpsechance(self) -> Union[str, None]:
        """The chance of a corpse dropping, if corpsechance is >0"""
        chance = self.part_Corpse_CorpseChance
        if chance is not None and int(chance) > 0:
            return int(chance)

    @property
    def cursed(self) -> Union[bool, None]:
        """If the item cannot be removed by normal circumstances."""
        if self.part_Cursed is not None:
            return True

    @property
    def damage(self) -> Union[str, None]:
        """The damage dealt by this object. Often a dice string."""
        val = None
        if self.inherits_from('MeleeWeapon') or self.is_specified('part_MeleeWeapon'):
            val = self.part_MeleeWeapon_BaseDamage
        if self.part_Gaslight:
            val = self.part_Gaslight_ChargedDamage
        if self.is_specified('part_ThrownWeapon'):
            if self.is_specified('part_GeomagneticDisk'):
                val = self.part_GeomagneticDisk_Damage
            else:
                val = self.part_ThrownWeapon_Damage
        projectiledamage = self.projectile_object('part_Projectile_BaseDamage')
        if projectiledamage:
            val = projectiledamage
        return val

    @property
    def demeanor(self) -> Union[str, None]:
        """The demeanor of the creature."""
        if any(self.inherits_from(character) for character in ACTIVE_CHARS):
            if self.part_Brain_Calm is not None:
                return "docile" if self.part_Brain_Calm.lower() == "true" else "neutral"
            if self.part_Brain_Hostile is not None:
                return "aggressive" if self.part_Brain_Hostile.lower() == "true" else "neutral"

    @property
    def desc(self) -> Union[str, None]:
        """The short description of the object, with color codes included (ampersands escaped)."""
        desc = None
        if self.part_Description_Short == 'A hideous specimen.':
            pass  # hide items with default description
        elif self.intproperty_GenotypeBasedDescription is not None:
            desc = f"[True kin]\n{self.property_TrueManDescription_Value}\n\n" \
                   f"[Mutant]\n{self.property_MutantDescription_Value}"
        elif self.part_Description_Short:
            if self.part_Description_Mark:
                desc = self.part_Description_Short + "\n\n" + self.part_Description_Mark
            else:
                desc = self.part_Description_Short
        if desc is not None:
            if self.part_BonusPostfix is not None:
                desc += "\n\n" + self.part_BonusPostfix_Postfix
            desc = desc.replace('\r\n', '\n')  # currently, only the description for Bear
        return desc

    @property
    def destroyonunequip(self) -> Union[bool, None]:
        """If the object is destroyed on unequip."""
        if self.part_DestroyOnUnequip is not None:
            return True

    @property
    def displayname(self) -> Union[str, None]:
        """The display name of the object, with color codes removed. Used in UI and wiki."""
        dname = ""
        if self.part_Render_DisplayName is not None:
            dname = self.part_Render_DisplayName
            dname = strip_oldstyle_qud_colors(dname)
            dname = strip_newstyle_qud_colors(dname)
        return dname

    @property
    def dramsperuse(self) -> Union[int, None]:
        """The number of drams of liquid consumed by each shot action."""
        if self.is_specified('part_LiquidAmmoLoader'):
            return 1  # LiquidAmmoLoader always uses 1 dram per action
        # TODO: calculate fractional value for blood-gradient hand vacuum

    @property
    def dv(self) -> Union[int, None]:
        """The Dodge Value of this object."""
        dv = None
        if self.inherits_from('Armor'):
            # if this object is armor, the 'DV' we are interested in is the DV modifier of the armor
            armor_dv = self.part_Armor_DV
            if armor_dv is not None:
                dv = int(armor_dv)
        if self.inherits_from('Shield'):
            # same as above
            shield_dv = self.part_Shield_DV
            if shield_dv is not None:
                dv = int(shield_dv)
        elif any(self.inherits_from(character) for character in INACTIVE_CHARS):
            dv = -10
        elif any(self.inherits_from(character) for character in ACTIVE_CHARS):
            # the 'DV' here is the actual DV of the creature or NPC, after:
            # base of 6 plus any explicit DV bonus,
            # skills, agility modifier (which may be a range determined by
            # dice rolls, and which changes DV by 1 for every 2 points of agility
            # over/under 16), and any equipment that is guaranteed to be worn
            if self.is_specified('part_Brain_Mobile') and (self.part_Brain_Mobile == 'false' or
                                                           self.part_Brain_Mobile == 'False'):
                dv = -10
            else:
                dv = 6
                if self.stat_DV_Value is not None:
                    dv += int(self.stat_DV_Value)
                if self.skill_Acrobatics_Dodge:  # the 'Spry' skill
                    dv += 2
                if self.skill_Acrobatics_Tumble:  # the 'Tumble' skill
                    dv += 1
                dv += self.attribute_helper_mod('Agility')
                # does this creature have armor with DV modifiers to add?
                if self.inventoryobject:
                    for name in list(self.inventoryobject.keys()):
                        if name[0] in '*#@':
                            # special values like '*Junk 1'
                            continue
                        item = self.qindex[name]
                        if item.dv is not None:
                            dv += item.dv
                # does this creature have mutations that affect DV?
                if self.mutation:
                    for mutation, info in self.mutation.items():
                        if mutation == 'Carapace':
                            lvl = int(info['Level']) + 1
                            dv -= (7 - (lvl // 2))
        return int_or_none(dv)

    @property
    def dynamictable(self) -> Union[list, None]:
        """What dynamic tables the object is a member of.

        Returns a list of strings, the dynamic tables."""
        if self.tag_ExcludeFromDynamicEncounters is not None:
            return None
        tables = []
        for key, val in self.tag.items():
            if key.startswith('DynamicObjectsTable'):
                if 'Value' in val and val['Value'] == '{{{remove}}}':
                    continue  # explicitly disallowed from an inherited dynamic table
                tables.append(key.split(':')[1])
        return tables if len(tables) > 0 else None

    @property
    def eatdesc(self) -> Union[str, None]:
        """The text when you eat this item."""
        return self.part_Food_Message

    @property
    def ego(self) -> Union[str, None]:
        """The ego the mutation effects, or the ego of the creature."""
        val = self.attribute_helper('Ego')
        return f"{val}+3d1" if self.name == "Wraith-Knight Templar" else val

    @property
    def electric(self) -> Union[int, None]:
        """The elemental resistance/weakness the equipment or NPC has."""
        return self.resistance('Electric')

    @property
    def elementaldamage(self) -> Union[str, None]:
        """The elemental damage dealt, if any, as a range."""
        if self.is_specified('part_ModFlaming'):
            tierstr = self.part_ModFlaming_Tier
            elestr = str(int(int(tierstr) * 0.8)) + '-' + str(int(int(tierstr) * 1.2))
        elif self.is_specified('part_ModFreezing'):
            tierstr = self.part_ModFreezing_Tier
            elestr = str(int(int(tierstr) * 0.8)) + '-' + str(int(int(tierstr) * 1.2))
        elif self.is_specified('part_ModElectrified'):
            tierstr = self.part_ModElectrified_Tier
            elestr = str(int(tierstr)) + '-' + str(int(int(tierstr) * 1.5))
        else:
            elestr = self.part_MeleeWeapon_ElementalDamage
        return elestr

    @property
    def elementaltype(self) -> Union[str, None]:
        """For elemental damage dealt, what the type of that damage is."""
        if self.is_specified('part_ModFlaming'):
            elestr = 'Fire'
        elif self.is_specified('part_ModFreezing'):
            elestr = 'Cold'
        elif self.is_specified('part_ModElectrified'):
            elestr = 'Electric'
        else:
            elestr = self.part_MeleeWeapon_Element
        return elestr

    @property
    def empsensitive(self) -> Union[bool, None]:
        """Returns yes if the object is empensitive. Can be found in multiple parts."""
        parts = ['EquipStatBoost',
                 'BootSequence',
                 'NavigationBonus',
                 'SaveModifier',
                 'LiquidFueledPowerPlant',
                 'LiquidProducer',
                 'TemperatureAdjuster'
                 ]
        if any(getattr(self, f'part_{part}_IsEMPSensitive') == 'true' for part in parts):
            return True
        parts = ['EnergyCellSocket',
                 'ZeroPointEnergyCollector',
                 'ModFlaming',
                 'ModFreezing',
                 'ModElectrified']
        if any(getattr(self, f'part_{part}') is not None for part in parts):
            return True

    @property
    def energycellrequired(self) -> Union[bool, None]:
        """Returns True if the object requires an energy cell to function."""
        if self.is_specified('part_EnergyCellSocket'):
            return True

    @property
    def exoticfood(self) -> Union[bool, None]:
        """When preserved, whether the player must explicitly agree to preserve it."""
        if self.tag_ChooseToPreserve is not None:
            return True

    @property
    def faction(self) -> Union[list, None]:
        """The factions this creature has loyalty to.

        Returned as a list of tuples of faction, value like
        [('Joppa', 100), ('Barathrumites', 100)]

        Example XML source:
        <part Name="Brain" Wanders="false" Factions="Joppa-100,Barathrumites-100" />
        """
        ret = None
        if self.part_Brain_Factions:
            ret = []
            for part in self.part_Brain_Factions.split(','):
                if '-' in part:
                    # has format like `Joppa-100,Barathrumites-100`
                    faction, value = part.split('-')
                    ret.append((faction, int(value)))
                else:
                    print(f'FIXME: unexpected faction format: {part} in {self.name}')
        return ret

    @property
    def flametemperature(self) -> Union[int, None]:
        """The temperature that this object sets on fire. Only for items."""
        if self.inherits_from('Item') and self.is_specified('part_Physics'):
            return int_or_none(self.part_Physics_FlameTemperature)

    @property
    def flyover(self) -> Union[bool, None]:
        """Whether a flying creature can pass over this object."""
        if self.inherits_from('Wall') or self.inherits_from('Furniture'):
            if self.tag_Flyover is not None:
                return True
            else:
                return False

    @property
    def gasemitted(self) -> Union[str, None]:
        """The gas emitted by the weapon (typically missile weapon 'pumps')."""
        return self.projectile_object('part_GasOnHit_Blueprint')

    @property
    def gender(self) -> Union[str, None]:
        """The gender of the object."""
        if self.tag_Gender_Value is not None and any(self.inherits_from(character) for
                                                     character in ACTIVE_CHARS):
            return self.tag_Gender_Value

    @property
    def harvestedinto(self) -> Union[str, None]:
        """What an item produces when harvested."""
        return self.part_Harvestable_OnSuccess

    @property
    def healing(self) -> Union[str, None]:
        """How much a food item heals when used.

        Example: "1d16+24" for Witchwood Bark"""
        return self.part_Food_Healing

    @property
    def heat(self) -> Union[int, None]:
        """The elemental resistance/weakness the equipment or NPC has."""
        return self.resistance('Heat')

    @property
    def hidden(self) -> Union[int, None]:
        """If hidden, what difficulty is required to find them.

        Example: 15 for Yonderbrush"""
        return int_or_none(self.part_Hidden_Difficulty)

    @property
    def hp(self) -> Union[str, None]:
        """The hitpoints of a creature or object.

        Returned as a string because some hitpoints are given as sValues, which can be
        strings, although they currently are not using this feature."""
        if any(self.inherits_from(character) for character in ALL_CHARS):
            if self.stat_Hitpoints_sValue is not None:
                return self.stat_Hitpoints_sValue
            elif self.stat_Hitpoints_Value is not None:
                return self.stat_Hitpoints_Value

    @property
    def hunger(self) -> Union[str, None]:
        """How much hunger it satiates.

        Example: "Snack" for Vanta Petals"""
        return self.part_Food_Satiation

    @property
    def id(self) -> str:
        """The name of the object in ObjectBlueprints.xml. Should always exist."""
        return self.name

    @property
    def illoneat(self) -> Union[bool, None]:
        """If eating this makes you sick."""
        if not self.inherits_from('Corpse'):
            if self.part_Food_IllOnEat == 'true':
                return True

    @property
    def inheritingfrom(self) -> Union[str, None]:
        """The ID of the parent object in the Qud object hierarchy.

        Only the root object ("Object") should return None for this."""
        return self.parent.name

    @property
    def intelligence(self) -> Union[str, None]:
        """The intelligence the mutation affects, or the intelligence of the creature."""
        return self.attribute_helper('Intelligence')

    @property
    def inventory(self) -> List[Tuple[str, str, str, str]]:
        """The inventory of a character.

        Returns a list of tuples of strings: (name, count, equipped, chance)."""
        inv = self.inventoryobject
        if inv is not None:
            ret = []
            for name in inv:
                if name[0] in '*#@':  # Ignores stuff like '*Junk 1'
                    continue
                count = inv[name].get('Number', '1')
                equipped = 'no'  # not yet implemented
                chance = inv[name].get('Chance', '100')
                ret.append((name, count, equipped, chance))
            return ret

    @property
    def iscurrency(self) -> Union[bool, None]:
        """If the item is considered currency (price remains fixed while trading)."""
        if self.intproperty_Currency_Value == '1':
            return True

    @property
    def isfungus(self) -> Union[bool, None]:
        """If the food item contains fungus."""
        if self.tag_Mushroom is not None:
            return True

    @property
    def ismeat(self) -> Union[bool, None]:
        """If the food item contains meat."""
        if self.tag_Meat is not None:
            return True

    @property
    def isoccluding(self) -> Union[bool, None]:
        if self.part_Render_Occluding is not None:
            if self.part_Render_Occluding == 'true' or self.part_Render_Occluding == 'True':
                return True

    @property
    def isplant(self) -> Union[bool, None]:
        """If the food item contains plants."""
        if self.tag_Plant is not None:
            return True

    @property
    def isswarmer(self) -> Union[bool, None]:
        """Whether a creature is a Swarmer."""
        if self.inherits_from('Creature'):
            if self.is_specified('part_Swarmer'):
                return True

    @property
    def lightprojectile(self) -> Union[bool, None]:
        """If the gun fires light projectiles (heat immune creatures will not take damage)."""
        if self.tag_Light is not None:
            return True

    @property
    def lightradius(self) -> Union[int, None]:
        """Radius of light the object gives off."""
        return int_or_none(self.part_LightSource_Radius)

    @property
    def liquidgen(self) -> Union[int, None]:
        """For liquid generators. how many turns it takes for 1 dram to generate."""
        # TODO: is this correct?
        return int_or_none(self.part_LiquidProducer_Rate)

    @property
    def liquidtype(self) -> Union[str, None]:
        """For liquid generators, the type of liquid generated."""
        return self.part_LiquidProducer_Liquid

    @property
    def liquidburst(self) -> Union[str, None]:
        """If it explodes into liquid, what kind?"""
        return self.part_LiquidBurst_Liquid

    @property
    def lv(self) -> Union[str, None]:
        """The object's level.

        Returned as a string because it may be possible for it to be an sValue, as in
        Barathrumite_FactionMemberMale which has a level sValue of "18-29"."""
        level = self.stat_Level_sValue
        if level is None:
            level = self.stat_Level_Value
        return level

    @property
    def ma(self) -> Union[int, None]:
        """The object's mental armor."""
        if self.part_MentalShield is not None:
            # things like Water, Stairs, etc. are not subject to mental effects.
            return None
        elif any(self.inherits_from(character) for character in INACTIVE_CHARS):
            return 0
        elif any(self.inherits_from(character) for character in ACTIVE_CHARS):
            # MA starts at base 4
            ma = 4
            # Add MA stat value if specified
            if self.stat_MA_Value:
                ma += int(self.stat_MA_Value)
            # add willpower modifier to MA
            ma += self.attribute_helper_mod('Willpower')
            return ma

    @property
    def maxammo(self) -> Union[int, None]:
        """How much ammo a gun can have loaded at once."""
        return int_or_none(self.part_MagazineAmmoLoader_MaxAmmo)

    @property
    def maxcharge(self) -> Union[int, None]:
        """How much charge it can hold (usually reserved for cells)."""
        return int_or_none(self.part_EnergyCell_MaxCharge)

    @property
    def maxvol(self) -> Union[int, None]:
        """The maximum liquid volume."""
        return int_or_none(self.part_LiquidVolume_MaxVolume)

    @property
    def maxpv(self) -> Union[int, None]:
        """The max strength bonus + our base PV."""
        if self.is_specified('part_ThrownWeapon'):
            pv = int_or_none(self.part_ThrownWeapon_Penetration)
            if pv is None:
                pv = 1
        else:
            pv = self.pv
            if pv is not None:
                if self.part_MeleeWeapon_MaxStrengthBonus is not None:
                    pv += int(self.part_MeleeWeapon_MaxStrengthBonus)
        return pv

    @property
    def metal(self) -> Union[bool, None]:
        """Whether the object is made out of metal."""
        if self.part_Metal is not None:
            return True

    @property
    def modcount(self) -> Union[int, None]:
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
            if key.startswith('Mod'):
                val += 1
        return val if val > 0 else None

    @property
    def mods(self) -> Union[List[Tuple[str, int]], None]:
        """Mods that are attached to the current item.

        Returns a list of tuples like [(modid, tier), ...].
        """
        mods = []
        if self.part_AddMod_Mods is not None:
            names = self.part_AddMod_Mods.split(',')
            if self.part_AddMod_Tiers is not None:
                tiers = self.part_AddMod_Tiers.split(',')
                tiers = [int(tier) for tier in tiers]
            else:
                tiers = [1] * len(names)
            mods.extend(zip(names, tiers))
        for key in self.part.keys():
            if key.startswith('Mod'):
                if 'Tier' in self.part[key]:
                    mods.append((key, int(self.part[key]['Tier'])))
                else:
                    mods.append((key, 1))
        return mods if len(mods) > 0 else None

    @property
    def movespeed(self) -> Union[int, None]:
        """The movespeed of a creature."""
        if self.inherits_from('Creature'):
            return int_or_none(self.stat_MoveSpeed_Value)

    @property
    def movespeedbonus(self) -> Union[int, None]:
        """The movespeed bonus of an item."""
        if self.inherits_from('Item'):
            bonus = self.part_MoveCostMultiplier_Amount
            if bonus is not None:
                return -int(bonus)

    @property
    def mutations(self) -> Union[List[Tuple[str, int]], None]:
        """The mutations the creature has along with their level.

        Returns a list of tuples like [(name, level), ...].
        """
        if self.mutation is not None:  # direct reference to <mutation> XML tag - not a property
            mutations = []
            for mutation, data in self.mutation.items():
                postfix = f"{data['GasObject']}" if 'GasObject' in data else ''
                level = int(data['Level']) if 'Level' in data else 0
                mutations.append((mutation + postfix, level))
            return mutations

    @property
    def noprone(self) -> Union[List[bool, None]]:
        """Returns true if has part NoKnockdown."""
        if self.part_NoKnockdown is not None:
            return True

    @property
    def omniphaseprojectile(self) -> Union[bool, None]:
        projectile = self.projectile_object()
        if projectile.is_specified('part_OmniphaseProjectile') or \
                projectile.is_specified('tag_Omniphase'):
            return True

    @property
    def oneat(self) -> Union[List[str], None]:
        """Effects granted when the object is eaten.

        Returns a list of strings, which are the effects.
        Example:
            Transform <part Name="BreatheOnEat" Class="FireBreather" Level="5"></part>
            into ['BreatheOnEatFireBreather5']"""
        effects = []
        for key, val in self.part.items():
            if key.endswith('OnEat'):
                effect = key
                if 'Class' in val:
                    effect += val['Class']
                    effect += val['Level']
                effects.append(effect)
        return effects if len(effects) > 0 else None

    @property
    def penetratingammo(self) -> Union[bool, None]:
        """If the missile weapon's projectiles pierce through targets."""
        if self.projectile_object('part_Projectile_PenetrateCreatures') is not None:
            return True

    @property
    def pettable(self) -> Union[bool, None]:
        """If the creature is pettable."""
        if self.part_Pettable is not None:
            return True

    @property
    def preservedinto(self) -> Union[str, None]:
        """When preserved, what a preservable item produces."""
        return self.part_PreservableItem_Result

    @property
    def preservedquantity(self) -> Union[int, None]:
        """When preserved, how many preserves a preservable item produces."""
        return int_or_none(self.part_PreservableItem_Number)

    @property
    def pronouns(self) -> Union[str, None]:
        """Return the pronounset of a creature, if [they] have any."""
        if self.tag_PronounSet_Value is not None and self.inherits_from('Creature'):
            return self.tag_PronounSet_Value

    @property
    def pv(self) -> Union[int, None]:
        """The base PV, which is by default 4 if not set. Optional."""
        pv = None
        if self.inherits_from('MeleeWeapon') or self.is_specified('part_MeleeWeapon'):
            pv = 4
            if self.part_Gaslight_ChargedPenetrationBonus is not None:
                pv += int(self.part_Gaslight_ChargedPenetrationBonus)
            elif self.part_MeleeWeapon_PenBonus is not None:
                pv += int(self.part_MeleeWeapon_PenBonus)
        missilepv = self.projectile_object('part_Projectile_BasePenetration')
        if missilepv is not None:
            pv = int(missilepv) + 4  # add base 4 PV
        if pv is not None:
            return pv

    @property
    def pvpowered(self) -> Union[bool, None]:
        """Whether the object's PV changes when it is powered."""
        if ((self.vibro and
             (not self.part_VibroWeapon or int(self.part_VibroWeapon_ChargeUse) > 0)) or
                (self.part_Gaslight and int(self.part_Gaslight_ChargeUse) > 0)):
            return True

    @property
    def quickness(self) -> Union[int, None]:
        """Return quickness of a creature"""
        if self.inherits_from('Creature'):
            return int_or_none(self.stat_Speed_Value)

    @property
    def reflect(self) -> Union[int, None]:
        """If it reflects, what percentage of damage is reflected."""
        return int_or_none(self.part_ModGlassArmor_Tier)

    @property
    def renderstr(self) -> Union[str, None]:
        """The character used to render this object in ASCII mode."""
        render = None
        if self.part_Render_RenderString and len(self.part_Render_RenderString) > 1:
            # some RenderStrings are given as CP437 character codes in base 10
            render = cp437_to_unicode(int(self.part_Render_RenderString))
        elif self.part_Gas is not None:
            render = '▓'
        elif self.part_Render_RenderString is not None:
            render = self.part_Render_RenderString
        return render

    @property
    def reputationbonus(self) -> Union[List[Tuple[str, int]], None]:
        """Reputation bonuses granted by the object.

        Returns a list of tuples like [(faction, value), ...].
        """
        # Examples of XML source formats:
        # <part Name="AddsRep" Faction="Apes" Value="-100" />
        # <part Name="AddsRep" Faction="Antelopes,Goatfolk" Value="100" />
        # <part Name="AddsRep" Faction="Fungi:200,Consortium:-200" />
        if self.part_AddsRep:
            reps = []
            for part in self.part_AddsRep_Faction.split(','):
                if ':' in part:
                    # has format like `Fungi:200,Consortium:-200`
                    faction, value = part.split(':')
                else:
                    # has format like `Antelopes,Goatfolk` and Value `100`
                    # or is a single faction, like `Apes` and Value `-100`
                    faction = part
                    value = self.part_AddsRep_Value
                value = int(value)
                reps.append((faction, value))
            return reps

    @property
    def role(self) -> Union[str, None]:
        """What role a creature or object has assigned.

        Example: Programmable Recoiler has "Uncommon"
        Albino ape has "Brute"
        """
        return self.property_Role_Value

    @property
    def savemodifier(self) -> Union[str, None]:
        """Returns save modifier type"""
        return self.part_SaveModifier_Vs

    @property
    def savemodifieramt(self) -> Union[int, None]:
        """returns amount of the save modifer."""
        if self.part_SaveModifier_Vs is not None:
            return int_or_none(self.part_SaveModifier_Amount)

    @property
    def shotcooldown(self) -> Union[str, None]:
        """Cooldown before weapon can be fired again, typically a dice string."""
        return self.part_CooldownAmmoLoader_Cooldown

    @property
    def shots(self) -> Union[int, None]:
        """How many shots are fired in one round."""
        return int_or_none(self.part_MissileWeapon_ShotsPerAction)

    @property
    def skills(self) -> Union[str, None]:
        """The skills that certain creatures have."""
        if self.skill is not None:
            return self.skill

    @property
    def solid(self) -> Union[bool, None]:
        if self.is_specified('part_Physics_Solid'):
            if self.part_Physics_Solid == 'true' or self.part_Physics_Solid == 'True':
                return True
            else:
                return False

    @property
    def spectacles(self) -> Union[bool, None]:
        """If the item corrects vision."""
        return True if self.part_Spectacles is not None else None

    @property
    def strength(self) -> Union[str, None]:
        """The strength the mutation affects, or the strength of the creature."""
        return self.attribute_helper('Strength')

    @property
    def swarmbonus(self) -> Union[int, None]:
        """The additional bonus that Swarmers receive."""
        return int_or_none(self.part_Swarmer_ExtraBonus)

    @property
    def temponenter(self) -> Union[str, None]:
        """Temperature change caused to objects when weapon/projectile passes through cell.

        Can be a dice string."""
        var = self.projectile_object('part_TemperatureOnEntering_Amount')  # projectiles
        return var or self.part_TemperatureOnEntering_Amount  # melee weapons, etc.

    @property
    def temponhit(self) -> Union[str, None]:
        """Temperature change caused by weapon/projectile hit.

        Can be a dice string."""
        var = self.projectile_object('part_TemperatureOnHit_Amount')
        return var or self.part_TemperatureOnHit_Amount

    @property
    def temponhitmax(self) -> Union[int, None]:
        """Temperature change effect does not occur if target has already reached MaxTemp."""
        temp = self.projectile_object('part_TemperatureOnHit_MaxTemp')
        if temp is not None:
            return int(temp)
        temp = self.part_TemperatureOnHit_MaxTemp
        if temp is not None:
            return int(temp)

    @property
    def thirst(self) -> Union[int, None]:
        """How much thirst it slakes."""
        return int_or_none(self.part_Food_Thirst)

    @property
    def tier(self) -> Union[int, None]:
        """Returns tier. Returns the Specified tier if it isn't inherited. Else it will return
        the highest value bit (if tinkerable) or its FLOOR(Level/5), if neither of these exist,
        it will return the inherited tier value."""
        if not self.is_specified('tag_Tier_Value'):
            if self.is_specified('part_TinkerItem_Bits'):
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
                    level = int(self.lv.split('-')[0])
                return level // 5
        return int_or_none(self.tag_Tier_Value)

    @property
    def title(self) -> Union[str, None]:
        """The display name of the item."""
        val = self.name
        if self.builder_GoatfolkHero1_ForceName:
            val = self.builder_GoatfolkHero1_ForceName  # for Mamon
        elif self.name == "Wraith-Knight Templar":
            val = "&MWraith-Knight Templar of the Binary Honorum"  # override for Wraith Knights
        elif self.name == 'TreeSkillsoft':
            val = '&YSkillsoft Plus'  # override for Skillsoft Plus
        elif self.name == 'SingleSkillsoft1':
            val = '&YSkillsoft [&Wlow sp&Y]'  # override for Skillsoft [0-50sp]
        elif self.name == 'SingleSkillsoft2':
            val = '&YSkillsoft [&Wmedium sp&Y]'  # override for Skillsoft [51-150]
        elif self.name == 'SingleSkillsoft3':
            val = '&YSkillsoft [&Whigh sp&Y]'  # override for Skillsoft [151+]
        elif self.name == 'Schemasoft2':
            val = '&YSchemasoft [&Wlow-tier&Y]'  # override for Schemasoft [low-tier]
        elif self.name == 'Schemasoft3':
            val = '&YSchemasoft [&Wmid-tier&Y]'  # override for Schemasoft [mid-tier]
        elif self.name == 'Schemasoft4':
            val = '&YSchemasoft [&Whigh-tier&Y]'  # override for Schemasoft [high-tier]
        elif self.part_Render_DisplayName:
            val = self.part_Render_DisplayName
        return val

    @property
    def tohit(self) -> Union[int, None]:
        """The bonus or penalty to hit."""
        if self.inherits_from('Armor'):
            return int_or_none(self.part_Armor_ToHit)
        if self.is_specified('part_MeleeWeapon'):
            return int_or_none(self.part_MeleeWeapon_HitBonus)

    @property
    def toughness(self) -> Union[str, None]:
        """The toughness the mutation affects, or the toughness of the creature."""
        return self.attribute_helper('Toughness')

    @property
    def twohanded(self) -> Union[bool, None]:
        """Whether this is a two-handed item."""
        if self.inherits_from('MeleeWeapon') or self.inherits_from('MissileWeapon'):
            if self.tag_UsesSlots and self.tag_UsesSlots != 'Hand':
                return None  # exclude things like Slugsnout Snout
            if self.part_Physics_bUsesTwoSlots or self.part_Physics_UsesTwoSlots:
                return True
            return False

    @property
    def unpowereddamage(self) -> Union[str, None]:
        """For weapons that use charge, the damage dealt when unpowered.

        Given as a dice string."""
        return self.part_Gaslight_UnchargedDamage

    @property
    def usesslots(self) -> Union[List[str], None]:
        """Return the body slots taken up by equipping this item.

        This is not the same as the slot the item is equipped "to", which is given by wornon

        Example: Portable Beehive returns ["Back", "Floating Nearby"].
        """
        if self.tag_UsesSlots_Value is not None:
            return self.tag_UsesSlots_Value.split(',')

    @property
    def vibro(self) -> Union[bool, None]:
        """Whether this is a vibro weapon."""
        if self.is_specified('part_ThrownWeapon'):
            if self.is_specified('part_GeomagneticDisk'):
                return True
            else:
                return False
        elif self.inherits_from('NaturalWeapon') or self.inherits_from('MeleeWeapon'):
            if self.part_VibroWeapon:
                return True
            return False

    @property
    def waterritualable(self) -> Union[bool, None]:
        """Whether the creature is waterritualable."""
        if self.is_specified('xtag_WaterRitual') or self.part_GivesRep is not None:
            return True

    @property
    def weaponskill(self) -> Union[str, None]:
        """The skill tree required for use."""
        val = None
        if self.inherits_from('MeleeWeapon') or self.is_specified('part_MeleeWeapon'):
            val = self.part_MeleeWeapon_Skill
        if self.inherits_from('MissileWeapon'):
            if self.part_MissileWeapon_Skill is not None:
                val = self.part_MissileWeapon_Skill
        if self.part_Gaslight:
            val = self.part_Gaslight_ChargedSkill
        # disqualify various things from showing the 'cudgel' skill:
        if self.inherits_from('Projectile'):
            val = None
        if self.inherits_from('Shield'):
            val = 'Shield'
        return val

    @property
    def weight(self) -> Union[int, None]:
        """The weight of the object."""
        if not self.inherits_from('Creature'):
            return int_or_none(self.part_Physics_Weight)

    @property
    def willpower(self) -> Union[str, None]:
        """The willpower the mutation affects, or the willpower of the creature."""
        return self.attribute_helper('Willpower')

    @property
    def wornon(self) -> Union[str, None]:
        """The body slot that an item gets equipped to.

        Not the same as the body slots it occupies once equipped, which is given by usesslots."""
        wornon = None
        if self.part_Shield_WornOn:
            wornon = self.part_Shield_WornOn
        if self.part_Armor_WornOn:
            wornon = self.part_Armor_WornOn
        if self.name == 'Hooks':
            wornon = 'Feet'  # manual fix
        return wornon
