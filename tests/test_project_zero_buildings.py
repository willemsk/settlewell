import pytest
from settlewell.project import Project, SoilProfile, SoilLayer, ConstructionPit, DewateringConfig

def test_project_zero_buildings_plot():
    # Setup simple project with no buildings
    p = Project()
    p.soil = SoilProfile(
        layers=[
            SoilLayer(
                name="Sand",
                top_elevation=0,
                thickness=10,
                gamma=18,
                gamma_unsat=18,
                gamma_sat=20,
                phi=30,
                c=0,
                E=20000,
                Eoed=20000,
                k_h=1e-4,
                e0=0.5,
                Cc=0.1,
                Cr=0.01,
                Cv=10.0
            )
        ],
        gwl_mtaw=-1,
        surface_level_mtaw=0
    )
    p.pit = ConstructionPit(center_x=0, center_y=0, length=10, width=10, depth=3)
    p.dewatering = DewateringConfig(wells=[], target_drawdown_mtaw=-4, original_gwl_mtaw=-1, pumping_duration_days=30)
    p.buildings = []
    
    p.solve()
    
    # 3D plot and plan view should work without buildings
    fig_3d = p.plot_3d_drawdown()
    assert fig_3d is not None
    
    fig_plan = p.plot_plan_view()
    assert fig_plan is not None
    
    # Settlement trough, cross section, and damage summary should raise errors
    with pytest.raises(ValueError, match="requires at least one building"):
        p.plot_settlement_trough()
        
    with pytest.raises(ValueError, match="requires at least one building"):
        p.plot_cross_section()
        
    with pytest.raises(ValueError, match="requires at least one building"):
        p.plot_damage_summary()

def test_project_setters_validation():
    # Setup simple project
    p = Project()
    p.soil = SoilProfile(
        layers=[
            SoilLayer(
                name="Sand",
                top_elevation=0,
                thickness=10,
                gamma=18,
                gamma_unsat=18,
                gamma_sat=20,
                phi=30,
                c=0,
                E=20000,
                Eoed=20000,
                k_h=1e-4,
                e0=0.5,
                Cc=0.1,
                Cr=0.01,
                Cv=10.0
            )
        ],
        gwl_mtaw=-1,
        surface_level_mtaw=0
    )
    p.pit = ConstructionPit(center_x=0, center_y=0, length=10, width=10, depth=3)
    p.dewatering = DewateringConfig(wells=[], target_drawdown_mtaw=-4, original_gwl_mtaw=-1, pumping_duration_days=30)
    
    # Valid pit change
    p.pit = ConstructionPit(center_x=0, center_y=0, length=20, width=20, depth=3)
    
    # Invalid dewatering change (cross-dependency validation failure)
    with pytest.raises(ValueError, match="cannot be above surface_level_mtaw"):
        p.dewatering = DewateringConfig(wells=[], target_drawdown_mtaw=-4, original_gwl_mtaw=1, pumping_duration_days=30)
        
    # The dewatering should remain the valid one
    assert p.dewatering.original_gwl_mtaw == -1
