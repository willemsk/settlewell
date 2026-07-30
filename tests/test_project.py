import pytest

from settlewell import (
    Building,
    ConstructionPit,
    DewateringConfig,
    LoadGeometry,
    Project,
    ProjectResults,
    SoilLayer,
    SoilProfile,
    SolverSettings,
    Well,
)


@pytest.fixture
def sample_soil() -> SoilProfile:
    l1 = SoilLayer(
        name="Sand",
        thickness=3.0,
        gamma=17.5,
        gamma_sat=19.5,
        k_h=1e-4,
        e0=0.65,
        Cc=0.05,
        Cr=0.01,
        Eoed=25000.0,
        Cv=15e-7,
    )
    l2 = SoilLayer(
        name="Clay",
        thickness=6.5,
        gamma=15.0,
        gamma_sat=17.0,
        k_h=1e-9,
        e0=1.10,
        Cc=0.35,
        Cr=0.06,
        Eoed=8000.0,
        Cv=5e-8,
        OCR=3.0,
    )
    return SoilProfile(layers=[l1, l2], gwl_mtaw=5.0, surface_level_mtaw=7.0)


@pytest.fixture
def sample_pit() -> ConstructionPit:
    return ConstructionPit(length=20.0, width=15.0, depth=3.5)


@pytest.fixture
def sample_dewatering() -> DewateringConfig:
    wells = [Well(x=5.0, y=0.0, Q=0.005), Well(x=-5.0, y=0.0, Q=0.005)]
    return DewateringConfig(
        wells=wells,
        target_drawdown_mtaw=1.5,
        original_gwl_mtaw=5.0,
        pumping_duration_days=90.0,
    )


@pytest.fixture
def sample_building() -> Building:
    return Building(x=30.0, y=0.0, length=12.0, width=8.0, name="Neighbor House")


@pytest.fixture
def sample_load() -> LoadGeometry:
    return LoadGeometry(name="Crane Footing", width_B=4.0, length_L=4.0, stress_q=100.0)


class TestProjectInitializationAndValidation:
    def test_empty_init(self):
        """Test Project initializes cleanly with default/None properties."""
        p = Project()
        assert p.soil is None
        assert p.pit is None
        assert p.dewatering is None
        assert p.buildings == []
        assert p.loads == []
        assert isinstance(p.settings, SolverSettings)
        assert p.results is None

    def test_property_setters_and_invalidation(
        self,
        sample_soil: SoilProfile,
        sample_pit: ConstructionPit,
        sample_dewatering: DewateringConfig,
    ):
        """Test property setters update state and auto-invalidate results."""
        p = Project(soil=sample_soil, pit=sample_pit, dewatering=sample_dewatering)
        # Mock results
        p._results = ProjectResults()
        assert p.results is not None

        # Changing soil should invalidate results
        p.soil = sample_soil
        assert p.results is None

    def test_cross_dependency_validation(
        self, sample_soil: SoilProfile, sample_dewatering: DewateringConfig
    ):
        """Test validation error if original_gwl_mtaw > surface_level_mtaw."""
        invalid_dewatering = DewateringConfig(
            wells=[],
            target_drawdown_mtaw=1.0,
            original_gwl_mtaw=10.0,  # > surface 7.0
            pumping_duration_days=30.0,
        )
        with pytest.raises(ValueError, match="original_gwl_mtaw"):
            Project(soil=sample_soil, dewatering=invalid_dewatering)


class TestProjectSolveLifecycle:
    def test_solve_ready_check(self):
        """Test solve() raises ValueError if soil, pit, or dewatering missing."""
        p = Project()
        with pytest.raises(ValueError, match="must be set before calling solve"):
            p.solve()

    def test_full_solve_workflow(
        self,
        sample_soil: SoilProfile,
        sample_pit: ConstructionPit,
        sample_dewatering: DewateringConfig,
        sample_building: Building,
        sample_load: LoadGeometry,
    ):
        """Test full solve() workflow across hydraulics, stress, settlement, and damage."""
        p = Project(
            soil=sample_soil,
            pit=sample_pit,
            dewatering=sample_dewatering,
            buildings=[sample_building],
            loads=[sample_load],
        )

        res = p.solve()
        assert isinstance(res, ProjectResults)
        assert p.results is res

        # Hydraulics assertions
        assert res.hydraulics is not None
        assert res.hydraulics.T > 0
        assert res.hydraulics.R > 0
        assert res.hydraulics.drawdown_grid is not None
        assert res.hydraulics.drawdown_grid.ndim == 2

        # Stress assertions
        assert res.stress is not None
        assert len(res.stress.z) == len(sample_soil.layers)

        # Settlement assertions
        assert res.settlement is not None
        assert res.settlement.total_settlement > 0
        assert len(res.settlement.per_layer_settlements) == len(sample_soil.layers)
        assert res.settlement.time_settlement_curve is not None

        # Damage assertions
        assert res.damage is not None
        assert "Neighbor House" in res.damage.assessments


class TestProjectSerialization:
    def test_to_dict_and_from_dict(
        self,
        sample_soil: SoilProfile,
        sample_pit: ConstructionPit,
        sample_dewatering: DewateringConfig,
        sample_building: Building,
    ):
        """Test roundtrip dictionary serialization."""
        p1 = Project(
            soil=sample_soil,
            pit=sample_pit,
            dewatering=sample_dewatering,
            buildings=[sample_building],
        )
        d = p1.to_dict()
        assert isinstance(d, dict)
        assert "soil" in d
        assert "pit" in d
        assert "dewatering" in d

        p2 = Project.from_dict(d)
        assert p2.soil is not None
        assert p2.soil.gwl_mtaw == sample_soil.gwl_mtaw
        assert p2.pit is not None
        assert p2.pit.length == sample_pit.length
        assert len(p2.buildings) == 1
        assert p2.buildings[0].name == sample_building.name

    def test_save_and_load_file(
        self,
        sample_soil: SoilProfile,
        sample_pit: ConstructionPit,
        sample_dewatering: DewateringConfig,
        tmp_path,
    ):
        """Test saving and loading Project from JSON file."""
        p1 = Project(soil=sample_soil, pit=sample_pit, dewatering=sample_dewatering)
        file_path = tmp_path / "project.settlewell"
        p1.save(file_path)

        assert file_path.exists()

        p2 = Project.load(file_path)
        assert p2.soil is not None
        assert len(p2.soil.layers) == len(sample_soil.layers)
        assert p2.pit is not None
        assert p2.pit.width == sample_pit.width


class TestProjectTemplateLoader:
    def test_from_template_antwerp_boom_clay(self):
        """Test creating Project from Flemish soil template."""
        p = Project.from_template(
            "Antwerp Boom Clay Formation", gwl_mtaw=5.0, surface_level_mtaw=7.0
        )
        assert p.soil is not None
        assert len(p.soil.layers) > 1
        assert p.soil.surface_level_mtaw == 7.0
        assert p.soil.gwl_mtaw == 5.0

    def test_from_template_invalid_raises(self):
        """Test invalid template name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown template"):
            Project.from_template("NON_EXISTENT_TEMPLATE", 0.0, 5.0)


class TestProjectPlottingSmoke:
    def test_plotting_methods_run_without_error(
        self,
        sample_soil: SoilProfile,
        sample_pit: ConstructionPit,
        sample_dewatering: DewateringConfig,
        sample_building: Building,
    ):
        """Smoke test verifying all Project plotting wrapper methods execute cleanly."""
        p = Project(
            soil=sample_soil,
            pit=sample_pit,
            dewatering=sample_dewatering,
            buildings=[sample_building],
        )
        p.solve()

        # Execute plot methods
        fig1 = p.plot_cross_section()
        assert fig1 is not None

        fig2 = p.plot_plan_view()
        assert fig2 is not None

        fig3 = p.plot_settlement_trough()
        assert fig3 is not None

        fig4 = p.plot_time_settlement()
        assert fig4 is not None

        fig5 = p.plot_effective_stress_profile()
        assert fig5 is not None

        fig6 = p.plot_3d_drawdown()
        assert fig6 is not None

        fig7 = p.plot_damage_summary()
        assert fig7 is not None
