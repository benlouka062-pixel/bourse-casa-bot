import requests
import json
import time
from datetime import datetime

class MetalsAnalyzer:
    def __init__(self, api_key="goldapi-kqb19mlv7mcz7-io"):
        """
        Analyseur de métaux précieux et industriels
        Pour MNG, SMI, CMT (Compagnie Minière de Touissit)
        """
        self.api_key = api_key
        self.base_url = "https://www.goldapi.io/api"
        self.session = requests.Session()
        self.session.headers.update({'x-access-token': self.api_key})
        
        # === MÉTAUX PRÉCIEUX (via GoldAPI) ===
        self.metals_precieux = {
            "XAU": {
                "nom": "Or",
                "symbole": "XAU",
                "unite": "$/oz",
                "minieres_correliees": ["MNG", "CMT"]  # MNG (or), CMT (filons or)
            },
            "XAG": {
                "nom": "Argent",
                "symbole": "XAG",
                "unite": "$/oz",
                "minieres_correliees": ["MNG", "SMI", "CMT"]  # Toutes les minières
            }
        }
        
        # === MÉTAUX INDUSTRIELS (sources alternatives) ===
        self.metaux_industriels = {
            "XCU": {
                "nom": "Cuivre",
                "symbole": "XCU",
                "unite": "$/lb",
                "minieres_correliees": ["MNG", "CMT"],  # MNG (cuivre), CMT (projet Tabaroucht)
                "source": "LME"  # London Metal Exchange
            },
            "XPB": {
                "nom": "Plomb",
                "symbole": "XPB",
                "unite": "$/t",
                "minieres_correliees": ["SMI", "CMT"],  # SMI (plomb), CMT (plomb)
                "source": "LME"
            },
            "XZN": {
                "nom": "Zinc",
                "symbole": "XZN",
                "unite": "$/t",
                "minieres_correliees": ["SMI", "CMT"],  # SMI (zinc), CMT (zinc)
                "source": "LME"
            }
        }
        
        # Minières marocaines et leurs métaux
        self.minieres = {
            "MNG": {
                "nom": "Managem",
                "metaux": ["XAU", "XAG", "XCU"],  # Or, Argent, Cuivre
                "pays": "Maroc"
            },
            "SMI": {
                "nom": "Société Métallurgique d'Imiter",
                "metaux": ["XAG", "XPB", "XZN"],  # Argent, Plomb, Zinc
                "pays": "Maroc"
            },
            "CMT": {
                "nom": "Compagnie Minière de Touissit",
                "metaux": ["XPB", "XZN", "XAG", "XCU"],  # Plomb, Zinc, Argent, Cuivre
                "pays": "Maroc",
                "notes": "Projet cuivre Tabaroucht + filons or Tighza"
            }
        }
    
    def get_metal_precieux(self, metal):
        """Récupère le prix d'un métal précieux via GoldAPI"""
        try:
            url = f"{self.base_url}/{metal}/USD"
            r = self.session.get(url, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                return {
                    "prix": data.get('price'),
                    "variation": data.get('ch', 0),
                    "variation_pct": data.get('cp', 0),
                    "timestamp": datetime.now().isoformat(),
                    "source": "GoldAPI"
                }
            else:
                print(f"⚠️ GoldAPI {metal}: {r.status_code}")
        except Exception as e:
            print(f"⚠️ Exception {metal}: {e}")
        
        return None
    
    def get_metal_industriel(self, metal):
        """
        Récupère le prix d'un métal industriel
        Version simplifiée avec données simulées (à remplacer par vraie API)
        """
        # Prix indicatifs (à remplacer par appel API LME ou autre)
        prix_reference = {
            "XCU": 4.20,   # $/lb (cuivre)
            "XPB": 2100,    # $/t (plomb)
            "XZN": 2500     # $/t (zinc)
        }
        
        variation = {
            "XCU": 0.3,
            "XPB": -0.2,
            "XZN": 0.5
        }
        
        if metal in prix_reference:
            return {
                "prix": prix_reference[metal],
                "variation": variation[metal],
                "variation_pct": variation[metal],
                "timestamp": datetime.now().isoformat(),
                "source": "LME (simulé - à connecter)"
            }
        return None
    
    def get_all_metals(self):
        """Récupère les prix de tous les métaux"""
        results = {
            "precieux": {},
            "industriels": {},
            "timestamp": datetime.now().isoformat()
        }
        
        print("\n🏅 MÉTAUX PRÉCIEUX")
        print("="*40)
        for metal, infos in self.metals_precieux.items():
            print(f"  → {infos['nom']}...", end=" ")
            data = self.get_metal_precieux(metal)
            if data:
                results["precieux"][metal] = {**infos, **data}
                print(f"✅ {data['prix']} USD")
            else:
                print("❌")
            time.sleep(1)
        
        print("\n🔧 MÉTAUX INDUSTRIELS")
        print("="*40)
        for metal, infos in self.metaux_industriels.items():
            print(f"  → {infos['nom']}...", end=" ")
            data = self.get_metal_industriel(metal)
            if data:
                results["industriels"][metal] = {**infos, **data}
                print(f"✅ {data['prix']} {infos['unite']}")
            else:
                print("❌")
            time.sleep(1)
        
        return results
    
    def analyser_correlation(self, metals_data, actions_data):
        """
        Analyse la corrélation entre métaux et minières
        """
        correlations = []
        
        if not metals_data or not actions_data:
            return correlations
        
        # Créer un dictionnaire des actions par symbole
        actions_dict = {a['sym']: a for a in actions_data if a.get('prix')}
        
        # Analyser chaque minière
        for miniere, infos in self.minieres.items():
            if miniere not in actions_dict:
                continue
            
            action = actions_dict[miniere]
            metaux_correlations = []
            
            # Vérifier chaque métal associé à cette minière
            for metal_code in infos["metaux"]:
                metal_data = None
                
                # Chercher dans les métaux précieux
                if metal_code in metals_data.get("precieux", {}):
                    metal_data = metals_data["precieux"][metal_code]
                
                # Chercher dans les métaux industriels
                elif metal_code in metals_data.get("industriels", {}):
                    metal_data = metals_data["industriels"][metal_code]
                
                if metal_data:
                    metaux_correlations.append({
                        "metal": metal_data["nom"],
                        "prix_metal": metal_data["prix"],
                        "variation_metal": metal_data.get("variation_pct", 0),
                        "prix_miniere": action.get("prix"),
                        "correlation": "À calculer avec historique"
                    })
            
            correlations.append({
                "miniere": miniere,
                "miniere_nom": infos["nom"],
                "miniere_prix": action.get("prix"),
                "miniere_signal": action.get("signal", "N/A"),
                "metaux": metaux_correlations
            })
        
        return correlations
    
    def analyser_specifique_cmt(self, metals_data):
        """Analyse spécifique pour CMT avec ses multiples métaux"""
        if "CMT" not in self.minieres:
            return None
        
        cmt_metaux = []
        
        # Cuivre (projet Tabaroucht)
        if "XCU" in metals_data.get("industriels", {}):
            cuivre = metals_data["industriels"]["XCU"]
            cmt_metaux.append({
                "metal": "Cuivre",
                "prix": cuivre["prix"],
                "unite": cuivre["unite"],
                "impact": "Projet Tabaroucht (prévu 2024)"
            })
        
        # Argent
        if "XAG" in metals_data.get("precieux", {}):
            argent = metals_data["precieux"]["XAG"]
            cmt_metaux.append({
                "metal": "Argent",
                "prix": argent["prix"],
                "unite": argent["unite"],
                "impact": "Production historique"
            })
        
        # Plomb & Zinc
        for metal in ["XPB", "XZN"]:
            if metal in metals_data.get("industriels", {}):
                m = metals_data["industriels"][metal]
                cmt_metaux.append({
                    "metal": m["nom"],
                    "prix": m["prix"],
                    "unite": m["unite"],
                    "impact": "Production principale"
                })
        
        return {
            "miniere": "CMT",
            "nom": "Compagnie Minière de Touissit",
            "metaux": cmt_metaux,
            "note": "Diversification cuivre + or en développement"
        }

# Test du module
if __name__ == "__main__":
    analyzer = MetalsAnalyzer()
    
    # Récupérer tous les métaux
    metals = analyzer.get_all_metals()
    
    print("\n" + "="*60)
    print("📊 ANALYSE COMPLÈTE DES MÉTAUX")
    print("="*60)
    
    # Métaux précieux
    print("\n🏅 MÉTAUX PRÉCIEUX")
    for metal, data in metals["precieux"].items():
        print(f"\n{data['nom']} ({data['symbole']})")
        print(f"  Prix: {data['prix']} {data['unite']}")
        print(f"  Variation: {data.get('variation_pct', 0):+.2f}%")
        print(f"  Minières liées: {', '.join(data['minieres_correliees'])}")
    
    # Métaux industriels
    print("\n🔧 MÉTAUX INDUSTRIELS")
    for metal, data in metals["industriels"].items():
        print(f"\n{data['nom']} ({data['symbole']})")
        print(f"  Prix: {data['prix']} {data['unite']}")
        print(f"  Source: {data['source']}")
        print(f"  Minières liées: {', '.join(data['minieres_correliees'])}")
    
    # Analyse spécifique CMT
    print("\n" + "="*60)
    print("⛏️  ANALYSE SPÉCIFIQUE CMT")
    print("="*60)
    cmt_analyse = analyzer.analyser_specifique_cmt(metals)
    if cmt_analyse:
        for m in cmt_analyse["metaux"]:
            print(f"\n• {m['metal']}: {m['prix']} {m['unite']}")
            print(f"  Impact: {m['impact']}")
        print(f"\n📌 {cmt_analyse['note']}")
