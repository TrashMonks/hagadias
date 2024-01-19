"""Various constants that are unlikely to change."""

# Cherubim description templates
CHERUBIM_DESC = "Gallium veins press against the underside of =pronouns.possessive= crystalline *skin* and gleam warmly. =pronouns.Possessive= body is perfect, and the whole of it is wet with amniotic slick; could =pronouns.subjective= have just now peeled =pronouns.reflexive= off an oil canvas? =verb:Were:afterpronoun= =pronouns.subjective= cast into the material realm by a dreaming, dripping brain? Whatever the embryo, =pronouns.subjective= =verb:are:afterpronoun= now the archetypal *creatureType*; it's all there in impeccable simulacrum: *features*. Perfection is realized."  # noqa E501
MECHANICAL_CHERUBIM_DESC = "Dials tick and vacuum tubes mantle under synthetic *skin* and inside plastic joints. *features* are wrought from a vast and furcate machinery into the ideal form of the *creatureType*. By the artistry of =pronouns.possessive= construction, =pronouns.subjective= closely =verb:resemble:afterpronoun= =pronouns.possessive= referent, but an exposed cog here and an exhaust valve there betray the truth of =pronouns.possessive= nature. =pronouns.Possessive= movements are short and mimetic; =pronouns.subjective= =verb:inhabit:afterpronoun= the valley between the mountains of life and imagination."  # noqa E501
# BIT_TRANS: convert between the bit codes found in XML and the ones shown ingame.
bit_table = {
    "G": "B",
    "R": "A",
    "C": "D",
    "B": "C",
}
BIT_TRANS = "".maketrans(bit_table)
# ITEM_MOD_PROPS: difficulty and complexity changes when a mod is applied to an item
# ifcomplex means the change only applies if the item already has complexity > 0
# these values live in code, usually in ApplyModification() method of the Mod's .cs file
ITEM_MOD_PROPS = {
    "ModCounterweighted": {
        "complexity": 1,
        "difficulty": 1,
        "ifcomplex": True,
        "prefix": "&ycounterweighted ",
    },
    "ModElectrified": {
        "complexity": 1,
        "difficulty": 1,
        "ifcomplex": False,
        "prefix": "&Welectrified&y ",
    },
    "ModEngraved": {
        "complexity": 0,
        "difficulty": 0,
        "ifcomplex": False,
        "prefix": "&Ye&yn&cg&Cr&Ya&yv&ce&Cd &y",
    },
    "ModExtradimensional": {
        "complexity": 4,
        "difficulty": 8,
        "ifcomplex": True,
        "prefix": "&Me&Mx&mt&mr&ya&yd&Yi&Ym&" "Oe&Yn&Ys&yi&y&mo&mn&Ma&Ml&y ",
    },
    "ModFlaming": {"complexity": 1, "difficulty": 1, "ifcomplex": False, "prefix": "&Rflaming&y "},
    "ModFreezing": {
        "complexity": 1,
        "difficulty": 1,
        "ifcomplex": False,
        "prefix": "&Cfreezing&y ",
    },
    "ModGesticulating": {
        "complexity": 1,
        "difficulty": 1,
        "ifcomplex": False,
        "prefix": "&mgesticulating &y",
    },
    "ModGlassArmor": {"complexity": 0, "difficulty": 0, "ifcomplex": False},
    "ModHeatSeeking": {"complexity": 1, "difficulty": 1, "ifcomplex": True, "prefix": "&yhoming "},
    "ModImprovedElectricalGeneration": {"complexity": 0, "difficulty": 0, "ifcomplex": False},
    "ModImprovedTemporalFugue": {"complexity": 0, "difficulty": 0, "ifcomplex": False},
    "ModJewelEncrusted": {"complexity": 0, "difficulty": 0, "ifcomplex": False},
    "ModMasterwork": {
        "complexity": 1,
        "difficulty": 1,
        "ifcomplex": True,
        "prefix": "&Ymasterwork&y ",
    },
    "ModPainted": {
        "complexity": 0,
        "difficulty": 0,
        "ifcomplex": False,
        "prefix": "&rp&Ra&Wi&wn&gt&Ge&Bd &y",
    },
    "ModPiping": {
        "complexity": 0,
        "difficulty": 1,
        "ifcomplex": False,
        "postfix": " &ywith piping",
    },
    "ModRazored": {
        "complexity": 1,
        "difficulty": 1,
        "ifcomplex": True,
        "prefix": "&Yserra&Rt&Yed&y ",
    },
    "ModScoped": {"complexity": 1, "difficulty": 1, "ifcomplex": False, "prefix": "&yscoped "},
    "ModSharp": {"complexity": 1, "difficulty": 1, "ifcomplex": True, "prefix": "sharp "},
    "ModSpringLoaded": {
        "complexity": 1,
        "difficulty": 1,
        "ifcomplex": False,
        "prefix": "spring-loaded ",
    },
    "ModSturdy": {"complexity": 0, "difficulty": 0, "ifcomplex": False, "prefix": "sturdy "},
    "ModWired": {"complexity": 0, "difficulty": 1, "ifcomplex": True, "prefix": "&cwired &y"},
}
# This could be loaded from Factions.xml eventually, but for simplicity I'm putting it here for now.
FACTION_ID_TO_NAME = {
    "Antelopes": "antelopes",
    "Apes": "apes",
    "Arachnids": "arachnids",
    "Baboons": "baboons",
    "Baetyls": "baetyls",
    "Barathrumites": "Barathrumites",
    "Bears": "bears",
    "Birds": "birds",
    "Cannibals": "cannibals",
    "Cats": "cats",
    "Consortium": "Consortium of Phyta",
    "Crabs": "crabs",
    "Cragmensch": "cragmensch",
    "Daughters": "Daughters of Exile",
    "Dogs": "dogs",
    "Dromad": "dromad merchants",
    "Equines": "equines",
    "Ezra": "villagers of Ezra",
    "Farmers": "Farmers' Guild",
    "Fish": "fish",
    "Flowers": "flowers",
    "Frogs": "frogs",
    "Fungi": "fungi",
    "Girsh": "Girsh",
    "Glow Wights": "Glow-Wights",
    "Goatfolk": "goatfolk",
    "Hermits": "hermits",
    "highly entropic beings": "highly entropic beings",
    "Hindren": "hindren of Bey Lah",
    "Insects": "insects",
    "Issachari": "Issachari tribe",
    "Joppa": "villagers of Joppa",
    "Kyakukya": "villagers of Kyakukya",
    "Mamon": "Children of Mamon",
    "Mechanimists": "Mechanimists",
    "Merchants": "Merchants' Guild",
    "Mollusks": "mollusks",
    "Mopango": "mopango",
    "Naphtaali": "Naphtaali tribe",
    "Newly Sentient Beings": "newly sentient beings",
    "Oozes": "oozes",
    "Pariahs": "pariahs",
    "Prey": "grazing hedonists",
    "Resheph": "Cult of the Coiled Lamb",
    "Robots": "robots",
    "Roots": "roots",
    "Seekers": "Seekers of the Sightless Way",
    "Snapjaws": "snapjaws",
    "Strangers": "mysterious strangers",
    "Succulents": "succulents",
    "Swine": "swine",
    "Templar": "Putus Templar",
    "Tortoises": "tortoises",
    "Trees": "trees",
    "Trolls": "trolls",
    "Unshelled Reptiles": "unshelled reptiles",
    "Urchins": "urchins",
    "Vines": "vines",
    "Wardens": "Fellowship of Wardens",
    "Water": "water barons",
    "Winged Mammals": "winged mammals",
    "Worms": "worms",
}
CYBERNETICS_HARDCODED_INFIXES = {
    "CyberneticsMedassistModule": "{{c|Current loadout:}}{{y| no injectors}}"
}
COMPUTE = "Compute power on the local lattice"
INCREASES = "increases this item's effectiveness"
CYBERNETICS_HARDCODED_POSTFIXES = {
    "CyberneticsAnomalyFumigator": f"{COMPUTE} {INCREASES}.",
    "CyberneticsCommunicationsInterlock": f"{COMPUTE} {INCREASES}.",
    "CyberneticsCustomVisage": "+300 reputation with <chosen faction>",
    "CyberneticsHighFidelityMatterRecompositer": f"{COMPUTE} reduces this item's cooldown.",
    "CyberneticsInflatableAxons": f"{COMPUTE} {INCREASES}.",
    "CyberneticsMatterRecompositer": f"{COMPUTE} reduces this item's cooldown.",
    "CyberneticsNocturnalApex": f"{COMPUTE} {INCREASES}.",
    "CyberneticsOnboardRecoilerTeleporter": f"{COMPUTE} reduces this item's cooldown.",
    "CyberneticsCathedraBlackOpal": f"{COMPUTE} {INCREASES}.",
    "CyberneticsCathedraRuby": f"{COMPUTE} {INCREASES}.",
    "CyberneticsCathedraSapphire": f"{COMPUTE} {INCREASES}.",
    "CyberneticsCathedraWhiteOpal": f"{COMPUTE} {INCREASES}.",
    "CyberneticsPenetratingRadar": f"{COMPUTE} increases this item's range.",
    "CyberneticsStasisProjector": f"{COMPUTE} {INCREASES}.",
}
HARDCODED_CHARGE_USE = {
    "Displacer Bracelet": 1,
    "Force Bracelet": 500,
    "Neuro Animator": 5000,
    "Night-vision Goggles": 1,
    "Ninefold Boots": 250,
    "Slip Ring": 1,
    "Stopsvaalinn": 500,
    "Food Processor": 500,
}
CHARGE_USE_REASONS = {
    "Displacer Bracelet": "SpatialTransposer",
    "Force Bracelet": "ForceEmitter",
    "Neuro Animator": "Object Animation",
    "Night-vision Goggles": "Night Vision",
    "Ninefold Boots": "Accelerative Teleporter",
    "Slip Ring": "Slipperiness",
    "Stopsvaalinn": "ForceEmitter",
    "Food Processor": "Food Processing",
}
QUD_COLORS = {
    "r": (166, 74, 46),  # dark red
    "R": (215, 66, 0),  # bright red
    "w": (152, 135, 95),  # brown
    "W": (207, 192, 65),  # yellow
    "c": (64, 164, 185),  # dark cyan
    "C": (119, 191, 207),  # bright cyan
    "b": (0, 72, 189),  # dark blue
    "B": (0, 150, 255),  # bright blue
    "g": (0, 148, 3),  # dark green
    "G": (0, 196, 32),  # bright green
    "m": (177, 84, 207),  # dark magenta
    "M": (218, 91, 214),  # bright magenta
    "y": (177, 201, 195),  # bright grey
    "Y": (255, 255, 255),  # white
    "k": (15, 59, 58),  # black
    "K": (21, 83, 82),  # dark grey
    "o": (241, 95, 34),
    "O": (233, 159, 16),
    "transparent": (15, 59, 58, 0),
}
QUD_VIRIDIAN = (15, 59, 58, 255)  # 0f3b3a
LIQUID_COLORS = {
    "acid": "&G^g",
    "algae": "&g^C",
    "asphalt": "&k^K",
    "blood": "&r^k",
    "brainbrine": "&g^W",
    "cider": "&w^r",
    "cloning": "&M^Y",
    "convalessence": "&Y^C",
    "gel": "&y^Y",
    "goo": "&Y^G",
    "honey": "&w^W",
    "ink": "&y^k",
    "lava": "&W^R",
    "neutronflux": "&Y^y",
    "oil": "&Y^k",
    "ooze": "&y^k",
    "proteangunk": "&c^C",
    "putrid": "&g^K",
    "salt": "&Y^y",
    "sap": "&W^Y",
    "slime": "&w^g",
    "sludge": "&Y^w",
    "sunslag": "&Y^W",
    "warmstatic": "&K^Y",
    "water": "&b^B",
    "wax": "&y^Y",
    "wine": "&m^r",
}
STAT_DISPLAY_NAMES = {
    "AcidResistance": "acid resistance",
    "ColdResistance": "cold resistance",
    "ElectricResistance": "electric resistance",
    "HeatResistance": "heat resistance",
    "Hitpoints": "hit points",
    "MoveSpeed": "move speed",
    "Speed": "quickness",
    "AP": "attribute points",
    "MP": "mutation points",
    "SP": "skill points",
    "XP": "experience points",
}
# The following includes all parts descending from IActivePart, which defines the IsEMPSensitive and
# PowerLoadSensitive fields. This holds the hard-coded defaults. These can be overridden in the XML.
# This list is accurate as of patch 202.84. There are also a few special cases not descending from
# IActivePart, called out with a comment near the bottom of the dictionary.
ACTIVE_PARTS = {
    "AccelerativeTeleporter": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "ActiveLightSource": {"IsEMPSensitive": False, "IsPowerLoadSensitive": True},
    "AddsMutationOnEquip": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "AddsRep": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "AdjustSpecialEffectChances": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "AilingQuickness": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "AloePorta": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "AmbientCollector": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "AnimateObject": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ArtifactDetection": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ArtificialIntelligence": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "AutomatedExternalDefibrillator": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "Banner": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "Bed": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "BioAmmoLoader": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "BleedingOnHit": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "BootSequence": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "BroadcastPowerReceiver": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "BroadcastPowerTransmitter": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "BurnMe": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "Campfire": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "CannotBeInfluenced": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "Capacitor": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "CardiacArrestOnHit": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "CatacombsExitTeleporter": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "Chair": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ChargeSink": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "Circuitry": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "Clockwork": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "CompanionCapacity": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ComputeNode": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "CrossFlameOnStep": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "Cursed": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "CyberneticsAutomatedInternalDefibrillator": {
        "IsEMPSensitive": True,
        "IsPowerLoadSensitive": False,
    },
    "CyberneticsBiodynamicPowerPlant": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "CyberneticsEffectSuppressor": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "CyberneticsMedassistModule": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "CyberneticsMicromanipulatorArray": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "CyberneticsOnboardRecoilerImprinting": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "CyberneticsOnboardRecoilerTeleporter": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "CyberneticsPenetratingRadar": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "DamageContents": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "DecoyHologramEmitter": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "DeploymentMaintainer": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "DepositCorpses": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "DestroyMe": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "DiggingTool": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "DischargeOnHit": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "DischargeOnStep": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "DismemberAdjacentHostiles": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "Displacement": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "Displacer": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "Drill": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "DrinkMagnifier": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ElectricalDischargeLoader": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "ElectricalPowerTransmission": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ElementalDamage": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "EmergencyTeleporter": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "EmitGasOnHit": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "Enclosing": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "EnergyAmmoLoader": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "EnergyCell": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "EnergyCellSocket": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "Engulfing": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "EquipCharge": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "EquipIntProperties": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "EquipStatBoost": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "FabricateFromSelf": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "Fan": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "FeelingOnTarget": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "FireSuppressionSystem": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "FlareCompensation": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "Flywheel": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "FoliageCamouflage": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "FollowersGetTeleport": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "FoodProcessor": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ForceEmitter": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ForceProjector": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "FugueOnStep": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "FungalFortitude": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "FusionReactor": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "Gaslight": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "GasTumbler": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "GenericPowerTransmission": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "GenericTerminal": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "GlimmerAlteration": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "GrandfatherHorn": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "GritGateMainframeTerminal": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "GroundOnHit": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "HighBitBonus": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "HologramMaterialPrimary": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "HUD": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "HydraulicPowerTransmission": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "HydroTurbine": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "InductionCharger": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "InductionChargeReceiver": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "IntegralRecharger": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "IntegratedPowerSystems": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "IntPropertyChanger": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ItemElements": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "LatchesOn": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "LeaksFluid": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "LifeSaver": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "LiquidAmmoLoader": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "LiquidFueledEnergyCell": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "LiquidFueledPowerPlant": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "LiquidProducer": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "LiquidPump": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "LiquidRepellent": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "LowStatBooster": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "MagazineAmmoLoader": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "MechanicalPowerTransmission": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "MechanicalWings": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "MentalScreen": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "Mill": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "MissilePerformance": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModAirfoil": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModAntiGravity": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ModBeamsplitter": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModBeetlehost": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ModBlinkEscape": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ModCleated": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModColossal": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModCoProcessor": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "ModCounterweighted": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModDesecrated": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModDisguise": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModDisplacer": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "ModDrumLoaded": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModElectrified": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "ModEngraved": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModExtradimensional": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModFactionSlayer": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModFatecaller": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModFeathered": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModFeatherweight": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModFilters": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModFlaming": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "ModFlareCompensating": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ModFlexiweaved": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModFreezing": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "ModGearbox": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModGesticulating": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModGlassArmor": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModGlazed": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModHardened": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModHeatSeeking": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModHighCapacity": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModHorrifying": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModHUD": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModIlluminated": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModImprovedBerserk": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModImprovedBlock": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModImprovedBludgeon": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModImprovedHobble": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModImprovedWindmillStance": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModInduction": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModJacked": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModJewelEncrusted": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModLacquered": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModLanterned": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModLight": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModLiquidCooled": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModMagnetized": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ModMasterwork": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModMercurial": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ModMetallized": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModMetered": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModMighty": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModMorphogenetic": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "ModNanochelated": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModNanon": {"IsEMPSensitive": False, "IsPowerLoadSensitive": True},
    "ModNav": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ModNormalizing": {"IsEMPSensitive": False, "IsPowerLoadSensitive": True},
    "ModOverloaded": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ModPadded": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModPainted": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModPhaseConjugate": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModPhaseHarmonic": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModPiping": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModPolarized": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModPsionic": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModRadioPowered": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModRazored": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModRecycling": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModRefractive": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModReinforced": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModRelicFreezing": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "ModScaled": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModScoped": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModSerene": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModSharp": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModSirocco": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModSixFingered": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModSmart": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModSnailEncrusted": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModSpiked": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModSpringLoaded": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModSturdy": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModSuspensor": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ModTimereaver": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ModTransmuteOnHit": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModTwoFaced": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModVisored": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModWallSocket": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModWeightless": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModWired": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ModWooly": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "MultiIntPropertyChanger": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "MultiNavigationBonus": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "NavigationBonus": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "NightSightInterpolators": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "NightVision": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "NoKnockdown": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "PartsGas": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "PetPhylactery": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "PointDefense": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "Pounder": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "PowerCord": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "PoweredFloating": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "PowerOutlet": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "PowerSwitch": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ProgrammableRecoiler": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "PsychicMeridian": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "RadiusEventSender": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "RealityStabilization": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "RealityStabilizeOnHit": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "ReclamationCist": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "RecoilOnDeath": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ReduceCooldowns": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ReduceEnergyCosts": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ReflectProjectiles": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "RemotePowerSwitch": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "RequiresPowerToEquip": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "RespondToEvent": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "RocketSkates": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "SapChargeOnHit": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "SaveModifier": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "SaveModifiers": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "SlipRing": {"IsEMPSensitive": False, "IsPowerLoadSensitive": True},
    "SlottedCellCharger": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "Smartgun": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "SolarArray": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "Stopsvaalinn": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "StrideMason": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "StunOnHit": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "Suspensor": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "SwapOnHit": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "TattooGun": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "Teleporter": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "TeleporterPair": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "TemperatureAdjuster": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "TemplarPhylactery": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ThermalAmp": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "Toolbox": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "UniversalCharger": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "UrbanCamouflage": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "VampiricWeapon": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "VibroWeapon": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "Waldopack": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "WaterRitualDiscount": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "WindTurbine": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "Windup": {"IsEMPSensitive": False, "IsPowerLoadSensitive": False},
    "ZeroPointEnergyCollector": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ZoneAdjust": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    # Special cases (not descending from IActivePart):
    "ConveyorBelt": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "ConveyorPad": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "CryochamberWall": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "CyberneticsNightVision": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "GeomagneticDisc": {"IsEMPSensitive": True, "IsPowerLoadSensitive": True},
    "MagnetizedApplicator": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "Robot": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "Teleprojector": {"IsEMPSensitive": False, "IsPowerLoadSensitive": True},
    "Tinkering_Mine": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "WalltrapAcid": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "WalltrapClockworkBeetles": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "WalltrapCrabs": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "WalltrapFire": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "WalltrapGas": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
    "WalltrapShock": {"IsEMPSensitive": True, "IsPowerLoadSensitive": False},
}
# The 'Butcherable' part can contain a population tables reference if it begins with an '@' symbol.
# One day, we could potentially replace this if we start loading data from PopulationTables.xml.
BUTCHERABLE_POPTABLES = {
    "Eyeless Crab Corpse": {
        "Eyeless Crab Legs": {"Number": 1, "Weight": 95},
        "EyelessCrabShell": {"Number": 1, "Weight": 5},
    },
    "Knollworm Corpse": {
        "Raw Worm Meat": {"Number": 1, "Weight": 98},
        "Knollworm Skull": {"Number": 1, "Weight": 2},
    },
    "Albino ape corpse": {
        "Albino Ape Heart": {"Number": 1, "Weight": 20},
        "Ape Fur Cloak": {"Number": 1, "Weight": 13},
        "Ape Fur Hat": {"Number": 1, "Weight": 13},
        "Ape Fur Gloves": {"Number": 1, "Weight": 13},
        "Albino Ape Pelt": {"Number": 1, "Weight": 40},
    },
    "Ogre ape corpse": {
        "Ogre Ape Heart": {"Number": 1, "Weight": 20},
        "Ogre Fur Cloak": {"Number": 1, "Weight": 13},
        "Ogre Fur Hat": {"Number": 1, "Weight": 13},
        "Ogre Fur Gloves": {"Number": 1, "Weight": 13},
        "Ogre Ape Pelt": {"Number": 1, "Weight": 40},
    },
    "Salthopper Corpse": {
        "Salthopper Chip": {"Number": 1, "Weight": 85},
        "SalthopperMandible": {"Number": 1, "Weight": 15},
    },
    "Quartz Baboon Corpse": {
        "Quartzfur Hat": {"Number": 1, "Weight": 20},
        "Quartzfur Cloak": {"Number": 1, "Weight": 20},
        "Quartzfur Gloves": {"Number": 1, "Weight": 20},
    },
    "Kaleidoslug Corpse": {
        "Kaleidocera Cape": {"Number": 1, "Weight": 20},
        "Kaleidocera Muffs": {"Number": 1, "Weight": 20},
        "Kaleidocera Krakows": {"Number": 1, "Weight": 20},
    },
    "Enigma Snail Corpse": {
        "Enigma Cone": {"Number": 1, "Weight": 20},
        "Enigma Cap": {"Number": 1, "Weight": 20},
    },
}
