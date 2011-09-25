import logging
import mox
from datetime import date, timedelta
from openmemo.tests.tools import *

from openmemo.algorithms.ssrf import SSRFAlgorithmLUData, SSRFAlgorithmGlobalData, SSRFAlgorithm


logging.basicConfig(format=logging.BASIC_FORMAT, level=logging.DEBUG)


class SimpleSSRFAlgorithmLUData (SSRFAlgorithmLUData):
    def __init__(self, lu, *args, **kwargs):
        super(SimpleSSRFAlgorithmLUData, self).__init__(lu, *args, **kwargs)

    def set_attributes(self, **kwargs):
        self.__dict__.update(kwargs)


class TestSSRFAlgorithm (TestCase):
    def setUp(self):
        self._global_data = mox.MockObject(SSRFAlgorithmGlobalData)
        self._algorithm = SSRFAlgorithm(self._global_data)
    
    def _create_lu_data(self, **kwargs):
        lu_data = SimpleSSRFAlgorithmLUData(None)
        self._algorithm.fill_initial_algorithm_lu_data(lu_data)
        lu_data.set_attributes(**kwargs)
        return lu_data
    
    def test_initial_lu_data(self):
        lu_data = self._create_lu_data()
        assert_equals(SSRFAlgorithm.MIN_GRADE, lu_data.grade)
        assert_equals(1, lu_data.num_reviews)
        assert_equals(2.5, lu_data.avg_grade)
        assert_equals(SSRFAlgorithm.PRIORITY_MID, lu_data.priority)
        assert_equals(0.0, lu_data.difficulty)
    
    def test__calculate_interval_first_rep(self):
        interval = self._algorithm._calculate_interval(1, 0.0, 0, SSRFAlgorithm.PRIORITY_MID)
        self._assert_interval(1, interval)
        interval = self._algorithm._calculate_interval(1, 0.0, 2, SSRFAlgorithm.PRIORITY_MID)
        self._assert_interval(1, interval)
        interval = self._algorithm._calculate_interval(1, 0.0, 3, SSRFAlgorithm.PRIORITY_MID)
        self._assert_interval(2, interval)
        interval = self._algorithm._calculate_interval(1, 0.0, 5, SSRFAlgorithm.PRIORITY_MID)
        self._assert_interval(8, interval)
    
    def test__calculate_interval_consecutive_rep(self):
        interval = self._algorithm._calculate_interval(5, 2.3, 0, SSRFAlgorithm.PRIORITY_HIGH)
        self._assert_interval(1, interval)
        interval = self._algorithm._calculate_interval(5, 2.3, 2, SSRFAlgorithm.PRIORITY_HIGH)
        self._assert_interval(2, interval)
        interval = self._algorithm._calculate_interval(5, 2.3, 3, SSRFAlgorithm.PRIORITY_HIGH)
        self._assert_interval(3, interval)
        interval = self._algorithm._calculate_interval(5, 2.3, 5, SSRFAlgorithm.PRIORITY_HIGH)
        self._assert_interval(18, interval)
    
    def test__calculate_interval_wrong_num_reviews(self):
        assert_raises(AssertionError, self._algorithm._calculate_interval, 0, 0.0, 0, SSRFAlgorithm.PRIORITY_MID)
    
    def test__calculate_interval_wrong_prev_avg_grade(self):
        assert_raises(AssertionError, self._algorithm._calculate_interval, 1, -0.01, 0, SSRFAlgorithm.PRIORITY_MID)
        self._algorithm._calculate_interval(1, 0.0, 0, SSRFAlgorithm.PRIORITY_MID)
        
        self._algorithm._calculate_interval(1, 5.0, 0, SSRFAlgorithm.PRIORITY_MID)
        assert_raises(AssertionError, self._algorithm._calculate_interval, 1, 5.01, 0, SSRFAlgorithm.PRIORITY_MID)
        
    def test__calculate_interval_wrong_grade(self):
        assert_raises(AssertionError, self._algorithm._calculate_interval, 1, 0.0, -2, SSRFAlgorithm.PRIORITY_MID)
        self._algorithm._calculate_interval(1, 0.0, -1, SSRFAlgorithm.PRIORITY_MID)
    
        self._algorithm._calculate_interval(1, 0.0, 5, SSRFAlgorithm.PRIORITY_MID)
        assert_raises(AssertionError, self._algorithm._calculate_interval, 1, 0.0, 6, SSRFAlgorithm.PRIORITY_MID)
    
    def test__calculate_interval_wrong_priority(self):
        assert_raises(AssertionError, self._algorithm._calculate_interval, 1, 0.0, 0, 1.0)
        self._algorithm._calculate_interval(1, 0.0, 5, SSRFAlgorithm.PRIORITY_LOW)
        
        self._algorithm._calculate_interval(1, 0.0, 5, SSRFAlgorithm.PRIORITY_HIGH)
        assert_raises(AssertionError, self._algorithm._calculate_interval, 1, 0.0, 0, 5.0)

    def test__find_last_zero_workload_ind_wrong_workloads(self):
        assert_raises(AssertionError, self._algorithm._find_last_zero_workload_ind, [0, -1])
    
    def test__find_max_load_reduction_ind_wrong_intervals(self):
        assert_raises(AssertionError, self._algorithm._find_max_load_reduction_ind, 
                          self._create_lu_data(), [0, 1], [0, 0], [0.0, 0.0])
        
    def test__find_max_load_reduction_ind_wrong_workloads(self):
        assert_raises(AssertionError, self._algorithm._find_max_load_reduction_ind, 
                          self._create_lu_data(), [1, 2], [-1, 0], [0.0, 0.0])
        
    def test__find_max_load_reduction_ind_wrong_avg_difficulties(self):
        assert_raises(AssertionError, self._algorithm._find_max_load_reduction_ind, 
                          self._create_lu_data(), [1, 2], [0, 0], [-0.01, 0.0])
        
    def test__calculate_load_coeffs(self):
        load_coeffs = self._algorithm._calculate_load_coeffs([63, 40, 33, 20, 18, 50], [6.0, 2.2, 1.5, 1.6, 3.5, 5.1])
        self._assert_load_coeffs([0.536, 0.202, 0.103, 0.007, 0.163, 0.454], load_coeffs)
    
    def test__calculate_load_coeffs_0_workload(self):
        # zero workload on some day
        load_coeffs = self._algorithm._calculate_load_coeffs([0, 1], [0.0, 2.08])
        self._assert_load_coeffs([0.0, 1.0], load_coeffs)

    def test__calculate_load_coeffs_min_workload_avg_difficulty_on_same_interval(self):
        # min. workload and min. avg difficulty on the same date
        load_coeffs = self._algorithm._calculate_load_coeffs([5, 3, 2], [0.3, 2.5, 0.1])
        self._assert_load_coeffs([0.402, 0.516, 0.0], load_coeffs)

    def test__calculate_load_coeffs_wrong_workloads(self):
        assert_raises(AssertionError, self._algorithm._calculate_load_coeffs, [0, -1], [0.0, 0.0])
        self._algorithm._calculate_load_coeffs([0, 0], [0.0, 0.0])
        
    def test__calculate_load_coeffs_wrong_avg_difficulties(self):
        assert_raises(AssertionError, self._algorithm._calculate_load_coeffs, [0, 0], [0.0, -0.01])
        self._algorithm._calculate_load_coeffs([0, 0], [0.0, 0.0])
        
    def test__calculate_load_coeffs_workload_avg_difficulties_len_mismatch(self):
        assert_raises(AssertionError, self._algorithm._calculate_load_coeffs, [0, 0], [0.0])
        assert_raises(AssertionError, self._algorithm._calculate_load_coeffs, [0], [0.0, 0.0])
        self._algorithm._calculate_load_coeffs([0, 0], [0.0, 0.0])
        
    def test__calculate_difficulty(self):
        difficulty = self._algorithm._calculate_difficulty(1, SSRFAlgorithm.PRIORITY_MID, 1)
        self._assert_difficulty(1.50, difficulty)
        difficulty = self._algorithm._calculate_difficulty(1, SSRFAlgorithm.PRIORITY_MID, 2)
        self._assert_difficulty(1.10, difficulty)
        difficulty = self._algorithm._calculate_difficulty(1, SSRFAlgorithm.PRIORITY_MID, 7)
        self._assert_difficulty(0.12, difficulty)
        difficulty = self._algorithm._calculate_difficulty(1, SSRFAlgorithm.PRIORITY_MID, 8)
        self._assert_difficulty(0.0, difficulty)

    def test_schedule_first_rep_0_grade(self):
        date_from = date.today() + timedelta(1)
        date_to = date.today() + timedelta(1)
        self._global_data.get_workloads(date_from, date_to).AndReturn([0])
        mox.Replay(self._global_data)
        
        lu_data = self._create_lu_data(grade=0)
        self._algorithm.schedule(lu_data)

        mox.Verify(self._global_data)
        assert_equals(date.today() + timedelta(1), lu_data.next_review.date())
        self._assert_new_lu_data(2, 1.25, 1.50, SSRFAlgorithmLUData.LUStatus.FINAL_DRILL,
                                 lu_data)
        
    def test_schedule_first_rep_2_grade(self):
        date_from = date.today() + timedelta(1)
        date_to = date.today() + timedelta(1)
        self._global_data.get_workloads(date_from, date_to).AndReturn([5])
        self._global_data.get_avg_difficulties(date_from, date_to).AndReturn([0.88])
        mox.Replay(self._global_data)

        lu_data = self._create_lu_data(grade=2)
        self._algorithm.schedule(lu_data)

        mox.Verify(self._global_data)
        assert_equals(date.today() + timedelta(1), lu_data.next_review.date())
        self._assert_new_lu_data(2, 2.25, 1.50, SSRFAlgorithmLUData.LUStatus.FINAL_DRILL,
                                 lu_data)
        
    def test_schedule_first_rep_3_grade(self):
        date_from = date.today() + timedelta(1)
        date_to = date.today() + timedelta(2)
        self._global_data.get_workloads(date_from, date_to).AndReturn([0, 1])
        mox.Replay(self._global_data)

        lu_data = self._create_lu_data(grade=3)
        self._algorithm.schedule(lu_data)

        mox.Verify(self._global_data)
        assert_equals(date.today() + timedelta(1), lu_data.next_review.date())
        self._assert_new_lu_data(2, 2.75, 1.50, SSRFAlgorithmLUData.LUStatus.MEMORIZED,
                                 lu_data)

    def test_schedule_first_rep_5_grade(self):
        date_from = date.today() + timedelta(4)
        date_to = date.today() + timedelta(8)
        self._global_data.get_workloads(date_from, date_to).AndReturn([5, 3, 2, 4, 8])
        self._global_data.get_avg_difficulties(date_from, date_to).AndReturn([2.5, 0.3, 0.1, 1.1, 0.8])
        mox.Replay(self._global_data)

        lu_data = self._create_lu_data(grade=5)
        self._algorithm.schedule(lu_data)
        
        mox.Verify(self._global_data)
        assert_equals(date.today() + timedelta(5), lu_data.next_review.date())
        self._assert_new_lu_data(2, 3.75, 0.41, SSRFAlgorithmLUData.LUStatus.MEMORIZED,
                                 lu_data)
        
    def test_schedule_consecutive_rep_0_grade(self):
        date_from = date.today() + timedelta(1)
        date_to = date.today() + timedelta(2)
        self._global_data.get_workloads(date_from, date_to).AndReturn([1, 0])
        mox.Replay(self._global_data)

        lu_data = self._create_lu_data(grade=0, num_reviews=3, avg_grade=3.7, 
                                       priority=SSRFAlgorithm.PRIORITY_LOW,
                                       difficulty=2.26)
        self._algorithm.schedule(lu_data)
        
        mox.Verify(self._global_data)
        assert_equals(date.today() + timedelta(2), lu_data.next_review.date())
        self._assert_new_lu_data(4, 2.78, 4.65, SSRFAlgorithmLUData.LUStatus.FINAL_DRILL, 
                                 lu_data)

    def test_schedule_consecutive_rep_2_grade(self):
        date_from = date.today() + timedelta(4)
        date_to = date.today() + timedelta(9)
        self._global_data.get_workloads(date_from, date_to).AndReturn([63, 40, 33, 20, 18, 50])
        self._global_data.get_avg_difficulties(date_from, date_to).AndReturn([6.0, 2.2, 1.5, 1.6, 3.5, 5.1])
        mox.Replay(self._global_data)

        lu_data = self._create_lu_data(grade=2, num_reviews=3, avg_grade=3.7, 
                                       priority=SSRFAlgorithm.PRIORITY_LOW,
                                       difficulty=1.70)
        self._algorithm.schedule(lu_data)

        mox.Verify(self._global_data)
        assert_equals(date.today() + timedelta(8), lu_data.next_review.date())
        self._assert_new_lu_data(4, 3.28, 3.56, SSRFAlgorithmLUData.LUStatus.FINAL_DRILL, 
                                 lu_data)

    def test_schedule_consecutive_rep_3_grade(self):
        date_from = date.today() + timedelta(9)
        date_to = date.today() + timedelta(22)
        num_days = (date_to - date_from).days + 1
        workloads = range(10, 10 + num_days)
        assert_equals(num_days, len(workloads))
        self._global_data.get_workloads(date_from, date_to).AndReturn(workloads)
        avg_difficulties = [d / 2.0 for d in range(num_days / 2, 0, -1)] + \
            [d / 2.0 for d in range(num_days / 2, num_days)]
        assert_equals(num_days, len(avg_difficulties))
        self._global_data.get_avg_difficulties(date_from, date_to).AndReturn(avg_difficulties)
        mox.Replay(self._global_data)

        lu_data = self._create_lu_data(grade=3, num_reviews=3, avg_grade=3.7, 
                                       priority=SSRFAlgorithm.PRIORITY_LOW,
                                       difficulty=3.36)
        self._algorithm.schedule(lu_data)
        
        mox.Verify(self._global_data)
        assert_equals(date.today() + timedelta(14), lu_data.next_review.date())
        self._assert_new_lu_data(4, 3.53, 3.04, SSRFAlgorithmLUData.LUStatus.MEMORIZED,
                                 lu_data)
    
    def test_schedule_consecutive_rep_5_grade(self):
        date_from = date.today() + timedelta(57)
        date_to = date.today() + timedelta(154)
        num_days = (date_to - date_from).days + 1
        workloads = range(num_days, 0, -1)
        assert_equals(num_days, len(workloads))
        self._global_data.get_workloads(date_from, date_to).AndReturn(workloads)
        avg_difficulties = [float(d) / num_days for d in range(1, num_days + 1)]
        assert_equals(num_days, len(avg_difficulties))
        self._global_data.get_avg_difficulties(date_from, date_to).AndReturn(avg_difficulties)
        mox.Replay(self._global_data)

        lu_data = self._create_lu_data(grade=5, num_reviews=3, avg_grade=3.7, 
                                       priority=SSRFAlgorithm.PRIORITY_LOW,
                                       difficulty=0.41)
        self._algorithm.schedule(lu_data)
        
        mox.Verify(self._global_data)
        assert_equals(date.today() + timedelta(59), lu_data.next_review.date())
        self._assert_new_lu_data(4, 4.03, 1.66, SSRFAlgorithmLUData.LUStatus.MEMORIZED,
                                 lu_data)
    
    def test_schedule_consecutive_rep_final_drill_0_grade(self):
        lu_data = self._create_lu_data(grade=0, num_reviews=2, avg_grade=2.7, 
                                       priority=SSRFAlgorithm.PRIORITY_HIGH,
                                       difficulty=0.8, 
                                       status=SSRFAlgorithmLUData.LUStatus.FINAL_DRILL)
        self._algorithm.schedule(lu_data)
        
        self._assert_new_lu_data(2, 2.7, 0.8, SSRFAlgorithmLUData.LUStatus.FINAL_DRILL,
                                 lu_data)
    
    def test_schedule_consecutive_rep_final_drill_2_grade(self):
        lu_data = self._create_lu_data(grade=2, num_reviews=2, avg_grade=2.7, 
                                       priority=SSRFAlgorithm.PRIORITY_HIGH,
                                       difficulty=0.8, 
                                       status=SSRFAlgorithmLUData.LUStatus.FINAL_DRILL)
        self._algorithm.schedule(lu_data)
        
        self._assert_new_lu_data(2, 2.7, 0.8, SSRFAlgorithmLUData.LUStatus.FINAL_DRILL,
                                 lu_data)

    def test_schedule_consecutive_rep_final_drill_3_grade(self):
        lu_data = self._create_lu_data(grade=3, num_reviews=2, avg_grade=2.7, 
                                       priority=SSRFAlgorithm.PRIORITY_HIGH,
                                       difficulty=0.8, 
                                       status=SSRFAlgorithmLUData.LUStatus.FINAL_DRILL)
        self._algorithm.schedule(lu_data)
        
        self._assert_new_lu_data(2, 2.7, 0.8, SSRFAlgorithmLUData.LUStatus.MEMORIZED,
                                 lu_data)

    def test_schedule_consecutive_rep_final_drill_5_grade(self):
        lu_data = self._create_lu_data(grade=5, num_reviews=2, avg_grade=2.7, 
                                       priority=SSRFAlgorithm.PRIORITY_HIGH,
                                       difficulty=0.8, 
                                       status=SSRFAlgorithmLUData.LUStatus.FINAL_DRILL)
        self._algorithm.schedule(lu_data)
        
        self._assert_new_lu_data(2, 2.7, 0.8, SSRFAlgorithmLUData.LUStatus.MEMORIZED,
                                 lu_data)

    def test_schedule_wrong_lu_data_grade(self):
        lu_data = self._create_lu_data(grade=-1)
        assert_raises(AssertionError, self._algorithm.schedule, lu_data)

        lu_data = self._create_lu_data(grade=6)
        assert_raises(AssertionError, self._algorithm.schedule, lu_data)
            
    def test_schedule_wrong_lu_data_num_of_reviews(self):
        lu_data = self._create_lu_data(num_reviews=0)
        assert_raises(AssertionError, self._algorithm.schedule, lu_data)
        
    def test_schedule_wrong_lu_data_avg_grade(self):
        lu_data = self._create_lu_data(avg_grade=-0.01)
        assert_raises(AssertionError, self._algorithm.schedule, lu_data)
        
        lu_data = self._create_lu_data(avg_grade=5.01)
        assert_raises(AssertionError, self._algorithm.schedule, lu_data)
        
    def test_schedule_wrong_lu_data_priority(self):
        lu_data = self._create_lu_data(priority=1.0)
        assert_raises(AssertionError, self._algorithm.schedule, lu_data)
        
        lu_data = self._create_lu_data(priority=5.0)
        assert_raises(AssertionError, self._algorithm.schedule, lu_data)

    def test_schedule_wrong_lu_data_difficulty(self):
        lu_data = self._create_lu_data(difficulty=-0.01)
        assert_raises(AssertionError, self._algorithm.schedule, lu_data)

    def test_schedule_wrong_global_data_workloads(self):
        date_from = date.today() + timedelta(3)
        date_to = date.today() + timedelta(7)
        self._global_data.get_workloads(date_from, date_to).AndReturn([0, 0, 0, 0])
        mox.Replay(self._global_data)

        lu_data = self._create_lu_data(grade=5)
        assert_raises(AssertionError, self._algorithm.schedule, lu_data)
        
        mox.Verify(self._global_data)        
    
    def test_schedule_wrong_global_data_avg_difficulties(self):
        date_from = date.today() + timedelta(4)
        date_to = date.today() + timedelta(8)
        self._global_data.get_workloads(date_from, date_to).AndReturn([1, 1, 1, 1, 1])
        self._global_data.get_avg_difficulties(date_from, date_to).AndReturn([0.0, 0.0, 0.0, 0.0])
        mox.Replay(self._global_data)

        lu_data = self._create_lu_data(grade=5)
        assert_raises(AssertionError, self._algorithm.schedule, lu_data)
        
        mox.Verify(self._global_data)

    def _assert_interval(self, exp_interval, interval):
        assert_almost_equals(exp_interval, interval, 2)
        
    def _assert_difficulty(self, exp_difficulty, difficulty):
        assert_almost_equals(exp_difficulty, difficulty, 2)
    
    def _assert_load_coeffs(self, exp_load_coeffs, load_coeffs):
        assert_equals(len(exp_load_coeffs), len(load_coeffs))
        for i in range(len(exp_load_coeffs)):
            assert_almost_equals(exp_load_coeffs[i], load_coeffs[i], 3, 
                                    "[%d]: %s != %s within %d places" % (i, exp_load_coeffs[i], load_coeffs[i], 3))
        
    def _assert_new_lu_data(self, exp_num_reviews, exp_avg_grade, exp_difficulty,
                            exp_status, lu_data):
        assert_equals(exp_num_reviews, lu_data.num_reviews)
        assert_almost_equals(exp_avg_grade, lu_data.avg_grade, 2)
        self._assert_difficulty(exp_difficulty, lu_data.difficulty)
        assert_equals(exp_status, lu_data.status)
