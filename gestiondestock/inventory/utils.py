# utils.py

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
