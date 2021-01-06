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
    res = xy.get_sample('sample1', path=sample_file)
    assert res['M'] == 10
    assert res["N"] == 10
    # test sample2 in the file
    xy.save_grid(sample_name='sample2', path=sample_file)
    res = xy.get_sample('sample2', path=sample_file)
    # test all mapped samples
    res = xy.mapped_samples(path=sample_file)
    assert res == ['sample1', 'sample2']
