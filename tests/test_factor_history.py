import numpy as np
import pytest
from fragility_atlas.factor_history import read_factor_history_csv
from fragility_atlas.stress import replay_factor_history


def test_factor_history_reorders_columns_to_portfolio_order():
    data = "rates,equities\n0.01,-0.10\n-0.02,0.03\n"
    history = read_factor_history_csv(data, ("equities", "rates"))
    assert np.allclose(history, [[-0.10, 0.01], [0.03, -0.02]])
    assert replay_factor_history([100, -50], ("equities", "rates"), history) == pytest.approx([-10.5, 4])


@pytest.mark.parametrize("bad", [
    "equities,rates\n-0.1,0.01\n",
    "equities,rates\n-0.1,0.01\n0.1,nan\n",
    "equities,rates\n-0.1,0.01\n0.1\n",
    "equities,equities\n-0.1,0.01\n0.1,0.01\n",
    "equities,credit\n-0.1,0.01\n0.1,0.01\n",
])
def test_invalid_factor_history_rejected(bad):
    with pytest.raises(ValueError):
        read_factor_history_csv(bad, ("equities", "rates"))
