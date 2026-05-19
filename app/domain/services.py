from app.domain.models import EnergyDelivered, SessionCost


class PricingService:
    """
    Domain Service – beregner SessionCost fra EnergyDelivered og TariffRate.
    Ingen framework-afhængigheder – fuldt testbar uden at starte API'et.
    """

    def calculate(self, energy: EnergyDelivered, tariff_rate: float) -> SessionCost:
        if tariff_rate <= 0:
            raise ValueError("TariffRate must be positive")
        return SessionCost(
            amount_dkk=round(energy.kwh * tariff_rate, 2),
            tariff_rate=tariff_rate,
        )
