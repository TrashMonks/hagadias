"""Various constants that are unlikely to change."""

# BIT_TRANS: convert between the bit codes found in XML and the ones shown ingame.
bit_table = {'G': 'B',
             'R': 'A',
             'C': 'D',
             'B': 'C'}
BIT_TRANS = ''.maketrans(bit_table)

# ITEM_MOD_PROPS: difficulty and complexity changes when a mod is applied to an item
# ifcomplex means the change only applies if the item already has complexity > 0
# these values live in code, usually in ApplyModification() method of the Mod's .cs file
ITEM_MOD_PROPS = {'ModCounterweighted': {'complexity': 1,
                                         'difficulty': 1,
                                         'ifcomplex': True,
                                         'prefix': '&ycounterweighted '},
                  'ModElectrified': {'complexity': 1,
                                     'difficulty': 1,
                                     'ifcomplex': False,
                                     'prefix': '&Welectrified&y '},
                  'ModEngraved': {'complexity': 0,
                                  'difficulty': 0,
                                  'ifcomplex': False,
                                  'prefix': '&Ye&yn&cg&Cr&Ya&yv&ce&Cd &y'},
                  'ModExtradimensional': {'complexity': 4,
                                          'difficulty': 8,
                                          'ifcomplex': True,
                                          'prefix': '&Me&Mx&mt&mr&ya&yd&Yi&Ym&'
                                                    'Oe&Yn&Ys&yi&y&mo&mn&Ma&Ml&y '},
                  'ModFlaming': {'complexity': 1,
                                 'difficulty': 1,
                                 'ifcomplex': False,
                                 'prefix': '&Rflaming&y '},
                  'ModFreezing': {'complexity': 1,
                                  'difficulty': 1,
                                  'ifcomplex': False,
                                  'prefix': '&Cfreezing&y '},
                  'ModGesticulating': {'complexity': 1,
                                       'difficulty': 1,
                                       'ifcomplex': False,
                                       'prefix': '&mgesticulating &y'},
                  'ModGlassArmor': {'complexity': 0, 'difficulty': 0, 'ifcomplex': False},
                  'ModHeatSeeking': {'complexity': 1,
                                     'difficulty': 1,
                                     'ifcomplex': True,
                                     'prefix': '&yhoming '},
                  'ModImprovedElectricalGeneration': {'complexity': 0,
                                                      'difficulty': 0,
                                                      'ifcomplex': False},
                  'ModImprovedTemporalFugue': {'complexity': 0,
                                               'difficulty': 0,
                                               'ifcomplex': False},
                  'ModJewelEncrusted': {'complexity': 0, 'difficulty': 0, 'ifcomplex': False},
                  'ModMasterwork': {'complexity': 1,
                                    'difficulty': 1,
                                    'ifcomplex': True,
                                    'prefix': '&Ymasterwork&y '},
                  'ModPainted': {'complexity': 0,
                                 'difficulty': 0,
                                 'ifcomplex': False,
                                 'prefix': '&rp&Ra&Wi&wn&gt&Ge&Bd &y'},
                  'ModPiping': {'complexity': 0,
                                'difficulty': 1,
                                'ifcomplex': False,
                                'postfix': ' &ywith piping'},
                  'ModRazored': {'complexity': 1,
                                 'difficulty': 1,
                                 'ifcomplex': True,
                                 'prefix': '&Yserra&Rt&Yed&y '},
                  'ModScoped': {'complexity': 1,
                                'difficulty': 1,
                                'ifcomplex': False,
                                'prefix': '&yscoped '},
                  'ModSharp': {'complexity': 1,
                               'difficulty': 1,
                               'ifcomplex': True,
                               'prefix': 'sharp '},
                  'ModSpringLoaded': {'complexity': 1,
                                      'difficulty': 1,
                                      'ifcomplex': False,
                                      'prefix': 'spring-loaded '},
                  'ModSturdy': {'complexity': 0,
                                'difficulty': 0,
                                'ifcomplex': False,
                                'prefix': 'sturdy '},
                  'ModWired': {'complexity': 0,
                               'difficulty': 1,
                               'ifcomplex': True,
                               'prefix': '&cwired &y'}}

# This could be loaded from Factions.xml eventually, but for simplicity I'm putting it here for now.
FACTION_ID_TO_NAME = {
    'Antelopes': 'antelopes',
    'Apes': 'apes',
    'Arachnids': 'arachnids',
    'Baboons': 'baboons',
    'Baetyls': 'baetyls',
    'Barathrumites': 'Barathrumites',
    'Bears': 'bears',
    'Birds': 'birds',
    'Cannibals': 'cannibals',
    'Cats': 'cats',
    'Consortium': 'Consortium of Phyta',
    'Crabs': 'crabs',
    'Cragmensch': 'cragmensch',
    'Daughters': 'Daughters of Exile',
    'Dogs': 'dogs',
    'Dromad': 'dromad merchants',
    'Equines': 'equines',
    'Ezra': 'villagers of Ezra',
    'Farmers': 'Farmers\' Guild',
    'Fish': 'fish',
    'Flowers': 'flowers',
    'Frogs': 'frogs',
    'Fungi': 'fungi',
    'Girsh': 'Girsh',
    'Glow Wights': 'Glow-Wights',
    'Goatfolk': 'goatfolk',
    'Hermits': 'hermits',
    'highly entropic beings': 'highly entropic beings',
    'Hindren': 'hindren of Bey Lah',
    'Insects': 'insects',
    'Issachari': 'Issachari tribe',
    'Joppa': 'villagers of Joppa',
    'Kyakukya': 'villagers of Kyakukya',
    'Mamon': 'Children of Mamon',
    'Mechanimists': 'Mechanimists',
    'Merchants': 'Merchants\' Guild',
    'Mollusks': 'mollusks',
    'Mopango': 'mopango',
    'Naphtaali': 'Naphtaali tribe',
    'Newly Sentient Beings': 'newly sentient beings',
    'Oozes': 'oozes',
    'Pariahs': 'pariahs',
    'Prey': 'grazing hedonists',
    'Resheph': 'Cult of the Coiled Lamb',
    'Robots': 'robots',
    'Roots': 'roots',
    'Seekers': 'Seekers of the Sightless Way',
    'Snapjaws': 'snapjaws',
    'Strangers': 'mysterious strangers',
    'Succulents': 'succulents',
    'Swine': 'swine',
    'Templar': 'Putus Templar',
    'Tortoises': 'tortoises',
    'Trees': 'trees',
    'Trolls': 'trolls',
    'Unshelled Reptiles': 'unshelled reptiles',
    'Urchins': 'urchins',
    'Vines': 'vines',
    'Wardens': 'Fellowship of Wardens',
    'Water': 'water barons',
    'Winged Mammals': 'winged mammals',
    'Worms': 'worms'
}

CYBERNETICS_HARDCODED_INFIXES = {
    "Cybernetics2MedassistModule": "{{c|Current loadout:}}{{y| no injectors}}"
}

CYBERNETICS_HARDCODED_POSTFIXES = {
    "Cybernetics2AnomalyFumigator":
        "Compute power on the local lattice increases this item's effectiveness.",
    "Cybernetics2CommunicationsInterlock":
        "Compute power on the local lattice increases this item's effectiveness.",
    "Cybernetics2CustomVisage": "+300 reputation with <chosen faction>",
    "Cybernetics2HighFidelityMatterRecompositer":
        "Compute power on the local lattice reduces this item's cooldown.",
    "Cybernetics2InflatableAxons":
        "Compute power on the local lattice increases this item's effectiveness.",
    "Cybernetics2MatterRecompositer":
        "Compute power on the local lattice reduces this item's cooldown.",
    "Cybernetics2NocturnalApex":
        "Compute power on the local lattice increases this item's effectiveness.",
    "Cybernetics2OnboardRecoilerTeleporter":
        "Compute power on the local lattice reduces this item's cooldown.",
    "Cybernetics2PenetratingRadar":
        "Compute power on the local lattice increases this item's range."
}

HARDCODED_CHARGE_USE = {
    'Neuro Animator': 5000
}
CHARGE_USE_REASONS = {
    'Neuro Animator': 'Object Animation'
}

QUD_COLORS = {'r': (166, 74, 46),  # dark red
              'R': (215, 66, 0),  # bright red
              'w': (152, 135, 95),  # brown
              'W': (207, 192, 65),  # yellow
              'c': (64, 164, 185),  # dark cyan
              'C': (119, 191, 207),  # bright cyan
              'b': (0, 72, 189),  # dark blue
              'B': (0, 150, 255),  # bright blue
              'g': (0, 148, 3),  # dark green
              'G': (0, 196, 32),  # bright green
              'm': (177, 84, 207),  # dark magenta
              'M': (218, 91, 214),  # bright magenta
              'y': (177, 201, 195),  # bright grey
              'Y': (255, 255, 255),  # white
              'k': (15, 59, 58),  # black
              'K': (21, 83, 82),  # dark grey
              'o': (241, 95, 34),
              'O': (233, 159, 16),
              'transparent': (15, 64, 63, 0),
              }

QUD_VIRIDIAN = (15, 64, 63, 255)
