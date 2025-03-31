"""
Serviço para fornecer informações sobre aeroportos e companhias aéreas
"""

# Mapeamento de códigos IATA para nomes de aeroportos e cidades
AIRPORT_DATA = {
    # Aeroportos brasileiros mais comuns
    "GRU": {"name": "Aeroporto Internacional de São Paulo/Guarulhos", "city": "São Paulo", "country": "Brasil"},
    "CGH": {"name": "Aeroporto de Congonhas", "city": "São Paulo", "country": "Brasil"},
    "VCP": {"name": "Aeroporto Internacional de Viracopos", "city": "Campinas", "country": "Brasil"},
    "SDU": {"name": "Aeroporto Santos Dumont", "city": "Rio de Janeiro", "country": "Brasil"},
    "GIG": {"name": "Aeroporto Internacional do Galeão", "city": "Rio de Janeiro", "country": "Brasil"},
    "BSB": {"name": "Aeroporto Internacional de Brasília", "city": "Brasília", "country": "Brasil"},
    "CNF": {"name": "Aeroporto Internacional de Confins", "city": "Belo Horizonte", "country": "Brasil"},
    "SSA": {"name": "Aeroporto Internacional de Salvador", "city": "Salvador", "country": "Brasil"},
    "REC": {"name": "Aeroporto Internacional do Recife", "city": "Recife", "country": "Brasil"},
    "FOR": {"name": "Aeroporto Internacional de Fortaleza", "city": "Fortaleza", "country": "Brasil"},
    "CWB": {"name": "Aeroporto Internacional de Curitiba", "city": "Curitiba", "country": "Brasil"},
    "POA": {"name": "Aeroporto Internacional de Porto Alegre", "city": "Porto Alegre", "country": "Brasil"},
    "FLN": {"name": "Aeroporto Internacional de Florianópolis", "city": "Florianópolis", "country": "Brasil"},
    "NAT": {"name": "Aeroporto Internacional de Natal", "city": "Natal", "country": "Brasil"},
    "BEL": {"name": "Aeroporto Internacional de Belém", "city": "Belém", "country": "Brasil"},
    "VIX": {"name": "Aeroporto de Vitória", "city": "Vitória", "country": "Brasil"},
    "AJU": {"name": "Aeroporto Internacional de Aracaju", "city": "Aracaju", "country": "Brasil"},
    "MCZ": {"name": "Aeroporto Internacional de Maceió", "city": "Maceió", "country": "Brasil"},
    
    # Aeroportos internacionais populares
    "JFK": {"name": "Aeroporto Internacional John F. Kennedy", "city": "Nova York", "country": "Estados Unidos"},
    "LAX": {"name": "Aeroporto Internacional de Los Angeles", "city": "Los Angeles", "country": "Estados Unidos"},
    "MIA": {"name": "Aeroporto Internacional de Miami", "city": "Miami", "country": "Estados Unidos"},
    "LHR": {"name": "Aeroporto de Heathrow", "city": "Londres", "country": "Reino Unido"},
    "CDG": {"name": "Aeroporto Charles de Gaulle", "city": "Paris", "country": "França"},
    "FRA": {"name": "Aeroporto de Frankfurt", "city": "Frankfurt", "country": "Alemanha"},
    "MAD": {"name": "Aeroporto de Madrid-Barajas", "city": "Madri", "country": "Espanha"},
    "FCO": {"name": "Aeroporto Leonardo da Vinci", "city": "Roma", "country": "Itália"},
    "LIS": {"name": "Aeroporto de Lisboa", "city": "Lisboa", "country": "Portugal"},
    "EZE": {"name": "Aeroporto Internacional Ministro Pistarini", "city": "Buenos Aires", "country": "Argentina"},
    "SCL": {"name": "Aeroporto Internacional Comodoro Arturo Merino Benítez", "city": "Santiago", "country": "Chile"},
    "BOG": {"name": "Aeroporto Internacional El Dorado", "city": "Bogotá", "country": "Colômbia"},
    "MEX": {"name": "Aeroporto Internacional da Cidade do México", "city": "Cidade do México", "country": "México"},
    "DXB": {"name": "Aeroporto Internacional de Dubai", "city": "Dubai", "country": "Emirados Árabes Unidos"},
    "SYD": {"name": "Aeroporto de Sydney", "city": "Sydney", "country": "Austrália"},
    "NRT": {"name": "Aeroporto Internacional de Narita", "city": "Tóquio", "country": "Japão"},
    "HKG": {"name": "Aeroporto Internacional de Hong Kong", "city": "Hong Kong", "country": "China"},
}

# Mapeamento de códigos IATA para companhias aéreas
AIRLINE_DATA = {
    # Companhias brasileiras
    "G3": {"name": "GOL Linhas Aéreas", "country": "Brasil"},
    "AD": {"name": "Azul Linhas Aéreas", "country": "Brasil"},
    "LA": {"name": "LATAM Airlines", "country": "Brasil"},
    "O6": {"name": "Avianca Brasil", "country": "Brasil"},
    
    # Companhias internacionais
    "AA": {"name": "American Airlines", "country": "Estados Unidos"},
    "UA": {"name": "United Airlines", "country": "Estados Unidos"},
    "DL": {"name": "Delta Air Lines", "country": "Estados Unidos"},
    "AC": {"name": "Air Canada", "country": "Canadá"},
    "AF": {"name": "Air France", "country": "França"},
    "BA": {"name": "British Airways", "country": "Reino Unido"},
    "IB": {"name": "Iberia", "country": "Espanha"},
    "LH": {"name": "Lufthansa", "country": "Alemanha"},
    "AZ": {"name": "Alitalia", "country": "Itália"},
    "TP": {"name": "TAP Air Portugal", "country": "Portugal"},
    "EK": {"name": "Emirates", "country": "Emirados Árabes Unidos"},
    "QR": {"name": "Qatar Airways", "country": "Catar"},
    "TK": {"name": "Turkish Airlines", "country": "Turquia"},
    "AV": {"name": "Avianca", "country": "Colômbia"},
    "AM": {"name": "Aeroméxico", "country": "México"},
    "AR": {"name": "Aerolíneas Argentinas", "country": "Argentina"},
    "CM": {"name": "Copa Airlines", "country": "Panamá"},
    "KL": {"name": "KLM", "country": "Holanda"},
}

def get_airport_info(iata_code):
    """
    Retorna informações sobre o aeroporto com base no código IATA
    
    Args:
        iata_code: Código IATA do aeroporto (ex: GRU, MIA)
        
    Returns:
        dict: Informações do aeroporto ou dicionário vazio se não encontrado
    """
    if not iata_code:
        return {}
        
    iata_code = iata_code.upper()
    if iata_code in AIRPORT_DATA:
        return AIRPORT_DATA[iata_code]
    else:
        # Se não encontrarmos o aeroporto, retornamos um objeto com o código
        return {"name": f"Aeroporto {iata_code}", "city": iata_code, "country": ""}

def get_airline_info(iata_code):
    """
    Retorna informações sobre a companhia aérea com base no código IATA
    
    Args:
        iata_code: Código IATA da companhia aérea (ex: G3, AA)
        
    Returns:
        dict: Informações da companhia ou dicionário vazio se não encontrado
    """
    if not iata_code:
        return {}
        
    iata_code = iata_code.upper()
    if iata_code in AIRLINE_DATA:
        return AIRLINE_DATA[iata_code]
    else:
        # Se não encontrarmos a companhia, retornamos um objeto com o código
        return {"name": f"Companhia {iata_code}", "country": ""}

def get_airport_display_name(iata_code):
    """
    Retorna o nome de exibição do aeroporto (Cidade - Nome do Aeroporto)
    
    Args:
        iata_code: Código IATA do aeroporto
        
    Returns:
        str: Nome para exibição ou o próprio código se não encontrado
    """
    if not iata_code:
        return ""
        
    info = get_airport_info(iata_code)
    if info and info.get("city"):
        return f"{info['city']} ({iata_code})"
    return iata_code

def get_airline_display_name(iata_code):
    """
    Retorna o nome de exibição da companhia aérea
    
    Args:
        iata_code: Código IATA da companhia aérea
        
    Returns:
        str: Nome para exibição ou o próprio código se não encontrado
    """
    if not iata_code:
        return ""
        
    info = get_airline_info(iata_code)
    if info and info.get("name"):
        return f"{info['name']} ({iata_code})"
    return iata_code