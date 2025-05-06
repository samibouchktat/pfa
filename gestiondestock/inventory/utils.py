# inventory/utils.py

from twilio.rest import Client  # Si tu utilises Twilio pour l'envoi de SMS


def envoyer_sms(numero_telephone):
    # Exemple d'envoi de SMS avec Twilio
    client = Client('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN')

    message = client.messages.create(
        body="Voici votre code de confirmation",
        from_='+1XXXXXXXXXX',  # Ton numéro Twilio
        to=numero_telephone
    )

    return message.sid  # Retourne l'ID du message envoyé


def analyze_articles(articles, low_threshold=5):
    """
    Pour chaque article, calcule un statut en fonction de sa quantité :
      - 'Rupture' si quantité <= 0
      - 'Stock faible' si quantité <= low_threshold
      - 'OK' sinon
    Retourne une liste de dicts contenant nom, reference, quantite et statut.
    """
    report = []
    for art in articles:
        q = getattr(art, 'quantite', 0)
        if q <= 0:
            statut = 'Rupture'
        elif q <= low_threshold:
            statut = 'Stock faible'
        else:
            statut = 'OK'
        report.append({
            'nom': art.nom,
            'reference': art.reference,
            'quantite': q,
            'statut': statut,
        })
    return report


def generate_report(stats, low_stock_items=None):
    """
    Génère un rapport plus complet :
    - Titre avec emoji
    - Synthèse chiffres-clés
    - Liste des articles critiques (rupture ou stock faible)
    - Mini-analyse de tendance
    - Recommandations détaillées
    """
    lines = []
    # 1. Titre
    lines.append(f"🗓️ **Rapport Stock – {stats['date']}**\n")

    # 2. Synthèse
    lines.append("🔢 **Chiffres clés :**")
    lines.append(f" • Total d’articles     : {stats['totalArticles']}")
    lines.append(f" • Stock disponible     : {stats['stockDisponible']}")
    lines.append(f" • Articles en rupture  : {stats['ruptures']}")
    lines.append(f" • Commandes en attente : {stats['cmdEnAttente']}\n")

    # 3. Articles critiques
    if low_stock_items:
        lines.append("⚠️ **Articles critiques :**")
        for item in low_stock_items:
            lines.append(f"   - {item['nom']} (quantité {item['quantite']}) → {item['statut']}")
        lines.append("")  # ligne vide

    # 4. Mini-tendance
    if stats.get('last_week_stock') is not None:
        delta = stats['stockDisponible'] - stats['last_week_stock']
        trend = "↗️ augmentation" if delta > 0 else "↘️ diminution" if delta < 0 else "⏸️ stable"
        lines.append(f"📈 Tendance hebdo : {trend} de {abs(delta)} unités\n")

    # 5. Recommandations
    lines.append("💡 **Recommandations :**")
    if stats['ruptures'] > 0:
        lines.append(" • Relancer immédiatement les fournisseurs pour les ruptures.")
    elif low_stock_items:
        lines.append(" • Surveiller les articles en stock faible listés ci-dessus.")
    else:
        lines.append(" • Bon niveau de stock global ! Continuez ainsi.")

    return "\n".join(lines)

