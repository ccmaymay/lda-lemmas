from math import log

import numpy as np
from numpy.testing import assert_allclose

from follow_up.evaluation import (
    compute_entropy,
    compute_pmf,
    compute_mi,
    compute_voi,
    compute_joint_topic_assignment_counts,
)


def test_entropy():
    assert_allclose(compute_entropy(np.array([1.])), 0)
    assert_allclose(compute_entropy(np.array([1., 0.])), 0)
    assert_allclose(compute_entropy(np.array([0., 1.])), 0)
    assert_allclose(compute_entropy(np.array([1., 0., 0.])), 0)
    assert_allclose(compute_entropy(np.array([0., 1., 0.])), 0)
    assert_allclose(compute_entropy(np.array([0., 0., 1.])), 0)
    assert_allclose(compute_entropy(np.array([0.4, 0.6])), -0.4*log(0.4) - 0.6*log(0.6))
    assert_allclose(compute_entropy(np.array([0., 0.4, 0.6])), -0.4*log(0.4) - 0.6*log(0.6))
    assert_allclose(compute_entropy(np.array([0.4, 0., 0.6])), -0.4*log(0.4) - 0.6*log(0.6))
    assert_allclose(compute_entropy(np.array([0.4, 0.6, 0.])), -0.4*log(0.4) - 0.6*log(0.6))
    assert_allclose(compute_entropy(np.array([0., 0.6, 0.4])), -0.4*log(0.4) - 0.6*log(0.6))
    assert_allclose(compute_entropy(np.array([0.6, 0., 0.4])), -0.4*log(0.4) - 0.6*log(0.6))
    assert_allclose(compute_entropy(np.array([0.6, 0.4, 0.])), -0.4*log(0.4) - 0.6*log(0.6))


def test_pmf():
    assert_allclose(compute_pmf(np.array([0.2])), np.array([1.]))
    assert_allclose(compute_pmf(np.array([1.])), np.array([1.]))
    assert_allclose(compute_pmf(np.array([2.])), np.array([1.]))
    assert_allclose(compute_pmf(np.array([0., 0.2])), np.array([0., 1.]))
    assert_allclose(compute_pmf(np.array([0., 1.])), np.array([0., 1.]))
    assert_allclose(compute_pmf(np.array([0., 2.])), np.array([0., 1.]))
    assert_allclose(compute_pmf(np.array([0.2, 0.])), np.array([1., 0.]))
    assert_allclose(compute_pmf(np.array([1., 0.])), np.array([1., 0.]))
    assert_allclose(compute_pmf(np.array([2., 0.])), np.array([1., 0.]))
    assert_allclose(compute_pmf(np.array([1., 0., 0.])), np.array([1., 0., 0.]))
    assert_allclose(compute_pmf(np.array([0., 1., 0.])), np.array([0., 1., 0.]))
    assert_allclose(compute_pmf(np.array([0., 0., 1.])), np.array([0., 0., 1.]))
    assert_allclose(compute_pmf(np.array([0.2, 0.3])), np.array([0.4, 0.6]))
    assert_allclose(compute_pmf(np.array([0.4, 0.6])), np.array([0.4, 0.6]))
    assert_allclose(compute_pmf(np.array([4., 6.])), np.array([0.4, 0.6]))
    assert_allclose(compute_pmf(np.array([0.3, 0.2])), np.array([0.6, 0.4]))
    assert_allclose(compute_pmf(np.array([0.6, 0.4])), np.array([0.6, 0.4]))
    assert_allclose(compute_pmf(np.array([6., 4.])), np.array([0.6, 0.4]))


def test_mi():
    assert_allclose(compute_mi(0., 0., 0.), 0.)
    assert_allclose(compute_mi(1., 1., 2.), 0.)
    assert_allclose(compute_mi(2., 2., 2.), 2.)
    assert_allclose(compute_mi(2., 2., 3.), 1.)


def test_voi():
    assert_allclose(compute_voi(np.array([[1.]])), 0.)
    assert_allclose(compute_voi(np.array([[2.]])), 0.)
    assert_allclose(compute_voi(np.array([[1., 0.]])), 0.)
    assert_allclose(compute_voi(np.array([[0., 1.]])), 0.)
    assert_allclose(compute_voi(np.array([[1.], [0.]])), 0.)
    assert_allclose(compute_voi(np.array([[0.], [1.]])), 0.)
    assert_allclose(compute_voi(np.array([[2., 3.]])), -0.4*log(0.4) - 0.6*log(0.6))
    assert_allclose(compute_voi(np.array([[2.], [3.]])), -0.4*log(0.4) - 0.6*log(0.6))
    assert_allclose(compute_voi(np.array([[2., 3.], [0., 0.]])), -0.4*log(0.4) - 0.6*log(0.6))
    assert_allclose(compute_voi(np.array([[2., 0.], [3., 0.]])), -0.4*log(0.4) - 0.6*log(0.6))
    assert_allclose(compute_voi(np.array([[1., 0.], [0., 1.]])), 0.)
    assert_allclose(compute_voi(np.array([[1., 1.], [0., 0.]])), -2*0.5*log(0.5))
    assert_allclose(compute_voi(np.array([[1., 0.], [1., 0.]])), -2*0.5*log(0.5))
    assert_allclose(
        compute_voi(np.array([[2., 2.], [0., 1.]])),
        2*(-2*0.4*log(0.4) - 0.2*log(0.2)) - (
            -0.8*log(0.8) - 0.2*log(0.2) +
            -0.4*log(0.4) - 0.6*log(0.6)
        ))


def test_joint_topic_assignment_counts():
    assert_allclose(
        compute_joint_topic_assignment_counts(
            np.array([0]),
            np.array([0])),
        np.array([[1]]))
    assert_allclose(
        compute_joint_topic_assignment_counts(
            np.array([0, 0]),
            np.array([0, 0])),
        np.array([[2]]))
    assert_allclose(
        compute_joint_topic_assignment_counts(
            np.array([1, 0]),
            np.array([1, 0])),
        np.array([[1, 0], [0, 1]]))
    assert_allclose(
        compute_joint_topic_assignment_counts(
            np.array([0, 1]),
            np.array([0, 1])),
        np.array([[1, 0], [0, 1]]))
    assert_allclose(
        compute_joint_topic_assignment_counts(
            np.array([1, 0]),
            np.array([0, 1])),
        np.array([[0, 1], [1, 0]]))
    assert_allclose(
        compute_joint_topic_assignment_counts(
            np.array([0, 1]),
            np.array([1, 0])),
        np.array([[0, 1], [1, 0]]))
    assert_allclose(
        compute_joint_topic_assignment_counts(
            np.array([0, 1]),
            np.array([0, 0])),
        np.array([[1], [1]]))
    assert_allclose(
        compute_joint_topic_assignment_counts(
            np.array([0, 0]),
            np.array([0, 1])),
        np.array([[1, 1]]))
    assert_allclose(
        compute_joint_topic_assignment_counts(
            np.array([0, 1]),
            np.array([1, 1])),
        np.array([[0, 1], [0, 1]]))
    assert_allclose(
        compute_joint_topic_assignment_counts(
            np.array([1, 1]),
            np.array([0, 1])),
        np.array([[0, 0], [1, 1]]))
    assert_allclose(
        compute_joint_topic_assignment_counts(
            np.array([2, 1]),
            np.array([0, 1])),
        np.array([[0, 0], [0, 1], [1, 0]]))
