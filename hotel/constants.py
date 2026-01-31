"""Constantes partagées pour l'application hotel.

Contient la liste standard de postes/rôles utilisables dans le projet.
"""

STANDARD_POSITIONS = [
    "Directeur d'hôtel",
    "Directeur adjoint",
    "Responsable d'exploitation",
    "Chef de réception",
    "Réceptionniste",
    "Agent de réservation",
    "Concierge",
    "Femme de chambre",
    "Responsable ménage",
    "Cuisinier",
    "Chef de cuisine",
    "Serveur",
    "Plongeur",
    "Technicien de maintenance",
    "Responsable maintenance",
    "Comptable",
    "Portier",
    "Responsable commercial",
    "Responsable RH",
]

ROLE_PAGES = {
    'admin': ['/admin/dashboard/', '/admin/clients/', '/admin/chambres/', '/admin/reservations/', '/admin/utilisateurs/'],
    'employe': ['/employe/dashboard/', '/employe/reservations/', '/employe/chambres/'],
    'client': ['/client/dashboard/', '/client/mes-reservations/', '/client/chambres/'],
}
