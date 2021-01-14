import pytest
import numpy as np
from ophyd.sim import make_fake_device
from pcdsdevices.targets import XYGridStage
from pcdsdevices.sim import FastMotor


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
    x_motor = FastMotor()
    y_motor = FastMotor()
    grid = FakeGridStage(
        name='test', x_motor=x_motor,
        y_motor=y_motor, m_points=5, n_points=5,
        path=sample_file)
    grid._current_sample = 'current_sample'
    # dummy coeffs
    # a_coeffs = [0.0, 4.0, 0.0, 0.0]
    # b_coeffs = [0.0, 0.0, 4.0, 0.0]
    grid.coefficients = [0.0, 4.0, 0.0, 0.0, 0.0, 0.0, 4.0, 0.0]
    return grid


def test_samples_yaml_file(fake_grid_stage, sample_file):
    xy = fake_grid_stage
    xy.save_grid(sample_name='sample1', path=sample_file)
    # test sample1 in the file:
    res = xy.get_sample_data('sample1', path=sample_file)
    assert res['M'] == 5
    assert res["N"] == 5
    # test sample2 in the file
    xy.save_grid(sample_name='sample2', path=sample_file)
    res = xy.get_sample_data('sample2', path=sample_file)
    # test all mapped samples
    res = xy.get_samples(path=sample_file)
    assert res == ['sample1', 'sample2']
    # test current sample
    current_sample = xy.get_current_sample()
    assert current_sample == 'current_sample'
    # test get_sample_data
    res = xy.get_sample_data('sample2')
    assert res['M'] == 5
    assert res['N'] == 5
    coeffs = [0.0, 4.0, 0.0, 0.0, 0.0, 0.0, 4.0, 0.0]
    assert res['coefficients'] == coeffs
    # test get_sample_map_info - dummy values
    res = xy.get_sample_map_info('sample2')
    assert res == (5, 5, coeffs)


def test_mesh_interpolation(fake_grid_stage):
    xy = fake_grid_stage
    a_coeffs, b_coeffs = xy.mesh_interpolation((0, 0), (4, 0), (4, 4),
                                               (0, 4))
    assert np.isclose(a_coeffs, [0.0, 4.0,  0.0, 0.0]).all()
    assert np.isclose(b_coeffs, [0.0, 0.0, 4.0, 0.0]).all()
    # test with slope -0.25
    a_coeffs, b_coeffs = xy.mesh_interpolation((0, 0), (4, -1), (5, 3),
                                               (1, 4))
    assert np.isclose(a_coeffs, [0.0, 4.0,  1.0, 0.0]).all()
    assert np.isclose(b_coeffs, [0.0, -1.0, 4.0, 0.0]).all()


def test_get_unit_meshgrid(fake_grid_stage):
    xy = fake_grid_stage
    grid = xy.get_unit_meshgrid(m_rows=5, n_columns=5)
    xx_expected = [[0, 0.25, 0.5, 0.75, 1.0],
                   [0, 0.25, 0.5, 0.75, 1.0],
                   [0, 0.25, 0.5, 0.75, 1.0],
                   [0, 0.25, 0.5, 0.75, 1.0],
                   [0, 0.25, 0.5, 0.75, 1.0]]
    yy_expected = [[0.0, 0.0, 0.0, 0.0, 0.0],
                   [0.25, 0.25, 0.25, 0.25, 0.25],
                   [0.5, 0.5, 0.5, 0.5, 0.5],
                   [0.75, 0.75, 0.75, 0.75, 0.75],
                   [1.0, 1.0, 1.0, 1.0, 1.0]]

    assert grid[0].tolist() == xx_expected
    assert grid[1].tolist() == yy_expected


def test_convert_to_physical(fake_grid_stage):
    a_coeffs = [0.0, 4.0, 0.0, 0.0]
    b_coeffs = [0.0, 0.0, 4.0, 0.0]
    # based on these logical values:
    # xx_expected = [[0, 0.25, 0.5, 0.75, 1.0],
    #                [0, 0.25, 0.5, 0.75, 1.0],
    #                [0, 0.25, 0.5, 0.75, 1.0],
    #                [0, 0.25, 0.5, 0.75, 1.0],
    #                [0, 0.25, 0.5, 0.75, 1.0]]
    # yy_expected = [[0.0, 0.0, 0.0, 0.0, 0.0],
    #                [0.25, 0.25, 0.25, 0.25, 0.25],
    #                [0.5, 0.5, 0.5, 0.5, 0.5],
    #                [0.75, 0.75, 0.75, 0.75, 0.75],
    #                [1.0, 1.0, 1.0, 1.0, 1.0]]
    # should get these results:
    # expected_x_points = [0.0, 1.0, 2.0, 3.0, 4.0,
    #                      0.0, 1.0, 2.0, 3.0, 4.0,
    #                      0.0, 1.0, 2.0, 3.0, 4.0,
    #                      0.0, 1.0, 2.0, 3.0, 4.0,
    #                      0.0, 1.0, 2.0, 3.0, 4.0]

    # expected_y_points = [0.0, 0.0, 0.0, 0.0, 0.0,
    #                      1.0, 1.0, 1.0, 1.0, 1.0,
    #                      2.0, 2.0, 2.0, 2.0, 2.0,
    #                      3.0, 3.0, 3.0, 3.0, 3.0,
    #                      4.0, 4.0, 4.0, 4.0, 4.0]
    x, y = fake_grid_stage.convert_to_physical(a_coeffs, b_coeffs, 0, 0)
    # should be 0, 0
    assert (x, y) == (0.0, 0.0)
    x, y = fake_grid_stage.convert_to_physical(a_coeffs, b_coeffs, 0.75, 0.75)
    # should be 3, 3
    assert (x, y) == (3.0, 3.0)
    x, y = fake_grid_stage.convert_to_physical(a_coeffs, b_coeffs, 0.5, 0.0)
    # should be 2, 0
    assert (x, y) == (2.0, 0.0)


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


def test_compute_mapped_point(fake_grid_stage, sample_file):
    fake_grid_stage.save_grid(sample_name='test_sample', path=sample_file)

    x, y = fake_grid_stage.compute_mapped_point('test_sample', 1, 1)
    # first row, first column
    assert (x, y) == (0, 0)
    x, y = fake_grid_stage.compute_mapped_point('test_sample', 1, 2)
    # first row, second column
    assert (x, y) == (1.0, 0)
    # test compute all
    res = fake_grid_stage.compute_mapped_point('test_sample', 1, 2,
                                               compute_all=True)
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
    assert res[0] == expected_x_points
    assert res[1] == expected_y_points
    with pytest.raises(IndexError):
        fake_grid_stage.compute_mapped_point('test_sample', 0, 0)
    with pytest.raises(IndexError):
        fake_grid_stage.compute_mapped_point('test_sample', 6, 0)


def test_move_to_sample(fake_grid_stage, sample_file):
    # position of x and y shouold be 0, 0
    stage = fake_grid_stage
    stage.save_grid(sample_name='test_sample', path=sample_file)
    stage._current_sample = 'test_sample'
    assert stage.x.position == 0
    assert stage.y.position == 0
    stage.move_to_sample(3, 1)
    assert stage.x.position == 0.0
    assert stage.y.position == 2.0


def test_move_to(fake_grid_stage, sample_file):
    stage = fake_grid_stage
    stage.save_grid(sample_name='current_sample', path=sample_file)
    stage._current_sample = 'current_sample'
    stage.save_grid(sample_name='test_sample', path=sample_file)
    assert stage.x.position == 0
    assert stage.y.position == 0
    stage.move_to('test_sample', 3, 1)
    assert stage.x.position == 0.0
    assert stage.y.position == 2.0


def test_load_sample(fake_grid_stage, sample_file):
    stage = fake_grid_stage
    stage.save_grid(sample_name='current_sample', path=sample_file)
    stage.load_sample('current_sample')
    assert stage.get_current_sample() == 'current_sample'
