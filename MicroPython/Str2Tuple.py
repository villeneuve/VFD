# fonction pour convertir chaine recue via USB et main_2 qui est au format
# "[(6,0,35)-(7,0,25)-(12,0,0)]" en liste tuple utilisable par le programme
# journalier qui attend le format [(6, 0, 35), (7, 0, 25), (12, 0, 0)] liste
# qui ne contient que 1 a x (pas de max.) tuple de triplet d'entiers.

import re

def str2tuple(chaine: str):
    # 1. Vérification des bordures et absence d'espaces
    if not (chaine.startswith("[") and chaine.endswith("]")):
        return None
    if " " in chaine:
        return None
        
    if chaine == '[]':  #  program vide
        return []

    # Enlève '[' au début et ']' à la fin
    contenu = chaine[1:-1]

    # 2. Expression régulière pour un seul tuple de 3 entiers positifs : (X,Y,Z)
    pattern_tuple = r"^\((\d+),(\d+),(\d+)\)"

    resultat = []
    position = 0
    longueur = len(contenu)

    while position < longueur:
        # Recherche du motif au niveau du curseur actuel
        match = re.search(pattern_tuple, contenu[position:])

        if not match:
            # Si le motif ne correspond pas, la chaîne est invalide
            return None

        # Extraction des 3 entiers
        a, b, c = match.group(1), match.group(2), match.group(3)
        resultat.append((int(a), int(b), int(c)))

        # Avance le curseur de la taille du tuple trouvé ex: "(0,25,300)" -> 10 caractères
        position += len(match.group(0))

        # S'il reste du texte, le caractère suivant DOIT être un tiret '-'
        if position < longueur:
            if contenu[position] != "-":
                return None
            position += 1  # Passe le tiret

    # Si la boucle s'est terminée correctement et qu'au moins 1 tuple a été trouvé
    return resultat if resultat else None
