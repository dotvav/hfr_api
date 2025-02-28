"""Constants for HFR"""

import time
from datetime import datetime
from typing import Final

import requests
from bs4 import BeautifulSoup

from .topic import Topic

import re

CATEGORY_ID_INT_TO_STR: Final = {
    1: "Hardware",
    16: "HardwarePeripheriques",
    15: "OrdinateursPortables",
    2: "OverclockingCoolingModding",
    30: "electroniquedomotiquediy",
    23: "gsmgpspda",
    25: "apple",
    3: "VideoSon",
    14: "Photonumerique",
    5: "JeuxVideo",
    4: "WindowsSoftware",
    22: "reseauxpersosoho",
    21: "systemereseauxpro",
    11: "OSAlternatifs",
    10: "Programmation",
    12: "Graphisme",
    6: "AchatsVentes",
    8: "EmploiEtudes",
    13: "Discussions",
}

CATSUBCAT_ID_STR_TO_INT: Final = {
    "Hardware": {
        "carte-mere": 108,
        "Memoire": 534,
        "Processeur": 533,
        "2D-3D": 109,
        "Boitier": 466,
        "Alimentation": 532,
        "HDD": 110,
        "SSD": 531,
        "lecteur-graveur": 467,
        "minipc": 507,
        "Benchs": 252,
        "Materiels-problemes-divers": 253,
        "conseilsachats": 481,
        "hfr": 546,
        "actualites": 578,
    },
    "HardwarePeripheriques": {
        "Ecran": 451,
        "Imprimante": 452,
        "Scanner": 453,
        "webcam-camera-ip": 462,
        "Clavier-Souris": 454,
        "Joys": 455,
        "Onduleur": 530,
        "Divers": 456,
    },
    "OrdinateursPortables": {
        "portable": 448,
        "Ultraportable": 512,
        "Transportable": 516,
        "Netbook": 520,
        "Composant": 515,
        "Accessoire": 517,
        "Conseils-d-achat": 513,
        "SAV": 479,
    },
    "OverclockingCoolingModding": {
        "CPU": 458,
        "GPU": 119,
        "Air-Cooling": 117,
        "Water-Xtreme-Cooling": 118,
        "Silence": 400,
        "Modding": 461,
        "Divers-8": 121,
    },
    "electroniquedomotiquediy": {
        "conception_depannage_mods": 571,
        "nano-ordinateur_microcontroleurs_fpga": 572,
        "domotique_maisonconnectee": 573,
        "mecanique_prototypage": 574,
        "imprimantes3D": 575,
        "robotique_modelisme": 576,
        "divers": 577,
    },
    "gsmgpspda": {
        "autres-os-mobiles": 567,
        "operateur": 510,
        "telephone-android": 553,
        "telephone-windows-phone": 554,
        "telephone": 529,
        "tablette": 540,
        "android": 550,
        "windows-phone": 551,
        "GPS-PDA": 509,
        "accessoires": 561,
    },
    "apple": {
        "Mac-OS-X": 522,
        "Applications": 528,
        "Mac": 523,
        "Macbook": 524,
        "Iphone-amp-Ipod": 525,
        "Ipad": 535,
        "Peripheriques": 526,
    },
    "VideoSon": {
        "HiFi-HomeCinema": 130,
        "Materiel": 129,
        "Traitement-Audio": 131,
        "Traitement-Video": 134,
    },
    "Photonumerique": {
        "Appareil": 442,
        "Objectif": 519,
        "Accessoire": 443,
        "Photos": 444,
        "Technique": 445,
        "Logiciels-Retouche": 446,
        "Argentique": 447,
        "Concours": 476,
        "Galerie-Perso": 478,
        "Divers-7": 457,
    },
    "JeuxVideo": {
        "PC": 249,
        "Consoles": 250,
        "Achat-Ventes": 251,
        "Teams-LAN": 412,
        "Tips-Depannage": 413,
        "VR-Realite-Virtuelle": 579,
        "mobiles": 569,
    },
    "WindowsSoftware": {
        "windows-11": 580,
        "windows-10": 570,
        "windows-8": 555,
        "Windows-7-seven": 521,
        "Windows-vista": 505,
        "Windows-nt-2k-xp": 406,
        "Win-9x-me": 504,
        "Securite": 437,
        "Virus-Spywares": 506,
        "Stockage-Sauvegarde": 435,
        "Logiciels": 407,
        "Tutoriels": 438,
    },
    "reseauxpersosoho": {
        "FAI": 496,
        "Reseaux": 503,
        "Routage-et-securite": 497,
        "WiFi-et-CPL": 498,
        "Hebergement": 499,
        "Tel-TV-sur-IP": 500,
        "Chat-visio-et-voix": 501,
        "Tutoriels": 502,
    },
    "systemereseauxpro": {
        "Reseaux": 487,
        "Securite": 488,
        "Telecom": 489,
        "Infrastructures-serveurs": 491,
        "Stockage": 492,
        "Logiciels-entreprise": 493,
        "Management-SI": 494,
        "poste-de-travail": 544,
    },
    "OSAlternatifs": {
        "Codes-scripts": 209,
        "Debats": 205,
        "Divers-2": 420,
        "Hardware-2": 472,
        "Installation": 204,
        "Logiciels-2": 208,
        "Multimedia": 207,
        "reseaux-securite": 206,
    },
    "Programmation": {
        "ADA": 381,
        "Algo": 382,
        "Android": 562,
        "API-Win32": 518,
        "ASM": 384,
        "ASP": 383,
        "Big-Data": 565,
        "C": 440,
        "CNET-managed": 405,
        "C-2": 386,
        "Delphi-Pascal": 391,
        "Flash-ActionScript": 473,
        "HTML-CSS-Javascript": 389,
        "iOS": 563,
        "Java": 390,
        "Javascript-Node-js": 566,
        "Langages-fonctionnels": 484,
        "Perl": 392,
        "PHP": 393,
        "Python": 394,
        "Ruby": 483,
        "Shell-Batch": 404,
        "SGBD-SQL": 395,
        "VB-VBA-VBS": 396,
        "Windows-Phone": 564,
        "XML-XSL": 439,
        "Divers-6": 388,
    },
    "Graphisme": {
        "Cours": 475,
        "Galerie": 469,
        "Infographie-2D": 227,
        "PAO-Desktop-Publishing": 470,
        "Infographie-3D": 228,
        "Webdesign": 402,
        "Arts-traditionnels": 441,
        "Concours-2": 229,
        "Ressources": 230,
        "Divers-5": 231,
    },
    "AchatsVentes": {
        "Hardware": 169,
        "pc-portables": 536,
        "tablettes": 560,
        "Photo-Audio-Video": 171,
        "audio-video": 537,
        "Telephonie": 573,
        "Softs-livres": 170,
        "Divers-4": 174,
        "Avis-estimations": 398,
        "Feedback": 416,
        "Regles-coutumes": 399,
    },
    "EmploiEtudes": {
        "Marche-emploi": 233,
        "Etudes-Orientation": 235,
        "Annonces-emplois": 234,
        "Feedback-entreprises": 464,
        "Aide-devoirs": 465,
    },
    "Discussions": {
        "Actualite": 422,
        "politique": 482,
        "Societe": 423,
        "Cinema": 424,
        "Musique": 425,
        "Arts-Lecture": 426,
        "TV-Radio": 427,
        "Sciences": 428,
        "Sante": 429,
        "Sports": 430,
        "Auto-Moto": 431,
        "Cuisine": 433,
        "Loisirs": 434,
        "voyages": 557,
        "Viepratique": 432,
    },
}


CATEGORY_TOPICS_PAGE_URL = (
    "https://forum.hardware.fr/hfr/{str_id}/liste_sujet-{page}.htm"
)


class Category:
    def __init__(self, id: int):
        self.id: int = id
        self.topics: list[Topic] = []

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> datetime:
        d = timestamp_str[0:10]
        t = timestamp_str[13:18]
        return datetime.strptime(f"{d} {t}", "%d-%m-%Y %H:%M")

    def load_page(self, page: int) -> dict:
        time.sleep(1)

        url = str.format(
            CATEGORY_TOPICS_PAGE_URL, str_id=CATEGORY_ID_INT_TO_STR[self.id], page=page
        )

        r = requests.get(
            url,
            headers={
                "Accept": "text/html",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "User-Agent": "HFRTopicSummarizer",
            },
        )
        html = r.text

        return self.parse_page_html(html)

    def parse_page_html(self, html: str) -> dict:
        ts_min = None
        ts_max = None

        soup = BeautifulSoup(html, "html.parser")

        for topic_soup in soup.find_all("tr", class_="sujet"):
            href = topic_soup.find("td", class_="sujetCase3").find("a").attrs["href"]
            sticky = bool(
                topic_soup.find("td", class_="sujetCase3").find(
                    "img",
                    src=re.compile(r".*sticky.gif$"),
                )
            )
            post = int(href.split("_")[-2])
            cat_str = href.split("/")[2]
            subcat_str = href.split("/")[3]
            nb_messages = int(topic_soup.find("td", class_="sujetCase7").get_text())
            last_message = topic_soup.find("td", class_="sujetCase9").get_text()
            ts = self.parse_timestamp(last_message)
            max_page = int(1 + nb_messages / 1000)

            self.topics.append(
                Topic(
                    cat=self.id,
                    subcat=CATSUBCAT_ID_STR_TO_INT[cat_str][subcat_str],
                    post=post,
                    max_page=max_page,
                    max_date=ts.strftime("%Y-%m-%d"),
                    sticky=sticky,
                )
            )

            if not sticky:
                if not ts_min or ts < ts_min:
                    ts_min = ts
                if not ts_max or ts > ts_max:
                    ts_max = ts

        return {"ts_min": ts_min, "ts_max": ts_max}
