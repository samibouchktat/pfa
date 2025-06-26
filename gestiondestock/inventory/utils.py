import openai
from django.conf import settings

def generate_openai_report(data_summary, model="gpt-3.5-turbo", max_tokens=800):
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY non défini dans les settings.")

    client = openai.OpenAI(api_key=api_key)  # Nouveau client !

    prompt = (
        "Vous êtes un expert en gestion de la chaîne d’approvisionnement au niveau mondial. "
        "À partir des données suivantes pour chaque article, qui proviennent de votre entrepôt local :\n"
        + "\n".join(data_summary)
        + "\n\n"
        "Veuillez générer un rapport structuré comprenant :\n"
        "1. **Analyse comparative globale** : Situer ces chiffres par rapport aux tendances mondiales du secteur (rotations, ruptures, surstocks).\n"
        "2. **Indicateurs clés de performance (KPI)** : Taux de couverture des stocks, délai de rotation moyen, stock de sécurité recommandé.\n"
        "3. **Risques et points de vigilance** : Articles à risque de rupture, exposition financière sur les surstocks, vulnérabilités de la chaîne.\n"
        "4. **Recommandations stratégiques** : Ajustements de niveaux de réapprovisionnement, diversification des fournisseurs, prévisions de demande.\n"
        "5. **Plan d’action** : Prochaines étapes concrètes à court, moyen et long terme.\n\n"


    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Assistant de génération de rapport"},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()
generate_report = generate_openai_report
