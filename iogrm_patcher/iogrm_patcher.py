import sys, os, csv, bsdiff4

# Provide the vanilla SFC as a command-line argument, e.g. python iogrm_patcher.py "iog.sfc"
# iogrm_base.bsdiff is the "base patch" and contains all of IOGR's code and assets.
# iogrm_config.tsv contains the address (file offset) of every configurable parameter.


# This top section is just "hardcoding" parameter values required by the patch;
# in a real implementation, you'd randomly generate most parameters, use some kind of
# logical fill algorithm to assign items to locations, and so forth.
kara_location = 5    # 1-5
hieroglyph_order = [6, 1, 2, 3, 5, 4]   # Ordered list of numbers 1-6
inca_tile_pos = [1, 5]   # Range is 0-11 x 0-5
initial_hp = 9
jeweler_costs = [1, 2, 10, 15, 21, 35, 44]
# statues_player_choice is required; then either statues_required or statue_count is ignored, as appropriate
statues_player_choice = 0
statues_required = [1, 2, 4]
statue_count = 3
# List up to 3 changes to apply to each Ishtar room; the first change in each list
# is only applied in the right-side subroom, so is the difference that the player has to spot.
# Change ID 0 in each room is Will's hair. Use 0xffff to apply fewer than 3 changes. 10/7/4/9
ishtar_changes = [
                   [3, 0, 0xffff], # Room 1, range 0-10
                   [2, 1, 0xffff], # Room 2, range 0-7
                   [0, 4, 0xffff], # Room 3, range 0-4; if the chests are different, the game ignores the first element
                   [8, 5, 0xffff] # Room 4, range 0-9
                 ]
# 256 entries, one reward per "room", 1/2/3 = HP/STR/DEF
room_rewards = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,2,1,0,0,0,0,0,0,0,0,0,0,0,0,2,3,1,0,0,0,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,2,0,0,0,0,0,0,0,0,3,0,0,3,1,0,0,0,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3,0,2,0,2,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
# Encoding is sufficiently like ASCII that you can treat it as such for
# the arbitrary title screen code; but don't use O/0, l/1, or any of @#$%&'`
title_screen_code = [ b'e', b'R', b'+', b'4', b'K', b'A' ]
# Item-location and item-DS mappings. Most of these columns aren't needed
# for patching; I copied the dicts from IOGR and put no effort into simplifying them.
spawn_locations = {
    -1:  ["",       0x08, 0x00, 0],
    10:  ["Safe",   0x01, 0x00, 0],
    14:  ["",       0x0b, 0x01, 0],
    19:  ["Unsafe", 0x12, 0x02, 1],
    22:  ["Safe",   0x15, 0x03, 0],
    29:  ["Unsafe", 0x28, 0x04, 1],
    30:  ["Unsafe", 0x26, 0x05, 1],
    31:  ["",       0x1e, 0x06, 1],
    39:  ["Safe",   0x34, 0x07, 0],
    46:  ["Unsafe", 0x40, 0x08, 1],
    47:  ["Unsafe", 0x3d, 0x09, 1],
    48:  ["",       0x42, 0x0a, 1],
    57:  ["Safe",   0x4c, 0x0b, 0],
    58:  ["Unsafe", 0x56, 0x0c, 1],
    59:  ["",       0x51, 0x0d, 1],
    60:  ["Unsafe", 0x54, 0x0e, 1],
    66:  ["Safe",   0x5a, 0x0f, 0],
    74:  ["",       0x60, 0x10, 1],
    75:  ["",       0x62, 0x11, 1],
    77:  ["Safe",   0x6c, 0x12, 0],
    88:  ["Safe",   0x7c, 0x13, 0],
    93:  ["Unsafe", 0x85, 0x14, 1],
    94:  ["Unsafe", 0x86, 0x15, 1],
    95:  ["",       0x88, 0x16, 1],
    103: ["Safe",   0x99, 0x17, 0],
    109: ["Unsafe", 0xa1, 0x18, 1],
    110: ["Unsafe", 0xa3, 0x19, 1],
    111: ["",       0xa7, 0x1a, 1],
    114: ["Safe",   0xac, 0x1b, 0],
    122: ["Unsafe", 0xb6, 0x1c, 1],
    123: ["",       0xb8, 0x1d, 1],
    124: ["Unsafe", 0xbb, 0x1e, 1],
    129: ["Safe",   0xc3, 0x1f, 0],
    130: ["",       0xcc, 0x20, 1],
    142: ["Unsafe", 0xcc, 0x21, 1],
    145: ["",       0xdf, 0x22, 0],
    146: ["Safe",   0xe3, 0x23, 0]
}
item_pool = {
    # Normal items, high byte implicitly 0
    0: [2, 1,  0x00, "Nothing", False, 3, 0, 0],
    1: [45, 1, 0x01, "Red Jewel", False, 1, 0, 1],
    2: [1, 1,  0x02, "Prison Key", False, 1, 0, 0],
    3: [1, 1,  0x03, "Inca Statue A", False, 1, 0, 0],
    4: [1, 1,  0x04, "Inca Statue B", False, 2, 0, 0],
    #5: [0, 1,  0x05, "Inca Melody", False, 3, 0, 0],  # Not implemented
    6: [12, 1, 0x06, "Herb", False, 3, 0, 0],
    7: [1, 1,  0x07, "Diamond Block", False, 1, 0, 0],
    8: [1, 1,  0x08, "Wind Melody", False, 1, 0, 0],
    9: [1, 1,  0x09, "Lola's Melody", False, 1, 0, 0],
    10: [1, 1, 0x0a, "Large Roast", False, 1, 0, 0],
    11: [1, 1, 0x0b, "Mine Key A", False, 1, 0, 0],
    12: [1, 1, 0x0c, "Mine Key B", False, 2, 0, 0],
    13: [1, 1, 0x0d, "Memory Melody", False, 1, 0, 0],
    14: [4, 1, 0x0e, "Crystal Ball", False, 2, 0, 0],
    15: [1, 1, 0x0f, "Elevator Key", False, 1, 0, -1],
    16: [1, 1, 0x10, "Mu Palace Key", False, 1, 0, 0],
    17: [1, 1, 0x11, "Purity Stone", False, 1, 0, 0],
    18: [2, 1, 0x12, "Hope Statue", False, 1, 0, 0],
    19: [2, 1, 0x13, "Rama Statue", False, 2, 0, 0],
    20: [1, 1, 0x14, "Magic Dust", False, 2, 0, 0],
    21: [0, 1, 0x15, "Blue Journal", False, 3, 0, 0],
    22: [1, 1, 0x16, "Lance Letter", False, 3, 0, 0],
    23: [1, 1, 0x17, "Necklace", False, 1, 0, 0],
    24: [1, 1, 0x18, "Will", False, 1, 0, 0],
    25: [1, 1, 0x19, "Teapot", False, 1, 0, 0],
    26: [3, 1, 0x1a, "Mushroom Drops", False, 1, 0, -1],
    #27: [0, 1, 0x1b, "Bag of Gold", False, 3, 0, 0],  # Not implemented
    28: [1, 1, 0x1c, "Black Glasses", False, 1, 0, 0],
    29: [1, 1, 0x1d, "Gorgon Flower", False, 1, 0, 0],
    30: [1, 1, 0x1e, "Hieroglyph", False, 2, 0, 0],
    31: [1, 1, 0x1f, "Hieroglyph", False, 2, 0, 0],
    32: [1, 1, 0x20, "Hieroglyph", False, 2, 0, 0],
    33: [1, 1, 0x21, "Hieroglyph", False, 2, 0, 0],
    34: [1, 1, 0x22, "Hieroglyph", False, 2, 0, 0],
    35: [1, 1, 0x23, "Hieroglyph", False, 2, 0, 0],
    36: [1, 1, 0x24, "Aura", False, 1, 0, 0],
    37: [1, 1, 0x25, "Lola's Letter", False, 1, 0, 0],
    38: [1, 1, 0x26, "Journal", False, 2, 0, 0],
    39: [1, 1, 0x27, "Crystal Ring", False, 1, 0, 0],
    40: [1, 1, 0x28, "Apple", False, 1, 0, 0],
    41: [1, 1, 0x2e, "2 Red Jewels", False, 1, 0, -2],
    42: [1, 1, 0x2f, "3 Red Jewels", False, 1, 0, -2],

    # Status Upgrades
    # Mapped to artificial items whose IDs are $5E lower (e.g. $87 -> $29),
    # so $8c/$8d are skipped since they'd map to $2e/$2f which are in use.
    50: [3, 1, 0x87, "HP Upgrade", False, 3, 0, 0],
    51: [1, 1, 0x89, "DEF Upgrade", False, 3, 0, 0],
    52: [2, 1, 0x88, "STR Upgrade", False, 3, 0, 0],
    53: [1, 1, 0x8a, "Dash Upgrade", False, 3, 0, 0],
    54: [2, 1, 0x8b, "Friar Upgrade", False, 3, 0, 2],
    55: [0, 1, 0x8e, "Heart Piece", False, 3, 0, 0],

    # Abilities
    60: [0, 2, 0, "Nothing", False, 3, 0, 0],
    61: [1, 2, 0x1100, "Psycho Dash", False, 1, 0, 0],
    62: [1, 2, 0x1101, "Psycho Slider", False, 1, 0, 3],
    63: [1, 2, 0x1102, "Spin Dash", False, 1, 0, 3],
    64: [1, 2, 0x1103, "Dark Friar", False, 1, 0, 3],
    65: [1, 2, 0x1104, "Aura Barrier", False, 1, 0, 0],
    66: [1, 2, 0x1105, "Earthquaker", False, 1, 0, 3],
    67: [1, 6, "", "Firebird", False, 3, 0, 0],

    # Mystic Statues
    100: [1, 3, "", "Mystic Statue 1", False, 2, 0, 0],
    101: [1, 3, "", "Mystic Statue 2", False, 2, 0, 0],
    102: [1, 3, "", "Mystic Statue 3", False, 2, 0, 0],
    103: [1, 3, "", "Mystic Statue 4", False, 2, 0, 0],
    104: [1, 3, "", "Mystic Statue 5", False, 2, 0, 0],
    105: [1, 3, "", "Mystic Statue 6", False, 2, 0, 0],
    106: [0, 3, "", "Mystic Statue", False, 2, 0, 0],

    # Event Switches
    500: [1, 4, "", "Kara Released", False, 1, 0, 0],
    501: [1, 4, "", "Itory: Got Lilly", False, 1, 0, 0],
    502: [1, 4, "", "Moon Tribe: Healed Spirits", False, 1, 0, 0],
    503: [1, 4, "", "Inca: Beat Castoth", False, 1, 0, 0],
    504: [1, 4, "", "Freejia: Found Laborer", False, 1, 0, 0],
    505: [1, 4, "", "Neil's: Memory Restored", False, 1, 0, 0],
    506: [1, 4, "", "Sky Garden: Map 82 NW Switch", False, 1, 0, 0],
    507: [1, 4, "", "Sky Garden: Map 82 NE Switch", False, 1, 0, 0],
    508: [1, 4, "", "Sky Garden: Map 82 SE Switch", False, 1, 0, 0],
    509: [1, 4, "", "Sky Garden: Map 84 Switch", False, 1, 0, 0],
    510: [1, 4, "", "Seaside: Fountain Purified", False, 1, 0, 0],
    511: [1, 4, "", "Mu: Water Lowered 1", False, 1, 0, 0],
    512: [1, 4, "", "Mu: Water Lowered 2", False, 1, 0, 0],
    513: [1, 4, "", "Angel: Puzzle Complete", False, 1, 0, 0],
    514: [1, 4, "", "Mt Kress: Drops Used 1", False, 1, 0, 0],
    515: [1, 4, "", "Mt Kress: Drops Used 2", False, 1, 0, 0],
    516: [1, 4, "", "Mt Kress: Drops Used 3", False, 1, 0, 0],
    517: [1, 4, "", "Pyramid: Hieroglyphs Placed", False, 1, 0, 0],
    518: [1, 4, "", "Babel: Castoth Defeated", False, 1, 0, 0],
    519: [1, 4, "", "Babel: Viper Defeated", False, 1, 0, 0],
    520: [1, 4, "", "Babel: Vampires Defeated", False, 1, 0, 0],
    521: [1, 4, "", "Babel: Sand Fanger Defeated", False, 1, 0, 0],
    522: [1, 4, "", "Babel: Mummy Queen Defeated", False, 1, 0, 0],
    523: [1, 4, "", "Mansion: Solid Arm Defeated", False, 1, 0, 0],
    524: [1, 4, "", "Inca: Diamond Block Placed", False, 1, 0, 0],
    525: [1, 4, "", "Pyramid: Portals open", False, 1, 0, 0],
    526: [1, 4, "", "Mu: Access to Hope Room 1", False, 1, 0, 0],
    527: [1, 4, "", "Mu: Access to Hope Room 2", False, 1, 0, 0],
    528: [1, 4, "", "Mine: Blocked Tunnel Open", False, 1, 0, 0],
    529: [1, 4, "", "Underground Tunnel: Bridge Open", False, 1, 0, 0],
    530: [1, 4, "", "Inca: Slug Statue Broken", False, 1, 0, 0],
    531: [1, 4, "", "Mu: Beat Vampires", False, 1, 0, 0],

    # Misc. game states
    602: [1, 6, "", "Early Firebird enabled", False, 1, 0, 0],
    #603: [0, 6, "", "Firebird", False, 1, 0, 0],   # Firebird item is 67 instead of this
    604: [1, 1, 0x8f, "Flute", False, 1, 0, 0],
    608: [0, 6, "", "Has Any Will Ability", False, 1, 0, 0],   # Expanded to PDash|Slider|SDash during init
    609: [0, 6, "", "Has Any Attack", False, 1, 0, 0],   # Expanded to many options during init, if not starting with flute
    610: [0, 6, "", "Has Any Ranged Attack", False, 1, 0, 0],  # Expanded to Friar|Firebird during init
    611: [0, 6, "", "Can Play Songs", False, 1, 0, 0],   # Expanded during init to Flute|Fluteless
    612: [0, 6, "", "Telekinesis", False, 1, 0, 0],   # Expanded during init to Flute|Fluteless|Freedan|Shadow
    
    # Orbs that open doors -- ASM ID is the map rearrangement flag + artificial 0x1000
    700: [1, 5, 0x1001, "Open Underground Tunnel Skeleton Cage", False, 3, 0, 0],
    701: [1, 5, 0x1002, "Open Underground Tunnel First Worm Door", False, 1, 0, -5],
    702: [1, 5, 0x1003, "Open Underground Tunnel Second Worm Door", False, 1, 0, -5],
    703: [1, 5, 0x1005, "Open Underground Tunnel West Room Bat Door", False, 1, 0, -5],
    704: [1, 5, 0x1016, "Open Underground Tunnel Hidden Dark Space", False, 1, 0, -5],
    705: [1, 5, 0x1017, "Open Underground Tunnel Red Skeleton Barrier 1", False, 1, 0, -5],
    706: [1, 5, 0x1018, "Open Underground Tunnel Red Skeleton Barrier 2", False, 1, 0, -5],
    707: [1, 5, 0x100d, "Open Incan Ruins West Ladder", False, 1, 0, 0],
    708: [1, 5, 0x100e, "Open Incan Ruins Final Ladder", False, 1, 0, 0],
    709: [1, 5, 0x100f, "Open Incan Ruins Entrance Ladder", False, 1, 0, 0],
    710: [1, 5, 0x100c, "Open Incan Ruins Water Room Ramp", False, 1, 0, 0],
    711: [1, 5, 0x100b, "Open Incan Ruins East-West Freedan Ramp", False, 1, 0, 0],
    712: [1, 5, 0x100a, "Open Incan Ruins Diamond Block Stairs", False, 3, 0, 0],
    713: [1, 5, 0x1010, "Open Incan Ruins Singing Statue Stairs", False, 1, 0, 0],
    714: [1, 5, 0x1034, "Open Diamond Mine Tunnel Middle Fence", False, 1, 0, -3],
    715: [1, 5, 0x1035, "Open Diamond Mine Tunnel South Fence", False, 1, 0, -3],
    716: [1, 5, 0x1036, "Open Diamond Mine Tunnel North Fence", False, 1, 0, -3],
    717: [1, 5, 0x1022, "Open Diamond Mine Big Room Monster Cage", False, 3, 0, 0],
    718: [1, 5, 0x1032, "Open Diamond Mine Hidden Dark Space", False, 1, 0, 0],
    719: [1, 5, 0x1023, "Open Diamond Mine Ramp Room Worm Fence", False, 1, 0, 0],
    720: [1, 5, 0x1037, "Open Sky Garden SE Topside Friar Barrier", False, 1, 0, 0],
    721: [1, 5, 0x1030, "Open Sky Garden SE Darkside Chest Barrier", False, 1, 0, 0],
    722: [1, 5, 0x1024, "Open Sky Garden SW Topside Cyber Barrier", False, 1, 0, 0],
    723: [1, 5, 0x102b, "Open Sky Garden SW Topside Cyber Ledge", False, 3, 0, 0],
    724: [1, 5, 0x102c, "Open Sky Garden SW Topside Worm Barrier", False, 1, 0, 0],
    725: [1, 5, 0x1031, "Open Sky Garden SW Darkside Fire Cages", False, 1, 0, 0],
    726: [1, 5, 0x103d, "Open Mu Entrance Room Barrier", False, 1, 0, 0],
    727: [1, 5, 0x103e, "Open Mu Northeast Room Rock 1", False, 1, 0, 0],
    728: [1, 5, 0x103f, "Open Mu Northeast Room Rock 2", False, 1, 0, 0],
    729: [1, 5, 0x1042, "Open Mu West Room Slime Cages", False, 3, 0, 0],
    730: [1, 5, 0x1041, "Open Mu East-Facing Stone Head", False, 3, 0, 0],
    731: [1, 5, 0x1040, "Open Mu South-Facing Stone Head", False, 3, 0, 0],
    732: [1, 5, 0x1053, "Open Great Wall Archer Friar Barrier", False, 1, 0, 0],
    #733: [1, 5, 0x106a, "Open Great Wall Fanger Arena Exit", False, 1, 0, 0], # Probably shouldn't randomize this...
    734: [1, 5, 0x1068, "Open Mt. Temple West Chest Shortcut", False, 3, 0, 0],
    735: [1, 5, 0x106c, "Open Ankor Wat Entrance Stairs", False, 1, 0, 0],
    736: [1, 5, 0x106b, "Open Ankor Wat Outer East Slider Hole", False, 1, 0, 0],
    #737: [1, 5, 0x106d, "Open Ankor Wat Pit Exit", False, 1, 0, 0], # Probably shouldn't randomize this...
    738: [1, 5, 0x106f, "Open Ankor Wat Dark Space Corridor", False, 1, 0, 0],
    739: [1, 5, 0x1073, "Open Pyramid Foyer Upper Dark Space", False, 1, 0, 0],
    740: [1, 5, 0x109a, "Open Jeweler's Mansion First Barrier", False, 1, 0, 0],
    741: [1, 5, 0x109b, "Open Jeweler's Mansion Second Barrier", False, 1, 0, 0],
    
    800: [1, 6, "", "Dungeon Shuffle artificial logic", False, 3, 0, 0],
    801: [0, 6, "", "Dungeon Shuffle artificial antilogic", False, 3, 0, 0],
    
    900: [0, 1, 0x32, "Other World Item", False, 1, 0, 0]
}
item_locations = {
    0 : [2, 1, True, 1, [54, 62, 63, 64, 66, 604], 'Jeweler1Item', 'Jeweler Reward 1', 1, 4, []],
    1 : [3, 1, True, 14, [0, 1, 6, 41, 42, 604], 'Jeweler2Item', 'Jeweler Reward 2', 1, 5, []],
    2 : [4, 1, True, 6, [], 'Jeweler3Item', 'Jeweler Reward 3', 1, 8, []],
    3 : [5, 1, True, 37, [0, 1, 6, 41, 42], 'Jeweler4Item', 'Jeweler Reward 4', 1, 10, []],
    4 : [6, 1, True, 1, [], 'Jeweler5Item', 'Jeweler Reward 5', 1, 11, []],
    5 : [7, 1, True, 10, [0, 1, 6, 41, 42], 'Jeweler6Item', 'Jeweler Reward 6', 1, 31, []],
    6 : [21, 1, True, 1, [64, 66, 54, 62, 63], 'CapeTowerItem', 'South Cape: Bell Tower', 1, 1, []],
    7 : [20, 1, True, 7, [64, 66, 54, 62, 63], 'CapeFisherItem', 'South Cape: Fisherman', 1, 1, []],
    8 : [26, 1, True, 1, [64, 66, 54, 62, 63], 'CapeLancesHouseItem', "South Cape: Lance's House", 1, 1, []],
    9 : [23, 1, True, 9, [64, 66, 54, 62, 63], 'CapeLolaItem', 'South Cape: Lola', 1, 1, []],
    10 : [21, 2, False, 0, [64, 65, 66, 54, 62, 63], '', 'South Cape: Dark Space', 2, 1, []],
    11 : [30, 1, True, 1, [64, 66, 54, 62, 63], 'ECHiddenGuardItem', "Edward's Castle: Hidden Guard", 1, 1, []],
    12 : [30, 1, True, 1, [64, 66, 54, 62, 63], 'ECBasementItem', "Edward's Castle: Basement", 1, 1, []],
    13 : [32, 1, True, 1, [64, 66, 54, 62, 63], 'EDHamletItem', "Edward's Prison: Hamlet", 1, 1, []],
    14 : [32, 2, False, 0, [64, 65, 66, 54, 62, 63], '', "Edward's Prison: Dark Space", 2, 1, []],
    15 : [39, 1, True, 0, [], 'EDSpikeChestItem', "Underground Tunnel: Spike's Chest", 1, 13, []],
    16 : [44, 1, True, 1, [], 'EDSmallRoomChestItem', 'Underground Tunnel: Small Room Chest', 1, 13, []],
    17 : [705, 1, True, 26, [], 'EDEndChestItem', "Underground Tunnel: Ribber's Chest  ", 1, 13, []],
    18 : [49, 1, True, 20, [], 'EDEndBarrelsItem', 'Underground Tunnel: Barrels', 1, 13, []],
    19 : [720, 2, True, 0, [], '', 'Underground Tunnel: Dark Space', 0, 13, []],
    705 : [796, 5, True, 705, [], 'EDSkeleton1Item', 'Underground Tunnel: Red Skeleton 1', 0, 13, [[609, 1]]],
    706 : [797, 5, True, 706, [], 'EDSkeleton2Item', 'Underground Tunnel: Red Skeleton 2', 0, 13, [[609, 1]]],
    20 : [51, 1, True, 41, [64, 66, 54, 62, 63], 'ItoryLogsItem', 'Itory Village: Logs', 1, 2, []],
    21 : [58, 1, True, 8, [64, 66, 54, 62, 63], 'ItoryCaveItem', 'Itory Village: Cave', 1, 2, []],
    22 : [51, 2, True, 61, [64, 65, 66, 54, 62, 63], '', 'Itory Village: Dark Space', 2, 2, []],
    23 : [62, 1, True, 1, [64, 66, 54, 62, 63], 'MoonTribeCaveItem', 'Moon Tribe: Cave', 1, 2, []],
    24 : [71, 1, True, 1, [64, 66, 54, 62, 63], 'IncaDiamondBlockChestItem', 'Inca Ruins: Diamond-Block Chest', 1, 1, []],
    25 : [92, 1, True, 1, [64, 66, 62, 63], 'IncaMazeChestItem', 'Inca Ruins: Broken Statues Chest', 1, 3, []],
    26 : [83, 1, True, 1, [64, 66, 62, 63], 'IncaStatueChestItem', 'Inca Ruins: Stone Lord Chest', 1, 3, []],
    27 : [93, 1, True, 6, [64, 66, 62, 63], 'IncaWormChestItem', 'Inca Ruins: Slugger Chest', 1, 3, []],
    28 : [76, 1, True, 25, [64, 66, 62, 63], 'IncaCliffItem', 'Inca Ruins: Singing Statue', 1, 3, []],
    29 : [96, 2, True, 0, [64, 66, 62, 63], '', 'Inca Ruins: Dark Space 1', 0, 3, []],
    30 : [93, 2, True, 0, [64, 66, 62, 63], '', 'Inca Ruins: Dark Space 2', 2, 3, []],
    31 : [77, 2, True, 0, [], '', 'Inca Ruins: Final Dark Space', 2, 7, []],
    707 : [798, 5, True, 707, [64, 66, 62, 63], 'IncaWestLadderItem', 'Inca Ruins: 4-Way for West Ladder', 0, 3, [[609, 1]]],
    708 : [799, 5, True, 708, [64, 66, 62, 63], 'IncaSoutheastLadderItem', 'Inca Ruins: 4-Way for SE Ladder', 0, 3, [[609, 1]]],
    709 : [800, 5, True, 709, [64, 66, 62, 63], 'IncaNortheastLadderItem', 'Inca Ruins: 4-Way for NE Ladder', 0, 3, [[609, 1]]],
    711 : [802, 5, True, 711, [64, 66, 62, 63], 'IncaEWRampItem', 'Inca Ruins: Whirligig for E/W Ramp', 0, 3, [[609, 1]]],
    32 : [100, 1, True, 1, [], 'IncaGoldShipItem', 'Gold Ship: Seth', 1, 24, []],
    33 : [102, 1, True, 13, [], 'DiamondCoastJarItem', 'Diamond Coast: Jar', 1, 6, []],
    34 : [121, 1, True, 1, [], 'FrejHotelItem', 'Freejia: Hotel', 1, 6, []],
    35 : [110, 1, True, 1, [], 'FrejEastSlaverItem', 'Freejia: Creepy Guy', 1, 6, []],
    36 : [110, 1, True, 1, [], 'FrejBin1Item', 'Freejia: Trash Can 1', 1, 6, []],
    37 : [110, 1, True, 1, [], 'FrejBin2Item', 'Freejia: Trash Can 2', 1, 6, []],
    38 : [805, 1, True, 1, [], 'FrejSnitchItem', 'Freejia: Snitch', 1, 6, [[504, 1]]],
    39 : [125, 2, False, 0, [64, 65, 66], '', 'Freejia: Dark Space', 2, 6, []],
    40 : [134, 1, True, 1, [], 'MineChestItem', 'Diamond Mine: Chest', 1, 6, []],
    41 : [806, 1, True, 1, [], 'MineWallSlaveItem', 'Diamond Mine: Trapped Laborer', 1, 6, [[608, 1]]],
    42 : [807, 1, True, 1, [], 'MineRampSlaveItem', 'Diamond Mine: Laborer w/Elevator Key', 1, 6, [[609, 1]]],
    43 : [148, 1, True, 1, [], 'MineMorgueItem', 'Diamond Mine: Morgue', 1, 21, []],
    44 : [808, 1, True, 28, [], 'MineCombatSlaveItem', 'Diamond Mine: Laborer w/Mine Key', 1, 21, [[609, 1]]],
    45 : [150, 1, True, 1, [], 'MineSamItem', 'Diamond Mine: Sam', 1, 34, []],
    46 : [721, 2, True, 65, [], '', 'Diamond Mine: Appearing Dark Space', 2, 6, []],
    47 : [131, 2, True, 0, [], '', 'Diamond Mine: Dark Space at Wall', 0, 6, []],
    48 : [142, 2, True, 66, [], '', 'Diamond Mine: Dark Space behind Wall', 2, 6, []],
    714 : [809, 5, True, 714, [], 'MineMidFenceItem', 'Diamond Mine: Lizard for Tunnel Middle Fence', 0, 6, [[609, 1]]],
    715 : [810, 5, True, 715, [], 'MineSouthFenceItem', 'Diamond Mine: Eye for Tunnel South Fence', 0, 6, [[609, 1]]],
    716 : [811, 5, True, 716, [], 'MineNorthFenceItem', 'Diamond Mine: Eye for Tunnel North Fence', 0, 6, [[609, 1]]],
    719 : [814, 5, True, 719, [], 'MineFriarFenceItem', 'Diamond Mine: Worm for Friar Ramp Fence', 0, 6, [[609, 1]]],
    49 : [172, 1, True, 39, [], 'SGNENorthChestItem', 'Sky Garden: (NE) Platform Chest', 1, 6, []],
    50 : [173, 1, True, 2, [], 'SGNEWestChestItem', 'Sky Garden: (NE) Blue Cyber Chest', 1, 6, []],
    51 : [174, 1, True, 1, [], 'SGNEStatueChestItem', 'Sky Garden: (NE) Statue Chest', 1, 6, []],
    52 : [716, 1, True, 6, [], 'SGSEChestItem', 'Sky Garden: (SE) Dark Side Chest', 1, 6, []],
    53 : [185, 1, True, 1, [], 'SGSWTopChestItem', 'Sky Garden: (SW) Ramp Chest', 1, 6, []],
    54 : [186, 1, True, 23, [], 'SGSWBotChestItem', 'Sky Garden: (SW) Dark Side Chest', 1, 6, []],
    55 : [194, 1, True, 1, [], 'SGNWTopChestItem', 'Sky Garden: (NW) North Chest', 1, 6, []],
    56 : [815, 1, True, 1, [], 'SGNWBotChestItem', 'Sky Garden: (NW) South Chest', 1, 6, [[609, 1]]],
    57 : [170, 2, False, 0, [64, 65, 66], '', 'Sky Garden: Dark Space (Foyer)', 2, 6, []],
    58 : [169, 2, True, 0, [], '', 'Sky Garden: Dark Space (SE)', 0, 6, []],
    59 : [183, 2, True, 64, [], '', 'Sky Garden: Dark Space (SW)', 2, 6, []],
    60 : [195, 2, True, 0, [], '', 'Sky Garden: Dark Space (NW)', 2, 6, []],
    720 : [816, 5, True, 720, [], 'SGSETopBarrierItem', 'Sky Garden: (SE) Top Robot for Center Barrier', 0, 6, [[609, 1]]],
    722 : [818, 5, True, 722, [], 'SGSWTopPegGateItem', 'Sky Garden: (SW) Top Robot for Peg Gate', 0, 6, [[609, 1]]],
    724 : [820, 5, True, 724, [], 'SGSWTopWormGateItem', 'Sky Garden: (SW) Top Worm for West Gate', 0, 6, [[609, 1]]],
    61 : [202, 1, True, 22, [], 'SeaPalSideChestItem', 'Seaside Palace: Side Room Chest', 1, 6, []],
    62 : [200, 1, True, 52, [], 'SeaPalTopChestItem', 'Seaside Palace: First Area Chest', 1, 6, []],
    63 : [205, 1, True, 1, [], 'SeaPalBotChestItem', 'Seaside Palace: Second Area Chest', 1, 6, []],
    64 : [822, 1, True, 6, [], 'SeaPalBuffyItem', 'Seaside Palace: Buffy', 1, 22, [[510, 1]]],
    65 : [823, 1, True, 18, [], 'SeaPalCoffinItem', 'Seaside Palace: Coffin', 1, 9, [[501, 1]]],
    66 : [200, 2, True, 62, [64, 65, 66], '', 'Seaside Palace: Dark Space', 2, 6, []],
    67 : [217, 1, True, 54, [], 'MuEmptyChest1Item', 'Mu: Empty Chest 1', 1, 14, []],
    68 : [220, 1, True, 1, [], 'MuEmptyChest2Item', 'Mu: Empty Chest 2', 1, 14, []],
    69 : [225, 1, True, 1, [], 'MuHopeStatue1Item', 'Mu: Hope Statue 1', 1, 14, []],
    70 : [236, 1, True, 4, [], 'MuHopeStatue2Item', 'Mu: Hope Statue 2', 1, 15, []],
    71 : [215, 1, True, 30, [], 'MuHopeRoomChestItem', 'Mu: Chest s/o Hope Room 2', 1, 28, []],
    72 : [214, 1, True, 38, [], 'MuRamaChestNItem', 'Mu: Rama Chest N', 1, 28, []],
    73 : [219, 1, True, 6, [], 'MuRamaChestEItem', 'Mu: Rama Chest E', 1, 28, []],
    74 : [218, 2, True, 0, [], '', 'Mu: Northeast Dark Space', 0, 15, []],
    75 : [228, 2, True, 0, [], '', 'Mu: Slider Dark Space', 0, 15, []],
    726 : [824, 5, True, 726, [], 'MuEntranceGolemItem', 'Mu: Entrance Golem for Gate', 0, 14, [[609, 1]]],
    76 : [254, 1, True, 18, [], 'AnglDanceHallItem', 'Angel Village: Dance Hall', 1, 14, []],
    77 : [255, 2, False, 0, [64, 65, 66], '', 'Angel Village: Dark Space', 2, 14, []],
    78 : [265, 1, True, 24, [], 'AnglSliderChestItem', 'Angel Dungeon: Slider Chest', 1, 14, []],
    79 : [271, 1, True, 14, [], 'AnglIshtarSidePotItem', "Angel Dungeon: Ishtar's Room", 1, 14, []],
    80 : [274, 1, True, 29, [], 'AnglPuzzleChest1Item', 'Angel Dungeon: Puzzle Chest 1', 1, 14, []],
    81 : [274, 1, True, 6, [], 'AnglPuzzleChest2Item', 'Angel Dungeon: Puzzle Chest 2', 1, 14, []],
    82 : [273, 1, True, 50, [], 'AnglIshtarWinChestItem', "Angel Dungeon: Ishtar's Chest", 1, 14, []],
    83 : [280, 1, True, 50, [], 'WtrmWestJarItem', 'Watermia: West Jar', 1, 14, []],
    85 : [286, 1, True, 6, [], 'WtrmLanceItem', 'Watermia: Lance', 1, 14, []],
    86 : [283, 1, True, 1, [], 'WtrmDesertJarItem', 'Watermia: Gambling House', 1, 14, []],
    87 : [280, 1, True, 51, [], 'WtrmRussianGlassItem', 'Watermia: Russian Glass', 1, 14, []],
    88 : [282, 2, True, 63, [64, 65, 66], '', 'Watermia: Dark Space', 2, 14, []],
    89 : [290, 1, True, 6, [], 'GtWlNecklace1Item', 'Great Wall: Necklace 1', 1, 14, []],
    90 : [292, 1, True, 1, [], 'GtWlNecklace2Item', 'Great Wall: Necklace 2', 1, 14, []],
    91 : [292, 1, True, 1, [], 'GtWlChest1Item', 'Great Wall: Chest 1', 1, 14, []],
    92 : [294, 1, True, 1, [], 'GtWlChest2Item', 'Great Wall: Chest 2', 1, 14, []],
    93 : [295, 2, True, 0, [], '', 'Great Wall: Archer Dark Space', 2, 14, []],
    94 : [297, 2, True, 0, [], '', 'Great Wall: Platform Dark Space', 0, 14, []],
    95 : [300, 2, True, 0, [], '', 'Great Wall: Appearing Dark Space', 2, 14, []],
    732 : [830, 5, True, 732, [], 'GtWlArcherItem', 'Great Wall: Archer for Friar Gate', 0, 14, [[609, 1]]],
    96 : [310, 1, True, 6, [], 'EuroAlleyItem', 'Euro: Alley', 1, 12, []],
    97 : [310, 1, True, 15, [], 'EuroAppleVendorItem', 'Euro: Apple Vendor', 1, 12, []],
    98 : [320, 1, True, 6, [], 'EuroHiddenHouseItem', 'Euro: Hidden House', 1, 12, []],
    99 : [323, 1, True, 0, [], 'EuroShop1Item', 'Euro: Store Item 1', 1, 12, []],
    100 : [323, 1, True, 1, [], 'EuroShop2Item', 'Euro: Store Item 2', 1, 12, []],
    101 : [321, 1, True, 26, [], 'EuroSlaveRoomBarrelItem', 'Euro: Shrine', 1, 12, []],
    102 : [831, 1, True, 11, [], 'EuroAnnItem', 'Euro: Ann', 1, 30, [[40, 1]]],
    103 : [325, 2, False, 0, [64, 65, 66], '', 'Euro: Dark Space', 2, 12, []],
    104 : [336, 1, True, 17, [], 'KressChest1Item', 'Mt. Temple: Red Jewel Chest', 1, 14, []],
    105 : [338, 1, True, 1, [], 'KressChest2Item', 'Mt. Temple: Drops Chest 1', 1, 14, []],
    106 : [342, 1, True, 53, [], 'KressChest3Item', 'Mt. Temple: Drops Chest 2', 1, 17, []],
    107 : [343, 1, True, 1, [], 'KressChest4Item', 'Mt. Temple: Drops Chest 3', 1, 19, []],
    108 : [345, 1, True, 1, [], 'KressChest5Item', 'Mt. Temple: Final Chest', 1, 25, []],
    109 : [332, 2, True, 0, [], '', 'Mt. Temple: Dark Space 1', 2, 14, []],
    110 : [337, 2, True, 0, [], '', 'Mt. Temple: Dark Space 2', 2, 14, []],
    111 : [343, 2, True, 0, [], '', 'Mt. Temple: Dark Space 3', 2, 19, []],
    112 : [353, 1, True, 16, [], 'NativesPotItem', "Natives' Village: Statue Room", 1, 12, []],
    113 : [354, 1, True, 1, [], 'NativesGirlItem', "Natives' Village: Statue", 1, 18, []],
    114 : [350, 2, False, 0, [64, 65, 66], '', "Natives' Village: Dark Space", 2, 12, []],
    115 : [361, 1, True, 1, [], 'WatChest1Item', 'Ankor Wat: Ramp Chest', 1, 12, []],
    116 : [370, 1, True, 26, [], 'WatChest2Item', 'Ankor Wat: Flyover Chest', 1, 14, []],
    117 : [378, 1, True, 14, [], 'WatChest3Item', 'Ankor Wat: U-Turn Chest', 1, 14, []],
    118 : [382, 1, True, 42, [], 'WatChest4Item', 'Ankor Wat: Drop Down Chest', 1, 27, []],
    119 : [389, 1, True, 50, [], 'WatChest5Item', 'Ankor Wat: Forgotten Chest', 1, 27, []],
    120 : [380, 1, True, 3, [], 'WatGlassesItem', 'Ankor Wat: Glasses Location', 1, 14, []],
    121 : [391, 1, True, 1, [], 'WatSpiritItem', 'Ankor Wat: Spirit', 1, 27, []],
    122 : [372, 2, True, 0, [], '', 'Ankor Wat: Garden Dark Space', 2, 14, []],
    123 : [377, 2, True, 0, [], '', 'Ankor Wat: Earthquaker Dark Space', 2, 14, []],
    124 : [383, 2, True, 0, [], '', 'Ankor Wat: Drop Down Dark Space', 2, 27, []],
    735 : [833, 5, True, 735, [], 'WatSouthScarabItem', 'Ankor Wat: Scarab for Outer South Stair', 0, 14, [[609, 1]]],
    738 : [835, 5, True, 738, [], 'WatDarkSpaceHallItem', 'Ankor Wat: Skull for Inner East DS Hall', 0, 14, [[609, 1]]],
    125 : [400, 1, True, 6, [], 'DaoEntrance1Item', 'Dao: Entrance Item 1', 1, 12, []],
    126 : [400, 1, True, 1, [], 'DaoEntrance2Item', 'Dao: Entrance Item 2', 1, 12, []],
    127 : [400, 1, True, 54, [], 'DaoGrassItem', 'Dao: East Grass', 1, 12, []],
    128 : [836, 1, True, 6, [], 'DaoSnakeGameItem', 'Dao: Snake Game', 1, 12, [[609, 1]]],
    129 : [400, 2, False, 0, [64, 65, 66], '', 'Dao: Dark Space', 2, 12, []],
    130 : [713, 1, True, 36, [], 'PyramidGaiaItem', 'Pyramid: Dark Space Top', 1, 12, []],
    131 : [412, 1, True, 1, [], 'PyramidFoyerItem', 'Pyramid: Hidden Platform', 1, 26, []],
    132 : [442, 1, True, 31, [], 'PyramidHiero1Item', 'Pyramid: Hieroglyph 1', 1, 26, []],
    133 : [422, 1, True, 1, [], 'PyramidRoom2ChestItem', 'Pyramid: Room 2 Chest', 1, 26, []],
    134 : [443, 1, True, 40, [], 'PyramidHiero2Item', 'Pyramid: Hieroglyph 2', 1, 26, []],
    135 : [432, 1, True, 52, [], 'PyramidRoom3ChestItem', 'Pyramid: Room 3 Chest', 1, 26, []],
    136 : [444, 1, True, 19, [], 'PyramidHiero3Item', 'Pyramid: Hieroglyph 3', 1, 26, []],
    137 : [439, 1, True, 33, [], 'PyramidRoom4ChestItem', 'Pyramid: Room 4 Chest', 1, 26, []],
    138 : [445, 1, True, 32, [], 'PyramidHiero4Item', 'Pyramid: Hieroglyph 4', 1, 26, []],
    139 : [428, 1, True, 12, [], 'PyramidRoom5ChestItem', 'Pyramid: Room 5 Chest', 1, 26, []],
    140 : [446, 1, True, 35, [], 'PyramidHiero5Item', 'Pyramid: Hieroglyph 5', 1, 26, []],
    141 : [447, 1, True, 19, [], 'PyramidHiero6Item', 'Pyramid: Hieroglyph 6', 1, 26, []],
    142 : [413, 2, True, 0, [], '', 'Pyramid: Dark Space Bottom', 0, 26, []],
    143 : [461, 1, True, 14, [], 'BabelPillowItem', 'Babel: Pillow', 1, 12, []],
    144 : [461, 1, True, 1, [], 'BabelForceFieldItem', 'Babel: Force Field', 1, 12, []],
    145 : [461, 2, False, 0, [64, 65, 66], '', 'Babel: Dark Space Bottom', 2, 12, []],
    146 : [472, 2, False, 0, [64, 65, 66], '', 'Babel: Dark Space Top', 2, 29, []],
    147 : [715, 1, True, 34, [], 'MansionChestItem', "Jeweler's Mansion: Chest", 1, 32, []],
    740 : [838, 5, True, 740, [], 'MansionEastGateItem', "Jeweler's Mansion: Enemy for East Gate", 0, 32, [[609, 1]]],
    741 : [839, 5, True, 741, [], 'MansionWestGateItem', "Jeweler's Mansion: Enemy for West Gate", 0, 32, [[609, 1]]],
    148 : [101, 3, True, 100, [101, 102, 103, 104, 105], '', 'Castoth Prize', 0, 24, []],
    149 : [198, 3, True, 101, [100, 102, 103, 104, 105], '', 'Viper Prize', 0, 20, []],
    150 : [244, 3, True, 102, [100, 101, 103, 104, 105], '', 'Vampires Prize', 0, 35, []],
    151 : [302, 3, True, 103, [100, 101, 102, 104, 105], '', 'Sand Fanger Prize', 0, 14, []],
    152 : [448, 3, True, 104, [100, 101, 102, 103, 105], '', 'Mummy Queen Prize', 0, 33, []],
    153 : [479, 3, True, 105, [100, 101, 102, 103, 104], '', 'Babel Prize', 0, 29, []],
    500 : [500, 4, True, 500, [], '', 'Kara', 0, 23, []],
    501 : [840, 4, True, 501, [], '', 'Lilly', 0, 9, [[23, 1]]],
    502 : [502, 4, True, 502, [], '', 'Moon Tribe: Spirits Healed', 0, 6, []],
    503 : [503, 4, True, 503, [], '', 'Inca: Castoth defeated', 0, 24, []],
    504 : [122, 4, True, 504, [], '', 'Freejia: Found Laborer', 0, 6, []],
    505 : [505, 4, True, 505, [], '', "Neil's Memory Restored", 0, 12, []],
    506 : [841, 4, True, 506, [], '', 'Sky Garden: Map 82 NW Switch pressed', 0, 6, [[609, 1]]],
    507 : [189, 4, True, 507, [], '', 'Sky Garden: Map 82 NE Switch pressed', 0, 6, []],
    508 : [508, 4, True, 508, [], '', 'Sky Garden: Map 82 SE Switch pressed', 0, 6, []],
    509 : [509, 4, True, 509, [], '', 'Sky Garden: Map 84 Statue Switch pressed', 0, 6, []],
    510 : [842, 4, True, 510, [], '', 'Seaside: Fountain Purified', 0, 22, [[17, 1]]],
    511 : [511, 4, True, 511, [], '', 'Mu: Water Lowered 1', 0, 15, []],
    512 : [512, 4, True, 512, [], '', 'Mu: Water Lowered 2', 0, 28, []],
    513 : [274, 4, True, 513, [], '', 'Angel: Puzzle Complete', 0, 14, []],
    514 : [514, 4, True, 514, [], '', 'Mt Kress: Drops used 1', 0, 17, []],
    515 : [515, 4, True, 515, [], '', 'Mt Kress: Drops used 2', 0, 19, []],
    516 : [516, 4, True, 516, [], '', 'Mt Kress: Drops used 3', 0, 25, []],
    517 : [517, 4, True, 517, [], '', 'Pyramid: Hieroglyphs placed', 0, 33, []],
    518 : [518, 4, True, 518, [], '', 'Babel: Castoth defeated', 0, 29, []],
    519 : [519, 4, True, 519, [], '', 'Babel: Viper defeated', 0, 29, []],
    520 : [520, 4, True, 520, [], '', 'Babel: Vampires defeated', 0, 29, []],
    521 : [521, 4, True, 521, [], '', 'Babel: Sand Fanger defeated', 0, 29, []],
    522 : [522, 4, True, 522, [], '', 'Babel: Mummy Queen defeated', 0, 29, []],
    523 : [523, 4, True, 523, [], '', 'Mansion: Solid Arm defeated', 0, 32, []],
    524 : [843, 4, True, 524, [64, 66, 62, 63], '', 'Inca: Diamond Block Placed', 0, 3, [[7, 1]]],
    526 : [526, 4, True, 526, [], '', 'Mu: Access to Hope Room 1', 0, 14, []],
    527 : [527, 4, True, 527, [], '', 'Mu: Access to Hope Room 2', 0, 15, []],
    528 : [844, 4, True, 528, [], '', 'Mine: Blocked Tunnel Open', 0, 6, [[608, 1]]],
    529 : [529, 4, True, 529, [], '', 'Underground Tunnel: Bridge Open', 0, 13, []],
    530 : [530, 4, True, 530, [64, 66, 62, 63], '', 'Inca: Slug Statue Broken', 0, 3, []],
    531 : [531, 4, True, 531, [], '', 'Mu: Beat Vampires', 0, 35, []],
    603 : [491, 6, True, 67, [], '', 'Firebird access', 0, 500, []],
    525 : [525, 4, True, 525, [], '', 'Pyramid: Portals open', 0, 0, []],
    700 : [791, 5, True, 700, [], 'EDCageWormItem', 'Underground Tunnel: Worm for East Skeleton Cage', 0, 0, [[609, 1]]],
    701 : [792, 5, True, 701, [], 'EDSoutheastWormItem', 'Underground Tunnel: Worm for East Door', 0, 0, [[609, 1]]],
    702 : [793, 5, True, 702, [], 'EDSouthwestWormItem', 'Underground Tunnel: Worm for South Door', 0, 0, [[609, 1]]],
    703 : [794, 5, True, 703, [], 'EDDoorBatItem', 'Underground Tunnel: Bat for West Door', 0, 0, [[609, 1]]],
    704 : [795, 5, True, 704, [], 'EDDarkSpaceWormItem', 'Underground Tunnel: Worm for Appearing Dark Space', 0, 0, [[609, 1]]],
    710 : [801, 5, True, 710, [], 'IncaNSRampItem', 'Inca Ruins: Whirligig for N/S Ramp', 0, 0, [[609, 1]]],
    712 : [803, 5, True, 712, [], 'IncaDBlockMonsterItem', 'Inca Ruins: 4-Way West of Diamond Block Room', 0, 0, [[609, 1]]],
    713 : [804, 5, True, 713, [], 'IncaWMelodyMonsterItem', 'Inca Ruins: 4-Way Before Singing Statue', 0, 0, [[609, 1]]],
    717 : [812, 5, True, 717, [], 'MineWormCageItem', 'Diamond Mine: Worm for Big Room Cage', 0, 0, [[609, 1]]],
    718 : [813, 5, True, 718, [], 'MineWormDarkSpaceItem', 'Diamond Mine: Worm for Appearing Dark Space', 0, 0, [[609, 1]]],
    721 : [817, 5, True, 721, [], 'SGSEBotBarrierItem', 'Sky Garden: (SE) Bottom Robot for Chest', 0, 0, [[609, 1]]],
    723 : [819, 5, True, 723, [], 'SGSWTopRobotRampItem', 'Sky Garden: (SW) Top Robot for Robot Ramp', 0, 0, [[609, 1]]],
    725 : [821, 5, True, 725, [], 'SGSWBotFireCageItem', 'Sky Garden: (SW) Bot Robot for Fire Cages', 0, 0, [[609, 1]]],
    727 : [825, 5, True, 727, [], 'MuDroplet1Item', 'Mu: NE Droplet for Rock 1', 0, 0, [[609, 1]]],
    728 : [826, 5, True, 728, [], 'MuDroplet2Item', 'Mu: NE Droplet for Rock 2', 0, 0, [[609, 1]]],
    729 : [827, 5, True, 729, [], 'MuSlimeCageItem', 'Mu: West Slime for Slime Cages', 0, 0, [[609, 1]]],
    730 : [828, 5, True, 730, [], 'MuEastFacingHeadGolemItem', 'Mu: SE Golem for East-facing Head', 0, 0, [[609, 1]]],
    731 : [829, 5, True, 731, [], 'MuSouthFacingHeadGolemItem', 'Mu: SE Golem for South-facing Head', 0, 0, [[609, 1]]],
    734 : [832, 5, True, 734, [], 'KressSkullShortcutItem', 'Mt. Temple: Skull for Drops Chest 1 Shortcut', 0, 0, [[609, 1]]],
    736 : [834, 5, True, 736, [], 'WatEastSliderHoleItem', 'Ankor Wat: Scarab for Outer East Slider Hole', 0, 0, [[609, 1]]],
    739 : [837, 5, True, 739, [], 'PyramidEntranceOrbsItem', 'Pyramid: Entrance Orbs for DS Gate', 0, 0, [[609, 1]]]
}


# Here we read the original file, the "base" patch, and the configuration addresses.
if len(sys.argv) < 2:
    quit()

infile = open(sys.argv[1], "rb")
indata = infile.read()
infile.close()
if len(indata) == 0x200200:
    indata = indata[0x200:]   # remove SMC header

base_patch_file = open("iogrm_base.bsdiff", "rb")
base_patch_data = base_patch_file.read()
base_patch_file.close()

config_options = {}
cfgfile = open("iogrm_config.tsv", "r")
cfgreader = csv.reader(cfgfile, delimiter="\t", quotechar='"')
for row in cfgreader:
    config_options[row[0]] = int(row[1])
cfgfile.close()

iogrm_rom = bytearray(bsdiff4.patch(indata, base_patch_data))


# Here's where the patching starts. All writes are 16-bit except for room rewards and the title screen code.
def write16(array, addr, val):
    array[addr] = val & 0xff
    array[1+addr] = (val >> 8) & 0xff

# Write items to locations
ds_num = 1
for loc in item_locations:
    if item_locations[loc][1] not in [1,2]:
        # Types 3, 4, and 6 are artificial; 5 (monster orbs) are populated in the base patch
        continue
    elif item_locations[loc][1] == 1:
        # Normal item locations always require a ROM write
        loc_config_name = "Config_" + item_locations[loc][5]
        loc_addr = config_options[loc_config_name]
        loc_item = item_locations[loc][3]
        loc_item_id = item_pool[loc_item][2]
        write16(iogrm_rom, loc_addr, loc_item_id)
    elif item_locations[loc][1] == 2:
        # Dark Space locations require ROM writes if they "contain" a nonzero item
        loc_item = item_locations[loc][3]
        if loc_item:
            loc_item_id = item_pool[loc_item][2]
            ds_map_id = spawn_locations[loc][1]
            ds_loc_config_name = "Config_DarkSpaceItem"+str(ds_num)+"Item"
            ds_loc_addr = config_options[ds_loc_config_name]
            ds_map_config_name = "Config_DarkSpaceItem"+str(ds_num)+"Map"
            ds_map_addr = config_options[ds_map_config_name]
            write16(iogrm_rom, ds_loc_addr, loc_item_id)
            write16(iogrm_rom, ds_map_addr, ds_map_id)
            ds_num += 1
# Write other configuration
write16(iogrm_rom, config_options["Config_KaraLocation"], kara_location)
for hiero_slot in range(1,7):
    write16(iogrm_rom, config_options["Config_HieroOrder"+str(hiero_slot)], hieroglyph_order[hiero_slot-1])
write16(iogrm_rom, config_options["Config_IncaTileX"], inca_tile_pos[0])
write16(iogrm_rom, config_options["Config_IncaTileY"], inca_tile_pos[1])
write16(iogrm_rom, config_options["Config_InitialHp"], initial_hp)
for jeweler_line in range(1,8):
    write16(iogrm_rom, config_options["Config_Jeweler"+str(jeweler_line)+"Cost"], jeweler_costs[jeweler_line-1])
write16(iogrm_rom, config_options["Config_SettingStatuesPlayerChoice"], statues_player_choice)
write16(iogrm_rom, config_options["Config_StatuesRequiredCount"], statue_count)
for statue in range(1,7):
    if statue in statues_required:
        write16(iogrm_rom, config_options["Config_Statue"+str(statue)+"Required"], 1)
    else:
        write16(iogrm_rom, config_options["Config_Statue"+str(statue)+"Required"], 0)
for ishtar_room in [1,2,3,4]:
    for chg_idx in [1,2,3]:
        config_name = "Config_IshtarRoom"+str(ishtar_room)+"DifferenceIndex"+str(chg_idx)
        config_addr = config_options[config_name]
        write16(iogrm_rom, config_addr, ishtar_changes[ishtar_room-1][chg_idx-1])
base_room_reward_addr = config_options["Config_RoomClearRewards"]
this_room = 0
while this_room < 0x100:
    # Room rewards are the only 8-bit configuration values; all others are 16 bits
    reward = room_rewards[this_room]
    iogrm_rom[this_room + base_room_reward_addr] = reward
    this_room += 1
title_code_addr = config_options["Config_RandoTitleScreenHashString"]
for i in range(0,6):
    iogrm_rom[i + title_code_addr] = title_screen_code[i][0]


# Write out the patched ROM
outfile = open("iogrm.sfc", "wb")
outfile.write(iogrm_rom)
outfile.close()

