from datetime import date, timedelta, datetime, time
import logging
from math import exp, log
import sys

from .algorithm import AlgorithmLUData, AlgorithmGlobalData, Algorithm


logger = logging.getLogger(__name__)


class SSRFAlgorithmLUData (AlgorithmLUData):
    """ SSRF algorithm parameters for a single learning unit. 
    
    Instance variables:
    * ``grade`` - see SSRFAlgorithm documentation for allowed values
    * ``num_reviews`` - number of review; starts from 1 for a new LU
    * ``avg_grade`` - average grade
    * ``priority`` - material priority; see SSRFAlgorithm documentation for allowed values
    * ``difficulty`` - how this LU compares to an ideal LU
    """

    def __init__(self, lu, *args, **kwargs):
        super(SSRFAlgorithmLUData, self).__init__(lu, *args, **kwargs)

        self.grade = None        
        self.num_reviews = None
        self.avg_grade = None
        self.priority = None
        self.difficulty = None

    def __str__(self):
        return "grade: %(grade)s, num_reviews: %(num_reviews)d, \
avg_grade: %(avg_grade).2f, priority: %(priority)1.1f, \
difficulty: %(difficulty).2f, status: %(status)s" % \
            {"grade": self.grade, "num_reviews": self.num_reviews,
             "avg_grade": self.avg_grade, "priority": self.priority, 
             "difficulty": self.difficulty, "status": self.status}

class SSRFAlgorithmGlobalData (AlgorithmGlobalData):
    """ Interface implemented by global LU data provider for the SSRF algorithm. """
    
    def get_workloads(self, from_date, to_date):
        """ Returns a list with number of items scheduled between from and to date. 
        
        The number of workloads must be equal to the number of days between ``from_date`` and ``to_date``.
        """
        
        raise NotImplementedError()
    
    def get_avg_difficulties(self, from_date, to_date):
        """ Returns a list with average difficulties of items scheduled between from and to date.
        
        The number of average difficulties must be equal to the number of days between ``from_date`` and ``to_date``.
        """
        
        raise NotImplementedError()


class SSRFAlgorithm (Algorithm):
    """ 
    Acknowledgments
    ===============
    This algorithm is a result of Dariusz Laska's (dariuszlaska(at)gmail.com) 
    work on the spaced repetition area. He is the author of algorithm concepts 
    and foundations. We would like to thank him for the donation and support 
    he provided us with during the implementation and testing phases.
    
    Objectives
    ==========
    1. maximize local accuracy -> maximize the probability of one-period recall 
    for a particular item.
    2. maximize global accuracy -> maximize the probability of recall for all the items.

    local specificity: expanding rehearsal (spaced repetitions) and overlearning avoidance,
    global specificity: cognitive load avoidance (by minimizing average workloads 
    and average difficulty of scheduled study material)

    local accuracy: there is a set of acceptable inter-repetition intervals for an item .
    global accuracy: there is a good interval in a set of the acceptable intervals 
    found by minimizing an average workload and an average difficulty.
    
    Basic notions
    =============
    Testing effect 
      `http://en.wikipedia.org/wiki/Testing_effect <http://en.wikipedia.org/wiki/Testing_effect>`_
      
    Spaced repetitions, expanding rehearsal 
      `http://en.wikipedia.org/wiki/Spaced_repetition <http://en.wikipedia.org/wiki/Spaced_repetition>`_
      
    Overlearning
      `http://www.sciencedaily.com/releases/2007/08/070829122934.htm <http://www.sciencedaily.com/releases/2007/08/070829122934.htm>`_, 
      `http://www.pashler.com/Articles/RohrerPashler2007CDPS.pdf <http://www.pashler.com/Articles/RohrerPashler2007CDPS.pdf>`_
      
    Cognitive load
      `http://en.wikipedia.org/wiki/Cognitive_load, http://edutechwiki.unige.ch/en/Cognitive_load <http://en.wikipedia.org/wiki/Cognitive_load, http://edutechwiki.unige.ch/en/Cognitive_load>`_

    Parameters
    ==========
    * Number of reviews `n` - number of days when an item was presented for a review 
    (if you see an item few times during one session, n increases just by one)
    * Average Grade `AG(n-1)` - estimated mean value of grades for (n-1)-th review 
    (thus current grade is not included)
    * current Grade `G(n)` - first grade given during n-th (current) review, 
    next grades during n-th session are biased (you have already seen an answer), 
    so they are simply ignored
    * Priority of material `P` - can be set by an user locally (for a particular item) 
    or globally (for specific categories or even for a whole database)

    Parameters and inter-repetition intervals
    -----------------------------------------
    ================================  ===========================
    Parameters                        Intervals (ceteris paribus)
    ================================  ===========================
    higher Number of reviews `n`      longer
    higher Average Grade `AG(n-1)`    longer
    higher current Grade `G(n)`       longer
    higher Priority of material P`P`  shorter

    Grades and their meanings
    =========================
    =====  ====================  ===========
    Grade  An answer is          Domain
    =====  ====================  ===========
    5      instantly recalled    recall
    4      slowly recalled       recall    
    3      partially recalled    recall
    2      instantly recognized  recognition
    1      slowly recognized     recognition
    0      not recognized        recognition

    Remark:
    Average Grade AG(n-1) = 2.5 means that the quality of an answer is somewhere 
    between 'instantly recognized' and 'partially recalled'.
    
    If the probability of recognition is very high, say ~100%, 
    then the probability of recall equals ~50%, thus even if the recognition 
    is certain, the recall is still highly uncertain.

    Priorities of a studied material
    ================================
    ========  ======  =============  ===================      
    Priority  Values  Objective      Suggested for words
    ========  ======  =============  ===================
    high      4.0    total accuracy  most common (<= 2,000)
    mid       3.0    ...             frequent (<= 10,000)
    low       2.0    total recall    rare (> 10,000)

    Formulas used in the algorithms
    ===============================
    SSRF
    ----
    Calculates a maximum acceptable value of inter-repetition interval 
    for a given number of reviews, average and current grades 
    and for a specific priority of studied material. 
    To avoid an overlearning effect, it assumes 1 day as the minimum interval.
    
    ::   
        SSRF = overlearning correction interval + base interval * scale factor        
        SSRF(n, AG(n-1), G(n), P) = 1 + n ^ (AG(n-1) / 2) * exp(G(n) - P)
        
    where
    * n - number of reviews
    * AG(n-1) - previous average grade
    * G(n) - current grade
    * P - priority of material

    difficulty
    ----------
    Calculates a difficulty of a LU through comparing its last interval
    with the interval of an ideal LU.
        
    The ideal LU is a LU with the average grade (AG) = 5.0 and the current grade = 5 
    
    :: 
        D(P, Iideal, Ilast) = ln((Iideal + 1.0) / (Ilast + 1.0))
    
    where
    * Iideal = SSRF(n, 5.0, 5, P)
    * Ilast - last interval
    * P - priority of material

    load coefficient
    ----------------
    Mean squared error of minimun workload to daily workload ratio and 
    minimum average difficulty to daily average difficulty ratio.  
    
    ::
        LC(W, Wmin, AD, ADmin) = ((Wmin / W - 1) ^ 2 + (ADmin / AD - 1) ^ 2) / 2
        if W = Wmin then Wmin / W = 1
        if AD = ADmin then ADmin / AD = 1
    
    where
    * W - workload for a given date
    * Wmin - minimum workload in a given period
    * AD - average difficulty for a given date
    * ADmin - minimum average difficulty in a given period

    How it works, or finding a good inter-repetition interval
    =========================================================
    #. If the LU has FINAL_DRILL status, look at the current grade. 
    If the grade is between 0 and 2, return (without doing anything).
    If the grade is between 3 and 5, change status to RECOGNITION and return. 
    
    #. Calculate minimum and maximum acceptable repetion intervals:
    Imin = SSRF[n, AG(n-1), G(n) - 1, P]
    Imax = SSRF[n, AG(n-1), G(n), P]

    #. Collect workloads for dates between min. and max. acceptable repetition 
    interval (both inclusive).
    
    #. If there is at least one date with zero workload, choose the latest date
    with the zero workload as the good interval.
    
    #. Otherwise collect average difficulties for dates between min. and max. 
    acceptable repetition interval (both inclusive).

    #. Calculate load coefficients for each date between the min. and max.
    acceptable repetition interval (both inclusive).
    
    #. Calculate daily workloads and average difficulties in case the repetition 
    of current LU was scheduled on each date from min. - max. acceptable interval period.
    
    ::
        Wnew = W + 1 (for each date)
        Dnew = D(P, Iideal, I), where I = Imin, Imin + 1, ... Imax - 1, Imax
        ADnew = (W * AD + Dnew) / Wnew (for each date) 

    #. Calculate load coefficients for each date in case of LU repeated on this date
    
    #. An interval with the maximum load coefficient reduction = good interval (day)
    
    #. Depending on the grade, set the LU status: FINAL_DRILL for grades between 0 and 2, 
    RECOGNITION for status between 3 and 5. 
    
    Initial/default values
    ======================        
        
    Average grade AG(1) = 2.5 (alternative value, not used in this implementation - average grade for all items)
    
    Priority of material P = 3.0 (alternative value, not used in this implementation - average priority of all items)
    """
    
    GRADES = (0, 1, 2, 3, 4, 5)
    
    MIN_GRADE = GRADES[0]
    MAX_GRADE = GRADES[len(GRADES) - 1]
    FINAL_DRILL_GRADES = (0, 1, 2)

    PRIORITY_LOW = 2.0
    PRIORITY_MID = 3.0
    PRIORITY_HIGH = 4.0
    
    PRIORITIES = (PRIORITY_LOW, PRIORITY_MID, PRIORITY_HIGH)
    
    _DEFAULT_AVG_GRADE = 2.5
    _DEFAULT_PRIORITY = PRIORITY_MID
    
    def __init__(self, global_data, *args, **kwargs):
        super(SSRFAlgorithm, self).__init__(global_data, *args, **kwargs)
        
    def schedule(self, lu_data, now=None):
        """ Calculates next repetion for a LU and sets ``next_review`` field. 
        
        See the class docstring for an exact description of the scheduling algorithm. 
        """
        logger.debug("Input LU data: %s", lu_data)
        
        # Check preconditions
        self._assert_lu_data(lu_data)
        
        if now is None:
            now = datetime.utcnow()
        today = now.date()

        # If the LU status is FINAL_DRILL, it is already scheduled.
        # Update simply it's status depending on the current grade
        if lu_data.status == AlgorithmLUData.LUStatus.FINAL_DRILL:
            self._update_lu_data_status(lu_data)
            lu_data.last_review = now
            logger.debug("Output LU data: %s", lu_data)

            return
                
        # Calculate minimum and maximum acceptable repetion intervals
        min_interval = self._calculate_interval(lu_data.num_reviews,
                                                lu_data.avg_grade,
                                                lu_data.grade - 1,
                                                lu_data.priority)
        max_interval = self._calculate_interval(lu_data.num_reviews,
                                                lu_data.avg_grade,
                                                lu_data.grade,
                                                lu_data.priority)
        logger.debug("Min/max acceptable intervals: %d/%d", min_interval, max_interval)
        assert min_interval <= max_interval, \
            "min. interval %s > max. interval %s" % (min_interval, max_interval)

        # Get daily workloads for dates between min. and max. interval
        date_from = today + timedelta(min_interval) 
        date_to = today + timedelta(max_interval) 
        workloads = self.global_data.get_workloads(date_from, date_to)
        logger.debug("Workloads (from/to: %s/%s): %s", 
                     date_from, date_to, workloads)
        assert len(workloads) == max_interval - min_interval + 1, \
            "Workloads length doesn't match the number of days between min. and max. interval"
        
        # Check if there is a day with no workload
        zero_workload_ind = self._find_last_zero_workload_ind(workloads)
        if zero_workload_ind != None:
            # If true, this is the ideal interval
            ideal_interval = min_interval + zero_workload_ind
        else:
            # Get daily difficulties for dates between min. and max. interval
            avg_difficulties = self.global_data.get_avg_difficulties(date_from, date_to)
            logger.debug("Avg. difficulties (from/to: %s/%s): %s", 
                         date_from, date_to, avg_difficulties)
            assert len(avg_difficulties) == len(workloads), \
                "Avg. difficulties length doesn't match the workloads length"

            # Find the ideal interval with the maximum load reduction
            max_load_reduction_ind = self._find_max_load_reduction_ind(lu_data,
                                                                       range(min_interval, max_interval + 1), 
                                                                       workloads, 
                                                                       avg_difficulties)
            ideal_interval = min_interval + max_load_reduction_ind

        logger.debug("Ideal interval: %d", ideal_interval)
        
        # Update LU algorithm parameters
        self._update_lu_data_after_scheduling(lu_data, ideal_interval)
        self._update_lu_data_status(lu_data)
        
        # Set a new schedule date based on the ideal interval
        lu_data.last_review = now
        lu_data.next_review = datetime.combine(today + timedelta(ideal_interval), now.time())
        
        logger.debug("Output LU data: %s", lu_data)
        
        # Check postconditions
        self._assert_lu_data(lu_data)
        assert min_interval <= ideal_interval <= max_interval, \
            "ideal interval should be between min. and max. interval"
    
    def _calculate_interval(self, num_reviews, prev_avg_grade, grade, priority):
        """ Calculates a maximum acceptable value of inter-repetition interval (SSRF). 
         
        See the class docstring for an exact description of the method. 
        """
        # Check preconditions
        self._assert_num_reviews(num_reviews)
        self._assert_avg_grade(prev_avg_grade)
        assert grade in (SSRFAlgorithm.MIN_GRADE - 1,) + SSRFAlgorithm.GRADES, \
            "grade %s should be -1 or one of allowed grades" % grade
        self._assert_priority(priority)
        
        overlearning_factor = 1;
        base_interval = num_reviews ** (prev_avg_grade / 2.0)
        scale_factor = exp(grade - priority)
        interval = overlearning_factor + int(round(base_interval * scale_factor))
        
        # Check postconditions
        self._assert_interval(interval)
        
        return interval 

    def _find_last_zero_workload_ind(self, workloads):
        """ Finds an index of the last zero workload or None if all workloads are greater than 0. """
        # Check preconditions
        self._assert_workloads(workloads)

        # If there is no zero workload 0, return None
        if 0 not in workloads:
            return None
        
        # Return last zero workload index 
        rev_workloads = workloads[:]
        rev_workloads.reverse()
        last_zero_workload_ind = (len(workloads) - 1) - rev_workloads.index(0)
        
        # Check postconditions
        assert 0 <= last_zero_workload_ind <= (len(workloads) - 1), \
            "Zero workload index %s should one of the valid workload indexes"  % last_zero_workload_ind

        return last_zero_workload_ind
        
    def _find_max_load_reduction_ind(self, lu_data, intervals, workloads, avg_difficulties):
        """ Finds an index of the maximum load reduction in case the repetition 
        of the current LU was added to the schedule described with workloads and avg. difficulties.
        """
        # Check preconditions
        self._assert_lu_data(lu_data)
        self._assert_intervals(intervals)
        self._assert_workloads(workloads)
        self._assert_avg_difficulties(avg_difficulties)

        # Calculate load coefficients for each date
        load_coeffs = self._calculate_load_coeffs(workloads, avg_difficulties)
        logger.debug("Load coefficients: %s", load_coeffs)
        
        # Calculate daily workloads and average difficulties in case 
        # the repetition of current LU was scheduled on min. - max. interval dates
        new_workloads = map(lambda workload: workload + 1, workloads)
        logger.debug("New workloads: %s", new_workloads)
        def new_avg_difficulty(interval, workload, avg_difficulty, new_workload):
            new_difficulty = self._calculate_difficulty(lu_data.num_reviews, 
                                              lu_data.priority, 
                                              interval)
            logger.debug("New difficulty for the interval %d: %s", interval, new_difficulty)
            return (workload * avg_difficulty + new_difficulty) / new_workload 
        new_avg_difficulties = map(new_avg_difficulty, 
                                   intervals, workloads, avg_difficulties, new_workloads)
        logger.debug("New avg. difficulties: %s", new_avg_difficulties)
        
        # Calculate load coefficient for each date in case of LU repeated on this date
        new_load_coeffs = self._calculate_load_coeffs(new_workloads, new_avg_difficulties)
        logger.debug("New load coefficients: %s", new_load_coeffs)
        
        # Choose the date with the maximum load coefficient reduction
        load_coeff_rel = map(lambda coeff1, coeff2: coeff1 / coeff2 if coeff2 != 0 else sys.maxint, 
                             new_load_coeffs, load_coeffs)
        logger.debug("Load coefficient relations (new to old): %s", load_coeff_rel)
        load_coeff_rel.reverse()
        max_load_reduction_ind = (len(load_coeff_rel) - 1) - load_coeff_rel.index(min(load_coeff_rel))
        
        # Check postconditions
        assert 0 <= max_load_reduction_ind <= len(load_coeffs) - 1, \
            "Max. load coefficient reduction index %s should one of the valid load coefficient indexes"  % max_load_reduction_ind
        
        return max_load_reduction_ind

    def _calculate_load_coeffs(self, workloads, avg_difficulties):
        """ Calcuates load coefficients based on workloads and averages difficulties.
         
        See the class docstring for an exact description of the method. 
        """
        # Check preconditions
        self._assert_workloads(workloads)
        self._assert_avg_difficulties(avg_difficulties)
        assert len(avg_difficulties) == len(workloads), \
             "Avg. difficulties length doesn't match the workloads length"
        
        min_workload = float(min(workloads))
        min_difficulty = float(min(avg_difficulties))
        calculate_load_coeffs = lambda workload, avg_difficulty: \
            (((min_workload / workload - 1) ** 2 if workload != 0 else 0.0) + \
             ((min_difficulty / avg_difficulty - 1) ** 2 if avg_difficulty != 0.0 else 0.0)) / 2
        load_coeffs = map(calculate_load_coeffs, workloads, avg_difficulties)

        # Check postconditions
        self._assert_load_coeffs(load_coeffs)
        
        return load_coeffs 

    def _update_lu_data_after_scheduling(self, lu_data, ideal_interval):
        """ Updates the LU algorithm parameters after a successful scheduling. """
        # Check preconditions
        self._assert_lu_data(lu_data)
        
        new_num_reviews = lu_data.num_reviews + 1
        new_avg_grade = (lu_data.avg_grade * lu_data.num_reviews + lu_data.grade) / new_num_reviews  
        new_difficulty = self._calculate_difficulty(lu_data.num_reviews, 
                                                    lu_data.priority, 
                                                    ideal_interval)
        lu_data.num_reviews = new_num_reviews
        lu_data.avg_grade = new_avg_grade
        lu_data.difficulty = new_difficulty        

        # Check postconditions
        self._assert_lu_data(lu_data)

    def _update_lu_data_status(self, lu_data):
        """ Updates the LU status depending on the last grade. 
        
        A LU can be drilled during the same learning session or can be marked
        as memorized (it will be recalled on the scheduled repetition date.
        """
        if lu_data.grade in SSRFAlgorithm.FINAL_DRILL_GRADES:
            lu_data.status = AlgorithmLUData.LUStatus.FINAL_DRILL
        else:
            lu_data.status = AlgorithmLUData.LUStatus.MEMORIZED

    def _calculate_difficulty(self, num_reviews, priority, last_interval):
        """ Calcuates a difficulty of a LU.
         
        See the class docstring for an exact description of the method. 
        """
        # Check preconditions
        self._assert_num_reviews(num_reviews)
        self._assert_priority(priority)
        self._assert_interval(last_interval)
        
        ideal_interval = self._calculate_interval(num_reviews, 
                                        SSRFAlgorithm.MAX_GRADE, 
                                        SSRFAlgorithm.MAX_GRADE, 
                                        priority)
        difficulty = log((ideal_interval + 1.0) / (last_interval + 1.0))
        
        # Check postconditions
        self._assert_difficulty(difficulty)
        
        return difficulty

    def _assert_grade(self, grade):
        assert grade in SSRFAlgorithm.GRADES, \
            "grade %s should be one of allowed grades" % grade
    
    def _assert_num_reviews(self, num_reviews):
        assert num_reviews > 0, "number of reviews %s should be > 0" % num_reviews
    
    def _assert_avg_grade(self, avg_grade):
        assert SSRFAlgorithm.MIN_GRADE <= avg_grade <= SSRFAlgorithm.MAX_GRADE, \
            "avg. grade %s should be between min. and max. allowed grade" % avg_grade

    def _assert_priority(self, priority):
        assert priority in SSRFAlgorithm.PRIORITIES, \
            "priority %s should be one of allowed priorities" % priority

    def _assert_difficulty(self, difficulty):
        assert difficulty >= 0.0, "difficulty %s should be >= 0.0" % difficulty
    
    def _assert_lu_data(self, lu_data):
        self._assert_grade(lu_data.grade)
        self._assert_num_reviews(lu_data.num_reviews)
        self._assert_avg_grade(lu_data.avg_grade)
        self._assert_priority(lu_data.priority)
        self._assert_difficulty(lu_data.difficulty)

    def _assert_interval(self, interval):
        assert interval >= 1, "interval %s should be >= 1" % interval

    def _assert_intervals(self, intervals):
        for interval in intervals:
            self._assert_interval(interval)
        
    def _assert_workloads(self, workloads):
        for workload in workloads:
            assert workload >= 0, "all workloads %s should be >= 0" % workloads
    
    def _assert_avg_difficulties(self, avg_difficulties):
        for avg_difficulty in avg_difficulties:
            assert avg_difficulty >= 0.0, \
                "all avg. difficulties %s should be >= 0"  % avg_difficulties

    def _assert_load_coeffs(self, load_coeffs):
        for load_coeff in load_coeffs:
            assert 0.0 <= load_coeff <= 1.0, \
                "all load coefficients %s should be between 0.0 and 1.0"  % load_coeffs

    def fill_initial_algorithm_lu_data(self, lu_data):
        """ Fills the initial SSRF algorithm parameters for a newly created LU. """
        lu_data.grade = SSRFAlgorithm.MIN_GRADE
        
        lu_data.num_reviews = 1
        lu_data.avg_grade = SSRFAlgorithm._DEFAULT_AVG_GRADE
        lu_data.priority = SSRFAlgorithm._DEFAULT_PRIORITY
        lu_data.difficulty = 0.0
        lu_data.status = AlgorithmLUData.LUStatus.MEMORIZED
        
        # check postconditions
        self._assert_lu_data(lu_data)
