"""QWizard orchestrator for the 6-step settlement analysis workflow."""

from PySide6.QtWidgets import QWizard

from .pages.buildings import BuildingsPage
from .pages.construction_pit import ConstructionPitPage
from .pages.dewatering import DewateringConfigPage
from .pages.results import ResultsPage
from .pages.soil_profile import SoilProfilePage
from .pages.wells import WellsPage


class SettlewellWizard(QWizard):
    """Six-step wizard for the complete settlement analysis workflow.

    Page IDs:
        0 — SoilProfilePage
        1 — ConstructionPitPage
        2 — WellsPage
        3 — DewateringConfigPage
        4 — BuildingsPage
        5 — ResultsPage
    """

    PAGE_SOIL_PROFILE = 0
    PAGE_CONSTRUCTION_PIT = 1
    PAGE_WELLS = 2
    PAGE_DEWATERING = 3
    PAGE_BUILDINGS = 4
    PAGE_RESULTS = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settlewell — Zetbaarheidsanalyse")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        # Configure options
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        self.setOption(QWizard.WizardOption.NoBackButtonOnLastPage, True)

        # Custom button texts
        self.setButtonText(QWizard.WizardButton.NextButton, "Volgende >")
        self.setButtonText(QWizard.WizardButton.BackButton, "< Vorige")
        self.setButtonText(QWizard.WizardButton.FinishButton, "Voltooien")
        self.setButtonText(QWizard.WizardButton.CancelButton, "Annuleren")

        # Instantiate pages
        self.soil_page = SoilProfilePage(self)
        self.pit_page = ConstructionPitPage(self)
        self.wells_page = WellsPage(self)
        self.dewatering_page = DewateringConfigPage(self)
        self.buildings_page = BuildingsPage(self)
        self.results_page = ResultsPage(self)

        # Add pages to wizard
        self.setPage(self.PAGE_SOIL_PROFILE, self.soil_page)
        self.setPage(self.PAGE_CONSTRUCTION_PIT, self.pit_page)
        self.setPage(self.PAGE_WELLS, self.wells_page)
        self.setPage(self.PAGE_DEWATERING, self.dewatering_page)
        self.setPage(self.PAGE_BUILDINGS, self.buildings_page)
        self.setPage(self.PAGE_RESULTS, self.results_page)

    def get_state(self) -> dict:
        """Serialize state from all wizard pages into a dictionary."""
        state = {}
        for page_id in self.pageIds():
            page = self.page(page_id)
            if hasattr(page, "get_state"):
                state.update(page.get_state())
        return state

    def load_state(self, data: dict) -> None:
        """Populate wizard pages from a state dictionary."""
        for page_id in self.pageIds():
            page = self.page(page_id)
            if hasattr(page, "load_state"):
                page.load_state(data)
