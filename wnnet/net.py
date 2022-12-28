import wnutils.xml as wx
import wnnet.nuc as wn
import wnnet.reac as wr
import numpy as np
from astropy.constants import c, m_e


class Net(wn.Nuc, wr.Reac):
    """A class for to store webnucleo networks."""

    def __init__(self, file):
        wn.Nuc.__init__(self, file)
        wr.Reac.__init__(self, file)

    def compute_Q_values(self, nuc_xpath="", reac_xpath=""):
        result = {}
        nuclides = self.get_nuclides(nuc_xpath=nuc_xpath)
        reactions = self.get_reactions(reac_xpath=reac_xpath)
        for r in reactions:
            tmp = self.compute_reaction_Q_value(nuclides, reactions[r])
            if tmp:
                result[r] = tmp

        return result

    def get_valid_reactions(self, nuc_xpath="", reac_xpath=""):
        result = {}
        nuclides = self.get_nuclides(nuc_xpath=nuc_xpath)
        reactions = self.get_reactions(reac_xpath=reac_xpath)
        for r in reactions:
            if self.is_valid_reaction(nuclides, reactions[r]):
                result[r] = reactions[r]
        return result

    def compute_reaction_Q_value(self, nuclides, reaction):
        result = 0
        for sp in reaction.nuclide_reactants:
            if sp not in nuclides:
                return None
            else:
                result += nuclides[sp]["mass excess"]
        for sp in reaction.nuclide_products:
            if sp not in nuclides:
                return None
            else:
                result -= nuclides[sp]["mass excess"]

        if (
            "positron" in reaction.nuclide_products
            and "neutrino_e" in reaction.nuclide_products
        ):
            E = m_e * c**2
            result -= 2.0 * E.to("MeV").value

        if (
            "positron" in reaction.nuclide_reactants
            and "anti-neutrino_e" in reaction_products
        ):
            E = m_e * c**2
            result += 2.0 * E.to("MeV").value

        return result

    def is_valid_reaction(self, nuclides, reaction):
        for sp in reaction.nuclide_reactants + reaction.nuclide_products:
            if sp not in nuclides:
                return False
        return True

    def compute_rates_for_reaction(self, nuclides, reaction, t9, rho):
        forward = reaction.compute_rate(t9)

        d_exp = 0

        for sp in reaction.nuclide_reactants:
            d_exp += self.compute_NSE_factor(nuclides, nuclides[sp], t9, rho)
        for sp in reaction.nuclide_products:
            d_exp -= self.compute_NSE_factor(nuclides, nuclides[sp], t9, rho)

        d_exp += (
            len(reaction.nuclide_reactants) - len(reaction.nuclide_products)
        ) * np.log(rho)

        if d_exp < -300.0:
            return (forward, 0)

        if d_exp > 300.0:
            return (0, 0)

        tup = self.compute_reaction_duplicate_factors(reaction)

        return (forward, np.exp(d_exp) * (tup[1] / tup[0]) * forward)

    def compute_rates(self, t9, rho, nuc_xpath="", reac_xpath=""):
        v_reactions = self.get_valid_reactions(
            nuc_xpath=nuc_xpath, reac_xpath=reac_xpath
        )

        result = {}

        nuclides = self.get_nuclides()

        for r in v_reactions:
            result[r] = self.compute_rates_for_reaction(
                nuclides, v_reactions[r], t9, rho
            )

        return result
