import unittest
import numpy as np

from kafe2.fit import HistContainer, HistFit, IndexedContainer, IndexedFit, XYContainer, XYFit, XYMultiContainer, XYMultiFit
from kafe2.core.constraint import GaussianMatrixParameterConstraint, GaussianSimpleParameterConstraint
from kafe2.fit.indexed.fit import IndexedFitException
from kafe2.fit.xy.fit import XYFitException
from kafe2.fit.xy_multi.fit import XYMultiFitException
from kafe2.fit.histogram.fit import HistFitException


class TestMatrixParameterConstraintDirect(unittest.TestCase):

    def setUp(self):
        self._fit_par_values = [0.1, 1.2, 2.3, 3.4, 4.5, 5.6, 6.7, 7.8, 8.9, 9.0]
        self._par_test_values = np.array([[8.9, 3.4, 5.6], [0.1, 2.3, 9.0], [5.6, 4.5, 3.4]])
        self._par_indices = [[8, 3, 5], [0, 2, 9], [5, 4, 3]]
        self._par_values = np.array([[1.23, 7.20, 3.95], [4.11, 3.00, 2.95], [0.1, -8.5, 67.0]])
        self._par_cov_mats_abs = np.array([
            [
                [1.0, 0.0, 0.0],
                [0.0, 2.8, 0.0],
                [0.0, 0.0, 0.5],
            ], [
                [1.0, 0.2, 0.3],
                [0.2, 2.8, 0.1],
                [0.3, 0.1, 0.5],
            ]
        ])
        self._par_cov_mats_rel = np.array([
            [
                [0.1, 0.0, 0.0],
                [0.0, 0.2, 0.0],
                [0.0, 0.0, 0.3],
            ], [
                [0.10, 0.01, 0.02],
                [0.01, 0.20, 0.03],
                [0.02, 0.03, 0.30],
            ]
        ])
        self._uncertainties_abs = np.array([[1.2, 2.3, 0.4], [6.5, 2.6, 1.0]])
        self._uncertainties_rel = np.array([[0.2, 0.3, 0.2], [0.5, 2.6, 1.0]])
        self._par_cor_mats = np.array([
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0]
            ], [
                [1.0, 0.1, 0.2],
                [0.1, 1.0, 0.3],
                [0.2, 0.3, 1.0]
            ]
        ])

        self._expected_cost_cov_abs = np.zeros((3, 3, 2))
        for _i in range(3):
            for _j in range(3):
                for _k in range(2):
                    _res = self._par_test_values[_i] - self._par_values[_j]
                    self._expected_cost_cov_abs[_i, _j, _k] = _res.dot(np.linalg.inv(self._par_cov_mats_abs[_k])).dot(_res)
        self._expected_cost_cov_rel = np.zeros((3, 3, 2))
        for _i in range(3):
            for _j in range(3):
                for _k in range(2):
                    _res = self._par_test_values[_i] - self._par_values[_j]
                    _abs_cov_mat = self._par_cov_mats_rel[_k] * np.outer(self._par_values[_j], self._par_values[_j])
                    self._expected_cost_cov_rel[_i, _j, _k] = _res.dot(np.linalg.inv(_abs_cov_mat)).dot(_res)
        self._expected_cost_cor_abs = np.zeros((3, 3, 2, 2))
        for _i in range(3):
            for _j in range(3):
                for _k in range(2):
                    for _l in range(2):
                        _res = self._par_test_values[_i] - self._par_values[_j]
                        _cov_mat = self._par_cor_mats[_k] * np.outer(self._uncertainties_abs[_l],
                                                                         self._uncertainties_abs[_l])
                        self._expected_cost_cor_abs[_i, _j, _k, _l] = _res.dot(np.linalg.inv(_cov_mat)).dot(_res)
        self._expected_cost_cor_rel = np.zeros((3, 3, 2, 2))
        for _i in range(3):
            for _j in range(3):
                for _k in range(2):
                    for _l in range(2):
                        _res = self._par_test_values[_i] - self._par_values[_j]
                        _uncertainties_abs = self._uncertainties_rel[_l] * self._par_values[_j]
                        _cov_mat = self._par_cor_mats[_k] * np.outer(_uncertainties_abs, _uncertainties_abs)
                        self._expected_cost_cor_rel[_i, _j, _k, _l] = _res.dot(np.linalg.inv(_cov_mat)).dot(_res)

    def _call_all_properties(self, matrix_constraint):
        matrix_constraint.indices
        matrix_constraint.values
        matrix_constraint.cov_mat
        matrix_constraint.cov_mat_rel
        matrix_constraint.cor_mat
        matrix_constraint.uncertainties
        matrix_constraint.uncertainties_rel
        matrix_constraint.matrix_type
        matrix_constraint.relative
        matrix_constraint.cov_mat_inverse

    def test_bad_input_errors(self):
        with self.assertRaises(ValueError):  # matrix not symmetric
            GaussianMatrixParameterConstraint(indices=[1, 0], values=[0.0, 1.0], matrix=[[0.5, 0.1], [0.0, 0.6]])
        with self.assertRaises(ValueError):  # values wrong dim
            GaussianMatrixParameterConstraint(indices=[1, 0], values=[[0.0, 1.0]], matrix=[[0.5, 0.0], [0.0, 0.6]])
        with self.assertRaises(ValueError):  # values wrong length
            GaussianMatrixParameterConstraint(indices=[1, 0], values=[0.0, 1.0, 5.0], matrix=[[0.5, 0.0], [0.0, 0.6]])
        with self.assertRaises(ValueError):  # both uncertainties and cov mat
            GaussianMatrixParameterConstraint(indices=[1, 0], values=[0.0, 1.0], matrix=[[0.5, 0.0], [0.0, 0.6]],
                                              uncertainties=[0.5, 0.6])
        with self.assertRaises(ValueError):  # unknown matrix type
            GaussianMatrixParameterConstraint(indices=[1, 0], values=[0.0, 1.0], matrix=[[0.5, 0.0], [0.0, 0.6]],
                                              matrix_type='cost')
        with self.assertRaises(ValueError):  # cor_mat but no uncertainties
            GaussianMatrixParameterConstraint(indices=[1, 0], values=[0.0, 1.0], matrix=[[1.0, 0.0], [0.0, 1.0]],
                                              matrix_type='cor')
        with self.assertRaises(ValueError):  # cor mat diagonal elements != 1
            GaussianMatrixParameterConstraint(indices=[1, 0], values=[0.0, 1.0], matrix=[[1.1, 0.0], [0.0, 1.0]],
                                              matrix_type='cor')
        with self.assertRaises(ValueError):  # cor mat elements > 1
            GaussianMatrixParameterConstraint(indices=[1, 0], values=[0.0, 1.0], matrix=[[1.0, 2.0], [2.0, 1.0]],
                                              matrix_type='cor')
        with self.assertRaises(ValueError):  # cor mat elements < -1
            GaussianMatrixParameterConstraint(indices=[1, 0], values=[0.0, 1.0], matrix=[[1.0, -2.0], [-2.0, 1.0]],
                                              matrix_type='cor')

    def test_cost_matrix_cov_abs(self):
        for _i in range(3):
            for _j in range(3):
                for _k in range(2):
                    _constraint = GaussianMatrixParameterConstraint(
                        self._par_indices[_i], self._par_values[_j], self._par_cov_mats_abs[_k])
                    self.assertTrue(np.abs(
                        _constraint.cost(self._fit_par_values) - self._expected_cost_cov_abs[_i, _j, _k]) < 1e-12)
                    self._call_all_properties(_constraint)

    def test_cost_matrix_cov_rel(self):
        for _i in range(3):
            for _j in range(3):
                for _k in range(2):
                    _constraint = GaussianMatrixParameterConstraint(
                        self._par_indices[_i], self._par_values[_j], self._par_cov_mats_rel[_k],
                        relative=True
                    )
                    self.assertTrue(np.abs(
                        _constraint.cost(self._fit_par_values) - self._expected_cost_cov_rel[_i, _j, _k]) < 1e-12)
                    self._call_all_properties(_constraint)

    def test_cost_matrix_cor_abs(self):
        for _i in range(3):
            for _j in range(3):
                for _k in range(2):
                    for _l in range(2):
                        _constraint = GaussianMatrixParameterConstraint(
                            self._par_indices[_i], self._par_values[_j], self._par_cor_mats[_k],
                            matrix_type='cor', uncertainties=self._uncertainties_abs[_l]
                        )
                        self.assertTrue(np.abs(
                            _constraint.cost(self._fit_par_values)
                            - self._expected_cost_cor_abs[_i, _j, _k, _l]) < 1e-12)
                        self._call_all_properties(_constraint)

    def test_cost_matrix_cor_rel(self):
        for _i in range(3):
            for _j in range(3):
                for _k in range(2):
                    for _l in range(2):
                        _constraint = GaussianMatrixParameterConstraint(
                            self._par_indices[_i], self._par_values[_j], self._par_cor_mats[_k],
                            matrix_type='cor', uncertainties=self._uncertainties_rel[_l], relative=True
                        )
                        self.assertTrue(np.abs(
                            _constraint.cost(self._fit_par_values)
                            - self._expected_cost_cor_rel[_i, _j, _k, _l]) < 1e-12)
                        self._call_all_properties(_constraint)


class TestSimpleParameterConstraintDirect(unittest.TestCase):

    def setUp(self):
        self._fit_par_values = [0.1, 1.2, 2.3, 3.4, 4.5, 5.6, 6.7, 7.8, 8.9, 9.0]
        self._par_test_values = [8.9, 3.4, 5.6]
        self._par_indices = [8, 3, 5]
        self._par_values = [1.23, 7.20, 3.95]
        self._par_uncertainties_abs = [1.0, 2.8, 0.001]
        self._par_uncertainties_rel = [0.1, 0.3, 0.01]
        self._expected_cost_abs = np.zeros((3, 3, 3))
        for _i in range(3):
            for _j in range(3):
                for _k in range(3):
                    _res = self._par_test_values[_i] - self._par_values[_j]
                    self._expected_cost_abs[_i, _j, _k] = (_res / self._par_uncertainties_abs[_k]) ** 2
        self._expected_cost_rel = np.zeros((3, 3, 3))
        for _i in range(3):
            for _j in range(3):
                for _k in range(3):
                    _res = self._par_test_values[_i] - self._par_values[_j]
                    self._expected_cost_rel[_i, _j, _k] = (_res / (self._par_uncertainties_rel[_k]
                                                                   * self._par_values[_j])) ** 2

    def test_cost_simple_abs(self):
        for _i in range(3):
            for _j in range(3):
                for _k in range(3):
                    _constraint = GaussianSimpleParameterConstraint(
                        self._par_indices[_i], self._par_values[_j], self._par_uncertainties_abs[_k])
                    self.assertTrue(np.allclose(
                        _constraint.cost(self._fit_par_values), self._expected_cost_abs[_i, _j, _k]))

                    # ensure that results are consistent with matrix constraints
                    _constraint = GaussianMatrixParameterConstraint(
                        [self._par_indices[_i]], [self._par_values[_j]], [[self._par_uncertainties_abs[_k] ** 2]]
                    )
                    self.assertTrue(np.allclose(
                        _constraint.cost(self._fit_par_values), self._expected_cost_abs[_i, _j, _k]))
                    _constraint = GaussianMatrixParameterConstraint(
                        [self._par_indices[_i]], [self._par_values[_j]], [[1.0]],
                        matrix_type='cor', uncertainties=[self._par_uncertainties_abs[_k]]
                    )
                    self.assertTrue(np.allclose(
                        _constraint.cost(self._fit_par_values), self._expected_cost_abs[_i, _j, _k]))

    def test_cost_simple_rel(self):
        for _i in range(3):
            for _j in range(3):
                for _k in range(3):
                    _constraint = GaussianSimpleParameterConstraint(
                        self._par_indices[_i], self._par_values[_j], self._par_uncertainties_rel[_k],
                        relative=True
                    )
                    self.assertTrue(np.allclose(
                        _constraint.cost(self._fit_par_values), self._expected_cost_rel[_i, _j, _k]))

                    # ensure that results are consistent with matrix constraints
                    _constraint = GaussianMatrixParameterConstraint(
                        [self._par_indices[_i]], [self._par_values[_j]], [[self._par_uncertainties_rel[_k] ** 2]],
                        relative=True
                    )
                    self.assertTrue(np.allclose(
                        _constraint.cost(self._fit_par_values), self._expected_cost_rel[_i, _j, _k]))
                    _constraint = GaussianMatrixParameterConstraint(
                        [self._par_indices[_i]], [self._par_values[_j]], [[1.0]],
                        matrix_type='cor', uncertainties=[self._par_uncertainties_rel[_k]], relative=True
                    )
                    self.assertTrue(np.allclose(
                        _constraint.cost(self._fit_par_values), self._expected_cost_rel[_i, _j, _k]))


class TestParameterConstraintInHistFit(unittest.TestCase):

    @staticmethod
    def _model_function(x, a, b):
        return a * x + b

    @staticmethod
    def _model_function_antiderivative(x, a, b):
        return 0.5 * a * x ** 2 + b * x

    def _expected_profile_diff(self, res, cov_mat_inv):
        return res.dot(cov_mat_inv).dot(res)

    def _test_consistency(self, constrained_fit, par_cov_mat_inv):
        constrained_fit.do_fit()
        _cost_function = constrained_fit._fitter._fcn_wrapper
        for _i in range(4):
            for _j in range(9):
                _a = self._test_par_values[_i, 0, _j]
                _b = self._test_par_values[_i, 1, _j]
                _profile_constrained = _cost_function(self._test_par_values[_i, 0, _j], self._test_par_values[_i, 1, _j])
                _diff = _profile_constrained - self._profile_no_constraints[_i, _j]
                _expected_profile_diff = self._expected_profile_diff(self._test_par_res[_i, _j], par_cov_mat_inv)
                self.assertTrue(np.abs(_diff - _expected_profile_diff) < 1e-12)

    def setUp(self):
        _bin_edges = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        _data = [
            0.5,
            1.5, 1.5,
            2.5, 2.5, 2.5,
            3.5, 3.5, 3.5, 3.5,
            4.5, 4.5, 4.5, 4.5, 4.5
        ]
        self._means = np.array([3.654, 7.789])
        self._vars = np.array([2.467, 1.543])
        self._cov_mat_uncor = np.array([[self._vars[0], 0.0], [0.0, self._vars[1]]])
        self._cov_mat_uncor_inv = np.linalg.inv(self._cov_mat_uncor)
        self._cov_mat_cor = np.array([[self._vars[0], 0.1], [0.1, self._vars[1]]])
        self._cov_mat_cor_inv = np.linalg.inv(self._cov_mat_cor)
        self._cov_mat_simple_a_inv = np.array([[1.0 / self._vars[0], 0.0], [0.0, 0.0]])
        self._cov_mat_simple_b_inv = np.array([[0.0, 0.0], [0.0, 1.0 / self._vars[1]]])

        self._data_container = HistContainer(n_bins=5, bin_range=(0.0, 5.0), fill_data=_data, dtype=float)
        self._data_container.add_simple_error(err_val=1.0)

        _a_test = np.linspace(start=1, stop=2, num=9, endpoint=True)
        _b_test = np.linspace(start=2, stop=3, num=9, endpoint=True)
        self._test_par_values = np.zeros((4, 2, 9))
        self._test_par_values[0, 0] = _a_test
        self._test_par_values[1, 1] = _b_test
        self._test_par_values[2, 0] = _a_test
        self._test_par_values[2, 1] = _b_test
        self._test_par_values[3, 0] = _a_test
        self._test_par_values[3, 1] = _b_test[::-1]  # reverse order
        self._test_par_res = self._test_par_values - self._means.reshape((1, 2, 1))
        self._test_par_res = np.transpose(self._test_par_res, axes=(0, 2, 1))

        self._fit_no_constraints = HistFit(self._data_container, model_density_function=self._model_function,
                                           model_density_antiderivative=self._model_function_antiderivative)
        self._fit_no_constraints.do_fit()
        _cost_function = self._fit_no_constraints._fitter._fcn_wrapper
        self._profile_no_constraints = np.zeros((4, 9))
        for _i in range(4):
            for _j in range(9):
                self._profile_no_constraints[_i, _j] = _cost_function(
                    self._test_par_values[_i, 0, _j],
                    self._test_par_values[_i, 1, _j])

    def test_bad_input_exception(self):
        _fit_with_constraint = HistFit(self._data_container, model_density_function=self._model_function,
                                       model_density_antiderivative=self._model_function_antiderivative)
        with self.assertRaises(HistFitException):
            _fit_with_constraint.add_parameter_constraint('c', 1.0, 1.0)
        with self.assertRaises(HistFitException):
            _fit_with_constraint.add_matrix_parameter_constraint(['a', 'c'], [1.0, 2.0], [[0.2, 0.0], [0.0, 0.1]])
        with self.assertRaises(HistFitException):
            _fit_with_constraint.add_matrix_parameter_constraint(['a'], [1.0, 2.0], [[0.2, 0.0], [0.0, 0.1]])

    def test_fit_profile_cov_mat_uncorrelated(self):
        _fit_with_constraint = HistFit(self._data_container, model_density_function=self._model_function,
                                       model_density_antiderivative=self._model_function_antiderivative)
        _fit_with_constraint.add_matrix_parameter_constraint(['a', 'b'], self._means, self._cov_mat_uncor)
        self._test_consistency(_fit_with_constraint, self._cov_mat_uncor_inv)
        _fit_with_constraint_alt = HistFit(self._data_container, model_density_function=self._model_function,
                                           model_density_antiderivative=self._model_function_antiderivative)
        _fit_with_constraint_alt.add_parameter_constraint('a', self._means[0], np.sqrt(self._vars[0]))
        _fit_with_constraint_alt.add_parameter_constraint('b', self._means[1], np.sqrt(self._vars[1]))
        self._test_consistency(_fit_with_constraint_alt, self._cov_mat_uncor_inv)

    def test_fit_profile_cov_mat_correlated(self):
        _fit_with_constraint = HistFit(self._data_container, model_density_function=self._model_function,
                                       model_density_antiderivative=self._model_function_antiderivative)
        _fit_with_constraint.add_matrix_parameter_constraint(['a', 'b'], self._means, self._cov_mat_cor)
        self._test_consistency(_fit_with_constraint, self._cov_mat_cor_inv)

    def test_fit_profile_simple_a(self):
        _fit_with_constraint = HistFit(self._data_container, model_density_function=self._model_function,
                                       model_density_antiderivative=self._model_function_antiderivative)
        _fit_with_constraint.add_parameter_constraint('a', self._means[0], np.sqrt(self._vars[0]))
        self._test_consistency(_fit_with_constraint, self._cov_mat_simple_a_inv)

    def test_fit_profile_simple_b(self):
        _fit_with_constraint = HistFit(self._data_container, model_density_function=self._model_function,
                                       model_density_antiderivative=self._model_function_antiderivative)
        _fit_with_constraint.add_parameter_constraint('b', self._means[1], np.sqrt(self._vars[1]))
        self._test_consistency(_fit_with_constraint, self._cov_mat_simple_b_inv)


class TestParameterConstraintInIndexedFit(unittest.TestCase):

    def _expected_profile_diff(self, res, cov_mat_inv):
        return res.dot(cov_mat_inv).dot(res)

    def _test_consistency(self, constrained_fit, par_cov_mat_inv):
        constrained_fit.do_fit()
        _cost_function = constrained_fit._fitter._fcn_wrapper
        for _i in range(4):
            for _j in range(9):
                _profile_constrained = _cost_function(self._test_par_values[_i, 0, _j], self._test_par_values[_i, 1, _j])
                _diff = _profile_constrained - self._profile_no_constraints[_i, _j]
                _expected_profile_diff = self._expected_profile_diff(self._test_par_res[_i, _j], par_cov_mat_inv)
                self.assertTrue(np.abs(_diff - _expected_profile_diff) < 1e-12)

    @staticmethod
    def _model(a, b):
        return a * np.arange(5) + b

    def setUp(self):
        _data = [-2.1, 0.2, 1.9, 3.8, 6.1]
        self._means = np.array([3.654, 7.789])
        self._vars = np.array([2.467, 1.543])
        self._cov_mat_uncor = np.array([[self._vars[0], 0.0], [0.0, self._vars[1]]])
        self._cov_mat_uncor_inv = np.linalg.inv(self._cov_mat_uncor)
        self._cov_mat_cor = np.array([[self._vars[0], 0.1], [0.1, self._vars[1]]])
        self._cov_mat_cor_inv = np.linalg.inv(self._cov_mat_cor)
        self._cov_mat_simple_a_inv = np.array([[1.0 / self._vars[0], 0.0], [0.0, 0.0]])
        self._cov_mat_simple_b_inv = np.array([[0.0, 0.0], [0.0, 1.0 / self._vars[1]]])

        self._data_container = IndexedContainer(data=_data)
        self._data_container.add_simple_error(err_val=1.0)

        _a_test = np.linspace(start=0,  stop=4, num=9, endpoint=True)
        _b_test = np.linspace(start=-4, stop=0, num=9, endpoint=True)
        self._test_par_values = np.zeros((4, 2, 9))
        self._test_par_values[0, 0] = _a_test
        self._test_par_values[1, 1] = _b_test
        self._test_par_values[2, 0] = _a_test
        self._test_par_values[2, 1] = _b_test
        self._test_par_values[3, 0] = _a_test
        self._test_par_values[3, 1] = -_b_test
        self._test_par_res = self._test_par_values - self._means.reshape((1, 2, 1))
        self._test_par_res = np.transpose(self._test_par_res, axes=(0, 2, 1))

        self._fit_no_constraints = IndexedFit(self._data_container, model_function=self._model)
        self._fit_no_constraints.do_fit()
        _cost_function = self._fit_no_constraints._fitter._fcn_wrapper
        self._profile_no_constraints = np.zeros((4, 9))
        for _i in range(4):
            for _j in range(9):
                self._profile_no_constraints[_i, _j] = _cost_function(
                    self._test_par_values[_i, 0, _j],
                    self._test_par_values[_i, 1, _j])

    def test_bad_input_exception(self):
        _fit_with_constraint = IndexedFit(self._data_container, model_function=self._model)
        with self.assertRaises(IndexedFitException):
            _fit_with_constraint.add_parameter_constraint('c', 1.0, 1.0)
        with self.assertRaises(IndexedFitException):
            _fit_with_constraint.add_matrix_parameter_constraint(['a', 'c'], [1.0, 2.0], [[0.2, 0.0], [0.0, 0.1]])
        with self.assertRaises(IndexedFitException):
            _fit_with_constraint.add_matrix_parameter_constraint(['a'], [1.0, 2.0], [[0.2, 0.0], [0.0, 0.1]])

    def test_fit_profile_cov_mat_uncorrelated(self):
        _fit_with_constraint = IndexedFit(self._data_container, model_function=self._model)
        _fit_with_constraint.add_matrix_parameter_constraint(['a', 'b'], self._means, self._cov_mat_uncor)
        self._test_consistency(_fit_with_constraint, self._cov_mat_uncor_inv)
        _fit_with_constraint_alt = IndexedFit(self._data_container, model_function=self._model)
        _fit_with_constraint_alt.add_parameter_constraint('a', self._means[0], np.sqrt(self._vars[0]))
        _fit_with_constraint_alt.add_parameter_constraint('b', self._means[1], np.sqrt(self._vars[1]))
        self._test_consistency(_fit_with_constraint_alt, self._cov_mat_uncor_inv)

    def test_fit_profile_cov_mat_correlated(self):
        _fit_with_constraint = IndexedFit(self._data_container, model_function=self._model)
        _fit_with_constraint.add_matrix_parameter_constraint(['a', 'b'], self._means, self._cov_mat_cor)
        self._test_consistency(_fit_with_constraint, self._cov_mat_cor_inv)

    def test_fit_profile_simple_a(self):
        _fit_with_constraint = IndexedFit(self._data_container, model_function=self._model)
        _fit_with_constraint.add_parameter_constraint('a', self._means[0], np.sqrt(self._vars[0]))
        self._test_consistency(_fit_with_constraint, self._cov_mat_simple_a_inv)

    def test_fit_profile_simple_b(self):
        _fit_with_constraint = IndexedFit(self._data_container, model_function=self._model)
        _fit_with_constraint.add_parameter_constraint('b', self._means[1], np.sqrt(self._vars[1]))
        self._test_consistency(_fit_with_constraint, self._cov_mat_simple_b_inv)


class TestParameterConstraintInXYFit(unittest.TestCase):

    def _expected_profile_diff(self, res, cov_mat_inv):
        return res.dot(cov_mat_inv).dot(res)

    def _test_consistency(self, constrained_fit, par_cov_mat_inv):
        constrained_fit.do_fit()
        _cost_function = constrained_fit._fitter._fcn_wrapper
        for _i in range(4):
            for _j in range(9):
                _profile_constrained = _cost_function(self._test_par_values[_i, 0, _j], self._test_par_values[_i, 1, _j])
                _diff = _profile_constrained - self._profile_no_constraints[_i, _j]
                _expected_profile_diff = self._expected_profile_diff(self._test_par_res[_i, _j], par_cov_mat_inv)
                self.assertTrue(np.abs(_diff - _expected_profile_diff) < 1e-12)

    def setUp(self):
        _x = [ 0.0, 1.0, 2.0, 3.0, 4.0]
        _y = [-2.1, 0.2, 1.9, 3.8, 6.1]
        self._means = np.array([3.654, 7.789])
        self._vars = np.array([2.467, 1.543])
        self._cov_mat_uncor = np.array([[self._vars[0], 0.0], [0.0, self._vars[1]]])
        self._cov_mat_uncor_inv = np.linalg.inv(self._cov_mat_uncor)
        self._cov_mat_cor = np.array([[self._vars[0], 0.1], [0.1, self._vars[1]]])
        self._cov_mat_cor_inv = np.linalg.inv(self._cov_mat_cor)
        self._cov_mat_simple_a_inv = np.array([[1.0 / self._vars[0], 0.0], [0.0, 0.0]])
        self._cov_mat_simple_b_inv = np.array([[0.0, 0.0], [0.0, 1.0 / self._vars[1]]])

        self._data_container = XYContainer(x_data=_x, y_data=_y)
        self._data_container.add_simple_error(axis='y', err_val=1.0)

        _a_test = np.linspace(start=0,  stop=4, num=9, endpoint=True)
        _b_test = np.linspace(start=-4, stop=0, num=9, endpoint=True)
        self._test_par_values = np.zeros((4, 2, 9))
        self._test_par_values[0, 0] = _a_test
        self._test_par_values[1, 1] = _b_test
        self._test_par_values[2, 0] = _a_test
        self._test_par_values[2, 1] = _b_test
        self._test_par_values[3, 0] = _a_test
        self._test_par_values[3, 1] = -_b_test
        self._test_par_res = self._test_par_values - self._means.reshape((1, 2, 1))
        self._test_par_res = np.transpose(self._test_par_res, axes=(0, 2, 1))

        self._fit_no_constraints = XYFit(self._data_container)
        self._fit_no_constraints.do_fit()
        _cost_function = self._fit_no_constraints._fitter._fcn_wrapper
        self._profile_no_constraints = np.zeros((4, 9))
        for _i in range(4):
            for _j in range(9):
                self._profile_no_constraints[_i, _j] = _cost_function(
                    self._test_par_values[_i, 0, _j],
                    self._test_par_values[_i, 1, _j])

    def test_bad_input_exception(self):
        _fit_with_constraint = XYFit(self._data_container)
        with self.assertRaises(XYFitException):
            _fit_with_constraint.add_parameter_constraint('c', 1.0, 1.0)
        with self.assertRaises(XYFitException):
            _fit_with_constraint.add_matrix_parameter_constraint(['a', 'c'], [1.0, 2.0], [[0.2, 0.0], [0.0, 0.1]])
        with self.assertRaises(XYFitException):
            _fit_with_constraint.add_matrix_parameter_constraint(['a'], [1.0, 2.0], [[0.2, 0.0], [0.0, 0.1]])

    def test_fit_profile_cov_mat_uncorrelated(self):
        _fit_with_constraint = XYFit(self._data_container)
        _fit_with_constraint.add_matrix_parameter_constraint(['a', 'b'], self._means, self._cov_mat_uncor)
        self._test_consistency(_fit_with_constraint, self._cov_mat_uncor_inv)
        _fit_with_constraint_alt = XYFit(self._data_container)
        _fit_with_constraint_alt.add_parameter_constraint('a', self._means[0], np.sqrt(self._vars[0]))
        _fit_with_constraint_alt.add_parameter_constraint('b', self._means[1], np.sqrt(self._vars[1]))
        self._test_consistency(_fit_with_constraint_alt, self._cov_mat_uncor_inv)

    def test_fit_profile_cov_mat_correlated(self):
        _fit_with_constraint = XYFit(self._data_container)
        _fit_with_constraint.add_matrix_parameter_constraint(['a', 'b'], self._means, self._cov_mat_cor)
        self._test_consistency(_fit_with_constraint, self._cov_mat_cor_inv)

    def test_fit_profile_simple_a(self):
        _fit_with_constraint = XYFit(self._data_container)
        _fit_with_constraint.add_parameter_constraint('a', self._means[0], np.sqrt(self._vars[0]))
        self._test_consistency(_fit_with_constraint, self._cov_mat_simple_a_inv)

    def test_fit_profile_simple_b(self):
        _fit_with_constraint = XYFit(self._data_container)
        _fit_with_constraint.add_parameter_constraint('b', self._means[1], np.sqrt(self._vars[1]))
        self._test_consistency(_fit_with_constraint, self._cov_mat_simple_b_inv)


class TestParameterConstraintInXYMultiFit(unittest.TestCase):

    def _expected_profile_diff(self, res, cov_mat_inv):
        return res.dot(cov_mat_inv).dot(res)

    def _test_consistency(self, constrained_fit, par_cov_mat_inv):
        constrained_fit.do_fit()
        _cost_function = constrained_fit._fitter._fcn_wrapper
        for _i in range(6):
            for _j in range(9):
                _profile_constrained = _cost_function(
                    self._test_par_values[_i, 0, _j],
                    self._test_par_values[_i, 1, _j],
                    self._test_par_values[_i, 2, _j])
                _diff = _profile_constrained - self._profile_no_constraints[_i, _j]
                _expected_profile_diff = self._expected_profile_diff(self._test_par_res[_i, _j], par_cov_mat_inv)
                self.assertTrue(np.abs(_diff - _expected_profile_diff) < 1e-9)

    @staticmethod
    def _model_function_0(x, a, b, c):
        return a * x ** 2 + b * x + c

    @staticmethod
    def _model_function_1(x, b, c):
        return b * x + c

    def setUp(self):
        _x_0 = [ 2.5,  4.0,  5.5,   7.0,   8.5]
        _y_0 = [-0.1, -2.1, -6.0, -12.8, -21.0]
        _x_1 = [ 0.0,  1.0,  2.0,   3.0,   4.0]
        _y_1 = [-2.1,  0.2,  1.9,   3.8,   6.1]
        self._means = np.array([-2.856, 3.654, 7.789])
        self._vars = np.array([3.935, 2.467, 1.543])
        self._cov_mat_uncor = np.array([
            [self._vars[0], 0.0, 0.0],
            [0.0, self._vars[1], 0.0],
            [0.0, 0.0, self._vars[2]]])
        self._cov_mat_uncor_inv = np.linalg.inv(self._cov_mat_uncor)
        self._cov_mat_cor = np.array([
            [self._vars[0], 0.1, 0.3],
            [0.1, self._vars[1], 0.1],
            [0.3, 0.1, self._vars[2]]])
        self._cov_mat_cor_inv = np.linalg.inv(self._cov_mat_cor)
        self._cov_mat_simple_a_inv = np.array([
            [1.0 / self._vars[0], 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0]])
        self._cov_mat_simple_b_inv = np.array([
            [0.0, 0.0, 0.0],
            [0.0, 1.0 / self._vars[1], 0.0],
            [0.0, 0.0, 0.0]])
        self._cov_mat_simple_c_inv = np.array([
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0 / self._vars[2]]])

        self._data_container = XYMultiContainer(xy_data=[[_x_0, _y_0], [_x_1, _y_1]])
        self._data_container.add_simple_error(axis='y', err_val=1.0)

        _a_test = np.linspace(start=-2,  stop=2, num=9, endpoint=True)
        _b_test = np.linspace(start=0,  stop=4, num=9, endpoint=True)
        _c_test = np.linspace(start=-4, stop=0, num=9, endpoint=True)
        self._test_par_values = np.zeros((6, 3, 9))
        self._test_par_values[0, 0] = _a_test
        self._test_par_values[1, 1] = _b_test
        self._test_par_values[2, 2] = _c_test

        self._test_par_values[3, 0] = _a_test
        self._test_par_values[3, 1] = _b_test
        self._test_par_values[3, 2] = -_c_test

        self._test_par_values[4, 0] = _a_test
        self._test_par_values[4, 1] = -_b_test
        self._test_par_values[4, 2] = _c_test

        self._test_par_values[5, 0] = -_a_test
        self._test_par_values[5, 1] = _b_test
        self._test_par_values[5, 2] = _c_test

        self._test_par_res = self._test_par_values - self._means.reshape((1, 3, 1))
        self._test_par_res = np.transpose(self._test_par_res, axes=(0, 2, 1))

        self._fit_no_constraints = XYMultiFit(self._data_container, [self._model_function_0, self._model_function_1])
        self._fit_no_constraints.do_fit()
        _cost_function = self._fit_no_constraints._fitter._fcn_wrapper
        self._profile_no_constraints = np.zeros((6, 9))
        for _i in range(6):
            for _j in range(9):
                self._profile_no_constraints[_i, _j] = _cost_function(
                    self._test_par_values[_i, 0, _j],
                    self._test_par_values[_i, 1, _j],
                    self._test_par_values[_i, 2, _j])

    def test_bad_input_exception(self):
        _fit_with_constraint = XYMultiFit(self._data_container, [self._model_function_0, self._model_function_1])
        with self.assertRaises(XYMultiFitException):
            _fit_with_constraint.add_parameter_constraint('d', 1.0, 1.0)
        with self.assertRaises(XYMultiFitException):
            _fit_with_constraint.add_matrix_parameter_constraint(['a', 'd'], [1.0, 2.0], [[0.2, 0.0], [0.0, 0.1]])
        with self.assertRaises(XYMultiFitException):
            _fit_with_constraint.add_matrix_parameter_constraint(['a'], [1.0, 2.0], [[0.2, 0.0], [0.0, 0.1]])

    def test_fit_profile_cov_mat_uncorrelated(self):
        _fit_with_constraint = XYMultiFit(self._data_container, [self._model_function_0, self._model_function_1])
        _fit_with_constraint.add_matrix_parameter_constraint(['a', 'b', 'c'], self._means, self._cov_mat_uncor)
        self._test_consistency(_fit_with_constraint, self._cov_mat_uncor_inv)
        _fit_with_constraint_alt = XYMultiFit(self._data_container, [self._model_function_0, self._model_function_1])
        _fit_with_constraint_alt.add_parameter_constraint('a', self._means[0], np.sqrt(self._vars[0]))
        _fit_with_constraint_alt.add_parameter_constraint('b', self._means[1], np.sqrt(self._vars[1]))
        _fit_with_constraint_alt.add_parameter_constraint('c', self._means[2], np.sqrt(self._vars[2]))
        self._test_consistency(_fit_with_constraint_alt, self._cov_mat_uncor_inv)

    def test_fit_profile_cov_mat_correlated(self):
        _fit_with_constraint = XYMultiFit(self._data_container, [self._model_function_0, self._model_function_1])
        _fit_with_constraint.add_matrix_parameter_constraint(['a', 'b', 'c'], self._means, self._cov_mat_cor)
        self._test_consistency(_fit_with_constraint, self._cov_mat_cor_inv)

    def test_fit_profile_simple_a(self):
        _fit_with_constraint = XYMultiFit(self._data_container, [self._model_function_0, self._model_function_1])
        _fit_with_constraint.add_parameter_constraint('a', self._means[0], np.sqrt(self._vars[0]))
        self._test_consistency(_fit_with_constraint, self._cov_mat_simple_a_inv)

    def test_fit_profile_simple_b(self):
        _fit_with_constraint = XYMultiFit(self._data_container, [self._model_function_0, self._model_function_1])
        _fit_with_constraint.add_parameter_constraint('b', self._means[1], np.sqrt(self._vars[1]))
        self._test_consistency(_fit_with_constraint, self._cov_mat_simple_b_inv)

    def test_fit_profile_simple_c(self):
        _fit_with_constraint = XYMultiFit(self._data_container, [self._model_function_0, self._model_function_1])
        _fit_with_constraint.add_parameter_constraint('c', self._means[2], np.sqrt(self._vars[2]))
        self._test_consistency(_fit_with_constraint, self._cov_mat_simple_c_inv)
