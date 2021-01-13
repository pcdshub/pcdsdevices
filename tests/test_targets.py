import pytest
from ophyd.sim import make_fake_device
from pcdsdevices.targets import XYGridStage


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
    res = xy.get_sample_data('sample1', path=sample_file)
    assert res['M'] == 10
    assert res["N"] == 10
    # test sample2 in the file
    xy.save_grid(sample_name='sample2', path=sample_file)
    res = xy.get_sample_data('sample2', path=sample_file)
    # test all mapped samples
    res = xy.get_samples(path=sample_file)
    assert res == ['sample1', 'sample2']


def test_mapping_points(fake_grid_stage):
    # test grid of 5 rows by 5 columns
    top_left, top_right, bottom_right, bottom_left = ((0, 0), (4, 0), (4, 4),
                                                      (0, 4))
    x, y = fake_grid_stage.map_points(top_left, top_right, bottom_right,
                                      bottom_left, 5, 5)
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

    # test grid of 3 rows by 5 columns
    top_left, top_right, bottom_right, bottom_left = ((0, 0), (2, 0), (2, 4),
                                                      (0, 4))
    x, y = fake_grid_stage.map_points(top_left, top_right, bottom_right,
                                      bottom_left, 5, 3)
    expected_x_points = [0.0, 1.0, 2.0,
                         0.0, 1.0, 2.0,
                         0.0, 1.0, 2.0,
                         0.0, 1.0, 2.0,
                         0.0, 1.0, 2.0]

    expected_y_points = [0.0, 0.0, 0.0,
                         1.0, 1.0, 1.0,
                         2.0, 2.0, 2.0,
                         3.0, 3.0, 3.0,
                         4.0, 4.0, 4.0]
    assert expected_x_points == x
    assert expected_y_points == y

    # test 5 by 5 grid with slope of -0.25
    top_left, top_right, bottom_right, bottom_left = ((0, 0), (4, -1), (5, 3),
                                                      (1, 4))
    x, y = fake_grid_stage.map_points(top_left, top_right, bottom_right,
                                      bottom_left, 5, 5)
    expected_x_points = [0.0, 1.0, 2.0, 3.0, 4.0,
                         0.25, 1.25, 2.25, 3.25, 4.25,
                         0.50, 1.50, 2.50, 3.50, 4.50,
                         0.75, 1.75, 2.75, 3.75, 4.75,
                         1.0, 2.0, 3.0, 4.0, 5.0]

    expected_y_points = [0.0, -0.25, -0.50, -0.75, -1,
                         1.0, 0.75, 0.50, 0.25, 0,
                         2.0, 1.75, 1.50, 1.25, 1,
                         3.0, 2.75, 2.50, 2.25, 2,
                         4.0, 3.75, 3.50, 3.25, 3]
    assert expected_x_points == x
    assert expected_y_points == y
