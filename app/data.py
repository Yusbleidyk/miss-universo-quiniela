"""Seed data: candidatas de Miss Universe 2026, agrupadas por continente.

Fuente: Wikipedia + missuniverse.com (consultado el 23/11/2026). La final de
esta edicion es el 24/11/2026 en San Juan, Puerto Rico. Se usa solo para
armar la quiniela de votacion entre amigos -- no tiene relacion con el
resultado real del concurso.
"""

# Cada tupla: (pais, nombre, continente)
CANDIDATAS: list[tuple[str, str, str]] = [
    # Africa
    ("Botswana", "Dabilo Moses", "Africa"),
    ("Camerun", "Audrey Black", "Africa"),
    ("Cabo Verde", "Armandina Cunha", "Africa"),
    ("Republica Democratica del Congo", "Jessi Kalambayi", "Africa"),
    ("Egipto", "Sonia Gergis", "Africa"),
    ("Guinea Ecuatorial", "Isabel Mbomio", "Africa"),
    ("Etiopia", "Bruk Belete", "Africa"),
    ("Ghana", "Belvy Ofori", "Africa"),
    ("Guinea", "Justine Kamara", "Africa"),
    ("Kenia", "Jean Ojiro", "Africa"),
    ("Mayotte", "Maeva Toumbou Dani", "Africa"),
    ("Namibia", "Charene Labuschagne", "Africa"),
    ("Nigeria", "Danielle Adewusi", "Africa"),
    ("Reunion", "Abigaelle Tailamee", "Africa"),
    ("Sierra Leona", "Katti Fofanah", "Africa"),
    ("Sudafrica", "Bajabulise Thela", "Africa"),
    ("Tanzania", "Elizabeth Makune", "Africa"),
    ("Tunez", "Sarrah Brahmi", "Africa"),
    ("Uganda", "Mitchelle Daka", "Africa"),
    # Asia
    ("Armenia", "Arena Zeynalian", "Asia"),
    ("Bangladesh", "Samira Khan Mahi", "Asia"),
    ("Camboya", "Rthna Than", "Asia"),
    ("China", "Shiqi Wang", "Asia"),
    ("Hong Kong", "Jennifer Zhou", "Asia"),
    ("India", "Kaziah Mejo", "Asia"),
    ("Irak", "Samantha Slewa", "Asia"),
    ("Israel", "Danielle Yablonka", "Asia"),
    ("Japon", "Sayuki Ito", "Asia"),
    ("Jordania", "Destiny Anbar", "Asia"),
    ("Kazajistan", "Alina Ekaterinecheva", "Asia"),
    ("Kirguistan", "Medina Ermekova", "Asia"),
    ("Libano", "Perla Harb", "Asia"),
    ("Macao", "Xuhe Hou", "Asia"),
    ("Mongolia", "Namuunaa Otgonbaatar", "Asia"),
    ("Myanmar", "May Grace Parry", "Asia"),
    ("Pakistan", "Misbah Arshad", "Asia"),
    ("Filipinas", "Bea Millan-Windorski", "Asia"),
    ("Corea del Sur", "Yurim Kim", "Asia"),
    ("Sri Lanka", "Nimhara Sasindi", "Asia"),
    ("Uzbekistan", "Ziedakhon Sharipova", "Asia"),
    # Europa
    ("Albania", "Jogersa Beqiri", "Europa"),
    ("Belarus", "Aliya Karotkaya", "Europa"),
    ("Belgica", "Olga Lombardo", "Europa"),
    ("Croacia", "Antea Mrsic", "Europa"),
    ("Republica Checa", "Dominika Kotouckova", "Europa"),
    ("Dinamarca", "Fie Rose Lindegaard", "Europa"),
    ("Estonia", "Emili Denneng", "Europa"),
    ("Finlandia", "Veera Gronlund", "Europa"),
    ("Francia", "Garance Authie", "Europa"),
    ("Alemania", "Celina Weil", "Europa"),
    ("Gran Bretana", "Angela Aumonier", "Europa"),
    ("Grecia", "Olivia Vasilopoulos", "Europa"),
    ("Hungria", "Kamilla Kiss", "Europa"),
    ("Islandia", "Sigridur Hrafnkelsdottir", "Europa"),
    ("Irlanda", "Aideen Howard", "Europa"),
    ("Italia", "Giada Folcia", "Europa"),
    ("Kosovo", "Evisa Pacolli", "Europa"),
    ("Letonia", "Lasma Kuhtarska", "Europa"),
    ("Lituania", "Olga Bykadorova", "Europa"),
    ("Malta", "Francesca Mercieca", "Europa"),
    ("Moldavia", "Dorina Darii", "Europa"),
    ("Montenegro", "Aleksandra Ivezaj", "Europa"),
    ("Paises Bajos", "Melissa Bottema", "Europa"),
    ("Noruega", "Abelone Smedsrud", "Europa"),
    ("Polonia", "Vivica Lewandowski", "Europa"),
    ("Portugal", "Isabela Santos", "Europa"),
    ("Rumania", "Sabina Parmac", "Europa"),
    ("Rusia", "Alexandra Stashkevich", "Europa"),
    ("Serbia", "Nikolina Vujcic", "Europa"),
    ("Eslovaquia", "Anna Lickova", "Europa"),
    ("Espana", "Susana Medina", "Europa"),
    ("Suecia", "Josefin Strand", "Europa"),
    ("Suiza", "Itiya Dube", "Europa"),
    ("Ucrania", "Anna Nikonova", "Europa"),
    # America del Norte, Centroamerica y Caribe
    ("Aruba", "Elizabeth Johnson", "America del Norte y Caribe"),
    ("Bahamas", "Shawndra Henfield", "America del Norte y Caribe"),
    ("Belice", "Caleigh-Rose West", "America del Norte y Caribe"),
    ("Bonaire", "Caroline Porras", "America del Norte y Caribe"),
    ("Islas Virgenes Britanicas", "Orealia Thomas", "America del Norte y Caribe"),
    ("Canada", "Aslihan Morali", "America del Norte y Caribe"),
    ("Islas Caiman", "Juliana Myers", "America del Norte y Caribe"),
    ("Costa Rica", "Mariale Acosta", "America del Norte y Caribe"),
    ("Cuba", "Mia Dio", "America del Norte y Caribe"),
    ("Curazao", "Bianty Gomperts", "America del Norte y Caribe"),
    ("Republica Dominicana", "Melissa Nunez", "America del Norte y Caribe"),
    ("El Salvador", "Sofia Cordova", "America del Norte y Caribe"),
    ("Guadalupe", "Chloe Deher", "America del Norte y Caribe"),
    ("Guatemala", "Adelina Castillo", "America del Norte y Caribe"),
    ("Haiti", "Tatenda Rameau", "America del Norte y Caribe"),
    ("Honduras", "Luisa Pineda", "America del Norte y Caribe"),
    ("Jamaica", "Celene Hall", "America del Norte y Caribe"),
    ("Martinica", "Larissa Segarel", "America del Norte y Caribe"),
    ("Mexico", "Maria Vargas", "America del Norte y Caribe"),
    ("Nicaragua", "Jasmine Blandford", "America del Norte y Caribe"),
    ("Panama", "Gabriela Gonzalez", "America del Norte y Caribe"),
    ("Puerto Rico", "Jennifer Barreto", "America del Norte y Caribe"),
    ("Santa Lucia", "Bernella Velinor", "America del Norte y Caribe"),
    ("San Martin", "Elle Duncan", "America del Norte y Caribe"),
    ("Trinidad y Tobago", "Vinita Manoo", "America del Norte y Caribe"),
    ("Islas Turcas y Caicos", "Selena Grant", "America del Norte y Caribe"),
    ("Estados Unidos", "Justus Kelley", "America del Norte y Caribe"),
    ("Islas Virgenes de EE.UU.", "Jenna-Monet Queeley", "America del Norte y Caribe"),
    # America del Sur
    ("Argentina", "Daiana Pereyra", "America del Sur"),
    ("Bolivia", "Valeria Mena", "America del Sur"),
    ("Brasil", "Marcella Kozinski", "America del Sur"),
    ("Chile", "Dominga Lopez", "America del Sur"),
    ("Colombia", "Maria Alejandra Lopez", "America del Sur"),
    ("Ecuador", "Dalia Bucaram", "America del Sur"),
    ("Guyana", "Angel Bhathal", "America del Sur"),
    ("Paraguay", "Gretha Matiauda", "America del Sur"),
    ("Peru", "Luren Marquez", "America del Sur"),
    ("Surinam", "Maruschka Sahiboe", "America del Sur"),
    ("Uruguay", "Lucia Pineyro", "America del Sur"),
    ("Venezuela", "Clara Vegas", "America del Sur"),
    # Oceania
    ("Australia", "Caitlin Worthington", "Oceania"),
    ("Nueva Zelanda", "Georgia Waddington", "Oceania"),
]

# Secuencia de rondas y cuantas avanzan en cada una. Calca el formato
# oficial de Miss Universe (edicion 2025, la mas reciente confirmada):
# preliminar -> Top 30 -> Top 12 (traje de bano) -> Top 5 (vestido de
# noche) -> Top 3 (preguntas) -> ganadora (pregunta final).
#
# IMPORTANTE: el concurso real NO reparte cupos por continente para armar
# el Top 30 -- es puro puntaje de la competencia preliminar entre todas las
# candidatas juntas. Por eso "groups" tiene un cupo unico (30), igual que
# el resto de las rondas; el campo "continente" en CANDIDATAS es solo
# informativo/visual, no se usa para calcular cupos.
ORDEN_RONDAS: list[str] = ["groups", "top30", "top12", "top5", "top3", "done"]
CUPO_RONDA: dict[str, int] = {"groups": 30, "top30": 12, "top12": 5, "top5": 3, "top3": 1}
