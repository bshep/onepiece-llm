import json
import os

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

class AliasResolver:
    def __init__(self, alias_file="dumps/aliases.json"):
        self.alias_map = {} # alias -> main_name
        if os.path.exists(alias_file):
            try:
                with open(alias_file, "r") as f:
                    data = json.load(f)
                    for main_name, aliases in data.items():
                        for alias in aliases:
                            # Lowercase for case-insensitive matching
                            self.alias_map[alias.lower()] = main_name
            except Exception as e:
                print(f"Warning: Could not load aliases: {e}")

    def resolve(self, name):
        """Resolves an alias to the main name."""
        return self.alias_map.get(name.lower(), name)

    def expand_query(self, query):
        """
        Attempts to find aliases in the query and adds the main name to it.
        This is a simple implementation; better ones might use NER or keyword extraction.
        """
        words = query.split()
        expanded_terms = set()
        
        # Check for multi-word aliases (sliding window)
        # We'll check windows of 1-3 words
        words_lower = [w.lower().strip(",.?!") for w in words]
        for n in range(1, 4):
            for i in range(len(words_lower) - n + 1):
                phrase = " ".join(words_lower[i:i+n])
                if phrase in self.alias_map:
                    expanded_terms.add(self.alias_map[phrase])
        
        if expanded_terms:
            return query + " (" + ", ".join(expanded_terms) + ")"
        return query
