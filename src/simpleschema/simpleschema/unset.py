class UnsetType:
    """
    A holder value, like NoneType, that indicates a value has never been 
    provided before.
    
    Assumed to be a singleton.
    """
    def __str__(self):
        return "UNSET"
        
    def __repr__(self):
        return "UNSET"
        
    def __nonzero__(self):
        return False

UNSET = UnsetType()