import pytest
from ophyd.sim import make_fake_device
from pcdsdevices.targets import XYGridStage


@pytest.fixture(scope='function')
def fake_grid_stage():
    FakeGridStage = make_fake_device(XYGridStage)
    grid = FakeGridStage(
        name='test', x_prefix='X:MMN:PREFIX',
        y_prefix='Y:MMN:PREFIX', x_spacing=0.25, y_spacing=0.25,
        path='/dummy/path/samples.yml')
    return grid


@pytest.fixture(scope='function')
def sample_file(tmp_path):
    path = tmp_path / "sub"
    path.mkdir()
    sample_file = path / "samples.yml"
    sample_file.write_text('')
    return sample_file


def test_samples_yaml_file(fake_grid_stage, sample_file):
    xy = fake_grid_stage
    x_points = [1, 2, 3, 4]
    y_points = [1, 2, 3, 4]
    xy.save_grid(sample_name='sample1', x_points=x_points, y_points=y_points,
                 path=sample_file)
    # test sample1 in the file:
    res = xy.get_grid('sample1', path=sample_file)
    assert res == (x_points, y_points)
    # test update grid for sample1
    y_points = [4, 4, 4, 4]
    xy.save_grid(sample_name='sample1', x_points=x_points, y_points=y_points,
                 path=sample_file)
    res = xy.get_grid('sample1', path=sample_file)
    assert res == (x_points, y_points)
    # test sample2 in the file
    x2_points = [0, -1, -2, -3]
    y2_points = [1, 0, 3, 1]
    xy.save_grid(sample_name='sample2', x_points=x2_points, y_points=y2_points,
                 path=sample_file)
    res = xy.get_grid('sample2', path=sample_file)
    assert res == (x2_points, y2_points)
    # assert sample1 is still there
    res = xy.get_grid('sample1', path=sample_file)
    assert res == (x_points, y_points)
    # test all mapped samples
    res = xy.mapped_samples(path=sample_file)
    assert res == ['sample1', 'sample2']