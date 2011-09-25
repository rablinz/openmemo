from enum import Enum

class AlgorithmLUData (object):
    """ Base class for algorithm parameter containers. 
    
    It stores input parameters for a concrete algorithm for a single learning unit. 
    It keeps also a reference to the learning unit which repetion is scheduled. 
    Note: what is a learning unit, is application dependent. 
    
    The reference will be used in some global data adapter callbacks 
    (e.g. searching a reverse LU for the currently scheduled LU).
    
    * ``next_review_date`` - datetime.date of next planned review
    * ``next_review_time``
    * ``last_review_date`` - datetime.date of last review or None for a new LU, not seen before
    * ``last_review_time``
    * ``status`` - what is the next step with this item - recall it in the same learning session (low grade)
        or to remove it from the current session because it has been recognized correctly    
    """
    
    LUStatus = Enum("FINAL_DRILL", "MEMORIZED")
    
    def __init__(self, lu, *args, **kwargs):
        self.lu = lu

        self.last_review_date = None
        self.last_review_time = None
        self.next_review_date = None
        self.next_review_time = None            
        self.status = None
    

class AlgorithmGlobalData (object):
    """ Defines operations which gather data not associated with the current 
    learning unit in a more global context.
    
    Input data passed to the algorithm describes learning parameters of a single LU.
    Some algorithms require in some cases parameter summaries of more than one LU.
    Other may need a more global data which is known after some intermediate calculations
    (at the beginning of the calculations the algorithm doesn't know if it is 
    doing to request more data and what additional data is required).
    """
    
    def __init__(self, *args, **kwargs):
        pass


class Algorithm (object):
    """ Base class for a repetion scheduling algorithm. 
    
    Keeps a reference to a provider for gathering parameters that are out of scope 
    of the current LU algorithm data. 
    """
    
    def __init__(self, global_data, *args, **kwargs):
        self.global_data = global_data
    
    def schedule(self, lu_data, today=None):
        """ Calculates next repetion for a LU. 
        
        Updates ``next_review`` and ``last_review`` fields of ``lu_data``. 
        """
        raise NotImplementedError()
    
    def fill_initial_algorithm_lu_data(self, lu_data):
        """ Fills the initial algorithm parameters for a newly created LU. """
        
        raise NotImplementedError()
    