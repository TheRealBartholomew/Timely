def calculate_priority(effort, urgency, length, w1=0.3, w2=0.5, w3=0.2):
    
    #Calculate weighted priority score
    
    #Args:
    #    effort (int): Task effort (1-10)
    #    urgency (int): Task urgency (1-10)
    #    length (float): Task length in hours
    #    w1, w2, w3 (float): Weights (must sum to 1)
    
    #Returns:
    #    float: Priority score (0-10 scale)
    
    #Raises:
    #    ValueError: If weights don't sum to 1
    
    if abs(w1 + w2 + w3 - 1.0) > 0.001:  # Float comparison tolerance
        raise ValueError("Weights must sum to 1")

    normalized_length = min(length / 8.0 * 10, 10)
    
    priority = (effort * w1) + (urgency * w2) + (normalized_length * w3)
    
    return round(priority, 2)