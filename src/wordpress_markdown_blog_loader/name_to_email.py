from text_unidecode import unidecode


def name_to_email(name: str) -> str:
    """
    name to email Xebia style.

    >>> name_to_email("Léon Rodenburg")
    'leon.rodenburg@xebia.com'
    >>> name_to_email("Mark van Holsteijn")
    'mark.vanholsteijn@xebia.com'
    >>> name_to_email("Jorge Liauw-a-joe")
    'jorge.liauwajoe@xebia.com'
    >>> name_to_email("Jan-Justin van Tonder")
    'janjustin.vantonder@xebia.com'
    """
    email_name_exceptions = {}
    parts = name.replace("-", "").split()
    email = unidecode(
        f'{parts[0]}{"." if len(parts) > 1 else ""}{"".join(parts[1:])}@xebia.com'.lower()
    )
    return email_name_exceptions.get(email, email)
