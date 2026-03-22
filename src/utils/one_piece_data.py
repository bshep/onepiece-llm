# Chronological order of One Piece arcs
ONE_PIECE_ARCS = [
    "Romance Dawn Arc",
    "Orange Town Arc",
    "Syrup Village Arc",
    "Baratie Arc",
    "Arlong Park Arc",
    "Loguetown Arc",
    "Warship Island Arc",
    "Reverse Mountain Arc",
    "Whiskey Peak Arc",
    "Little Garden Arc",
    "Drum Island Arc",
    "Arabasta Arc",
    "Post-Arabasta Arc",
    "Goat Island Arc",
    "Ruluka Island Arc",
    "Jaya Arc",
    "Skypiea Arc",
    "G-8 Arc",
    "Long Ring Long Land Arc",
    "Ocean's Dream Arc",
    "Foxy's Return Arc",
    "Water 7 Arc",
    "Enies Lobby Arc",
    "Post-Enies Lobby Arc",
    "Ice Hunter Arc",
    "Thriller Bark Arc",
    "Spa Island Arc",
    "Sabaody Archipelago Arc",
    "Special Historical Arc",
    "Amazon Lily Arc",
    "Impel Down Arc",
    "Little East Blue Arc",
    "Marineford Arc",
    "Post-War Arc",
    "Return to Sabaody Arc",
    "Fish-Man Island Arc",
    "Z's Ambition Arc",
    "Punk Hazard Arc",
    "Caesar Retrieval Arc",
    "Dressrosa Arc",
    "Silver Mine Arc",
    "Zou Arc",
    "Marine Rookie Arc",
    "Whole Cake Island Arc",
    "Levely Arc",
    "Wano Country Arc",
    "Uta's Past Arc",
    "Cidre Guild Arc",
    "Egghead Arc",
    "Elbaph Arc"
]

def get_visible_arcs(current_arc):
    """Returns a list of arcs that are not spoilers based on the current arc."""
    if current_arc not in ONE_PIECE_ARCS:
        return ONE_PIECE_ARCS
    
    idx = ONE_PIECE_ARCS.index(current_arc)
    return ONE_PIECE_ARCS[:idx + 1]

def is_spoiler(arc_name, current_arc):
    """Checks if an arc is a spoiler based on the current arc."""
    if arc_name == "unknown" or arc_name is None:
        return False
        
    if current_arc not in ONE_PIECE_ARCS:
        return False
        
    try:
        current_idx = ONE_PIECE_ARCS.index(current_arc)
        arc_idx = ONE_PIECE_ARCS.index(arc_name)
        return arc_idx > current_idx
    except ValueError:
        # If the arc name is not in our list, we play it safe
        return False
