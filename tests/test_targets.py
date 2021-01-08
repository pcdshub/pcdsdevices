import pytest
from ophyd.sim import make_fake_device
from pcdsdevices.targets import XYGridStage
import numpy as np


@pytest.fixture(scope='function')
def sample_file(tmp_path):
    path = tmp_path / "sub"
    path.mkdir()
    sample_file = path / "samples.yml"
    sample_file.write_text('')
    return sample_file


@pytest.fixture(scope='function')
def fake_grid_stage(sample_file):
    FakeGridStage = make_fake_device(XYGridStage)
    grid = FakeGridStage(
        name='test', x_motor='X:MMN:PREFIX',
        y_motor='Y:MMN:PREFIX', m_points=10, n_points=10,
        path=sample_file)
    return grid


def test_samples_yaml_file(fake_grid_stage, sample_file):
    xy = fake_grid_stage
    xy.save_grid(sample_name='sample1', path=sample_file)
    # test sample1 in the file:
    res = xy.get_sample('sample1', path=sample_file)
    assert res['M'] == 10
    assert res["N"] == 10
    # test sample2 in the file
    xy.save_grid(sample_name='sample2', path=sample_file)
    res = xy.get_sample('sample2', path=sample_file)
    # test all mapped samples
    res = xy.mapped_samples(path=sample_file)
    assert res == ['sample1', 'sample2']


def test_mapping_points(fake_grid_stage):
    xx = np.linspace(0, 4, 5)
    yy = np.linspace(0, 4, 5)

    top_left, top_right = (0, 0), (4, 0)
    bottom_left, bottom_right = (0, 4), (4, 4)
    xx, yy = np.meshgrid(xx, yy)

    x, y = fake_grid_stage.map_points_second(top_left, top_right, bottom_right,
                                             bottom_left, 5, 5, False)
    # plt.scatter(x, y)
    # plt.show()

    expected_x_points = [0.0, 1.0, 2.0, 3.0, 4.0,
                         0.0, 1.0, 2.0, 3.0, 4.0,
                         0.0, 1.0, 2.0, 3.0, 4.0,
                         0.0, 1.0, 2.0, 3.0, 4.0,
                         0.0, 1.0, 2.0, 3.0, 4.0]

    expected_y_points = [0.0, 0.0, 0.0, 0.0, 0.0,
                         1.0, 1.0, 1.0, 1.0, 1.0,
                         2.0, 2.0, 2.0, 2.0, 2.0,
                         3.0, 3.0, 3.0, 3.0, 3.0,
                         4.0, 4.0, 4.0, 4.0, 4.0]

    assert expected_x_points == x
    assert expected_y_points == y

    coeffs = fake_grid_stage.projective_transform(
                top_left=top_left, top_right=top_right,
                bottom_right=bottom_right, bottom_left=bottom_left)
    coeffs = list(coeffs)
    x, y = fake_grid_stage.get_xy_coordinate(xx, yy, coeffs)
    assert np.isclose(x.flatten(), expected_x_points).all()
    assert np.isclose(y.flatten(), expected_y_points).all()

    top_left, top_right = (0, 0), (4, -1)
    bottom_left, bottom_right = (1, 4), (5, 3)

    x, y = fake_grid_stage.map_points_second(top_left, top_right, bottom_right,
                                             bottom_left, 5, 5, False)
    # plt.scatter(x, y)
    # plt.show()
