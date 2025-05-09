"""Test the QuantileRegression."""

from itertools import product

import numpy as np
import pytest
from sklearn.utils.estimator_checks import parametrize_with_checks

from sklego.linear_model import QuantileRegression
from sklego.testing import check_shape_remains_same_regressor

test_batch = [
    (np.array([0, 0, 3, 0, 6]), 3),
    (np.array([1, 0, -2, 0, 4, 0, -5, 0, 6]), 2),
    (np.array([4, -4]), 0),
]


def _create_dataset(coefs, intercept, noise=0.0):
    np.random.seed(0)
    size = 1_000
    X = np.random.randn(size, coefs.shape[0])
    y = X @ coefs + intercept + noise * np.random.randn(size)

    return X, y


@parametrize_with_checks(
    [
        QuantileRegression(**dict(zip(["quantile", "positive", "fit_intercept", "method"], args)))
        for args in product([0.5, 0.3], [True, False], [True, False], ["SLSQP", "TNC", "L-BFGS-B"])
    ]
)
def test_sklearn_compatible_estimator(estimator, check):
    if check.func.__name__ in {
        "check_sample_weights_invariance",
        "check_sample_weight_equivalence_on_dense_data",
        "check_sample_weights_invariance",
    }:
        pytest.skip()
    check(estimator)


@pytest.mark.parametrize("method", ["SLSQP", "TNC", "L-BFGS-B"])
@pytest.mark.parametrize("coefs, intercept", test_batch)
@pytest.mark.parametrize("noise, expected", [(0.0, 0.99), (1.0, 0.9)])
def test_coefs_and_intercept(method, coefs, intercept, noise, expected):
    """Regression problems with different level of noise."""
    X, y = _create_dataset(coefs, intercept, noise=noise)
    quant = QuantileRegression(method=method)
    quant.fit(X, y)
    assert quant.score(X, y) > expected


@pytest.mark.parametrize("method", ["SLSQP", "TNC", "L-BFGS-B"])
@pytest.mark.parametrize("coefs, intercept", test_batch)
@pytest.mark.parametrize("quantile", np.linspace(0, 1, 7))
def test_quantile(coefs, intercept, quantile, method):
    """Tests with noise on an easy problem. A good score should be possible."""
    X, y = _create_dataset(coefs, intercept, noise=1.0)
    quant = QuantileRegression(method=method, quantile=quantile)
    quant.fit(X, y)

    np.testing.assert_almost_equal((quant.predict(X) >= y).mean(), quantile, decimal=2)


@pytest.mark.parametrize("method", ["SLSQP", "TNC", "L-BFGS-B"])
@pytest.mark.parametrize("coefs, intercept", test_batch)
def test_coefs_and_intercept__no_noise_positive(coefs, intercept, method):
    """Test with only positive coefficients."""
    X, y = _create_dataset(coefs, intercept, noise=0.0)
    quant = QuantileRegression(method=method, positive=True)
    quant.fit(X, y)
    assert all(quant.coef_ >= 0)
    assert quant.score(X, y) > 0.3


@pytest.mark.parametrize("coefs, intercept", test_batch)
def test_coefs_and_intercept__no_noise_regularization(coefs, intercept):
    """Test model with regularization. The size of the coef vector should shrink the larger alpha gets."""
    X, y = _create_dataset(coefs, intercept)

    quants = [QuantileRegression(alpha=alpha, l1_ratio=0.0).fit(X, y) for alpha in range(3)]
    coef_size = np.array([np.sum(quant.coef_**2) for quant in quants])

    for i in range(2):
        assert coef_size[i] >= coef_size[i + 1]


@pytest.mark.parametrize("coefs, intercept", test_batch)
def test_fit_intercept_and_copy(coefs, intercept):
    """Test if fit_intercept and copy_X work."""
    X, y = _create_dataset(coefs, intercept, noise=2.0)
    imb = QuantileRegression(fit_intercept=False, copy_X=False)
    imb.fit(X, y)

    assert imb.intercept_ == 0.0


@pytest.mark.parametrize("test_fn", [check_shape_remains_same_regressor])
def test_quant(test_fn):
    regr = QuantileRegression()
    test_fn(QuantileRegression.__name__, regr)
