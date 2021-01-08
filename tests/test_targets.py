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

    coeffs = fake_grid_stage.mesh_interpolation(top_left=top_left,
                                                top_right=top_right,
                                                bottom_right=bottom_right,
                                                bottom_left=bottom_left)
    a = coeffs[0]
    b = coeffs[1]
    # find logical l and m
    m_points, l_points = [], []
    for i in range(xx.shape[0]):
        m_point, l_point = fake_grid_stage.convert_physical_to_logical(
                            a_coeffs=a, b_coeffs=b, x=xx[i], y=yy[i])
        m_points.extend(m_point)
        l_points.extend(l_point)

    # find physical x and y
    x_points, y_points = [], []
    for i in range(len(m_points)):
        x, y = fake_grid_stage.convert_to_physical(a_coeffs=a, b_coeffs=b,
                                                   l_point=l_points[i],
                                                   m_point=m_points[i])
        x_points.append(x)
        y_points.append(y)

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

    assert expected_x_points == x_points
    print(y_points)
    # I AM NOT GET THE EXPECTED Ys!!
    coeffs = fake_grid_stage.projective_transform(
                top_left=top_left, top_right=top_right,
                bottom_right=bottom_right, bottom_left=bottom_left)
    coeffs = list(coeffs)
    x, y = fake_grid_stage.get_xy_coordinate(xx, yy, coeffs)
    assert np.isclose(x.flatten(), expected_x_points).all()
    assert np.isclose(y.flatten(), expected_y_points).all()

    xx = np.linspace(0, 4, 5)
    yy = np.linspace(0, 4, 5)

    top_left, top_right = (0, 0), (4, -1)
    bottom_left, bottom_right = (1, 4), (5, 3)
    xx, yy = np.meshgrid(xx, yy)

    coeffs = fake_grid_stage.projective_transform(
        top_left=top_left, top_right=top_right,
        bottom_right=bottom_right, bottom_left=bottom_left)

    coeffs = list(coeffs)
    x, y = fake_grid_stage.get_xy_coordinate(xx, yy, coeffs)

    # seems to work fine here too
    # plt.scatter(x, y)
    # plt.show()
    coeffs = fake_grid_stage.mesh_interpolation(top_left=top_left,
                                                top_right=top_right,
                                                bottom_right=bottom_right,
                                                bottom_left=bottom_left)
    a = coeffs[0]
    b = coeffs[1]
    print(f'a: {a}')
    print(f'b: {b}')
    # find logical l and m
    m_points, l_points = [], []
    for i in range(xx.shape[0]):
        m_point, l_point = fake_grid_stage.convert_physical_to_logical(
            a_coeffs=a, b_coeffs=b, x=xx[i], y=yy[i])
        m_points.extend(m_point)
        l_points.extend(l_point)

    # find physical x and y
    x_points, y_points = [], []
    for i in range(len(m_points)):
        x, y = fake_grid_stage.convert_to_physical(a_coeffs=a, b_coeffs=b,
                                                   l_point=l_points[i],
                                                   m_point=m_points[i])
        x_points.append(x)
        y_points.append(y)
