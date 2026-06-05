"""配置测试"""
from data_pipeline.config import CONFIG


def test_domain_config():
    assert CONFIG.domain.coarse_grid == (50, 50)
    assert CONFIG.domain.fine_grid == (150, 150)
    assert CONFIG.domain.name == "chengdu_plain"


def test_cma_config():
    assert CONFIG.cma.tianzi_url.startswith("https://")
    assert CONFIG.cma.fenglei_url.startswith("https://")


def test_variable_channels():
    assert len(CONFIG.vars.surface_channels) == 6
    assert len(CONFIG.vars.pressure_channels) == 5
