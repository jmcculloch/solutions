"""Tropical Tree Staples solution model.
   Excel filename: Drawdown-Tropical Tree Staples_BioS_v1.1_3Jan2019_PUBLIC.xlsm
"""

import pathlib

import numpy as np
import pandas as pd

from model import adoptiondata
from model import advanced_controls as ac
from model import aez
from model import ch4calcs
from model import co2calcs
from model import customadoption
from model import dd
from model import emissionsfactors
from model import firstcost
from model import helpertables
from model import operatingcost
from model import s_curve
from model import unitadoption
from model import vma
from model import tla
from solution import land

DATADIR = pathlib.Path(__file__).parents[2].joinpath('data')
THISDIR = pathlib.Path(__file__).parents[0]
VMAs = {
  'Current Adoption': vma.VMA(
      filename=None, use_weight=False),
  'CONVENTIONAL First Cost per Implementation Unit': vma.VMA(
      filename=None, use_weight=False),
  'SOLUTION First Cost per Implementation Unit': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "SOLUTION_First_Cost_per_Implementation_Unit.csv"),
      use_weight=False),
  'CONVENTIONAL Operating Cost per Functional Unit per Annum': vma.VMA(
      filename=DATADIR.joinpath(*('land', 'vma_cattle_CONVENTIONAL_Operating_Cost_per_Functional_Unit_per_Annum.csv')),
      use_weight=False),
  'SOLUTION Operating Cost per Functional Unit per Annum': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "SOLUTION_Operating_Cost_per_Functional_Unit_per_Annum.csv"),
      use_weight=False),
  'CONVENTIONAL Net Profit Margin per Functional Unit per Annum': vma.VMA(
      filename=DATADIR.joinpath(*('land', 'vma_cattle_CONVENTIONAL_Net_Profit_Margin_per_Functional_Unit_per_Annum.csv')),
      use_weight=False),
  'SOLUTION Net Profit Margin per Functional Unit per Annum': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "SOLUTION_Net_Profit_Margin_per_Functional_Unit_per_Annum.csv"),
      use_weight=False),
  'Yield from CONVENTIONAL Practice': vma.VMA(
      filename=DATADIR.joinpath(*('land', 'vma_Yield_from_CONVENTIONAL_Practice.csv')),
      use_weight=False),
  'Yield Gain (% Increase from CONVENTIONAL to SOLUTION)': vma.VMA(
      filename=None, use_weight=False),
  'Electricty Consumed per CONVENTIONAL Functional Unit': vma.VMA(
      filename=None, use_weight=False),
  'SOLUTION Energy Efficiency Factor': vma.VMA(
      filename=None, use_weight=False),
  'Total Energy Used per SOLUTION functional unit': vma.VMA(
      filename=None, use_weight=False),
  'Fuel Consumed per CONVENTIONAL Functional Unit': vma.VMA(
      filename=None, use_weight=False),
  'Fuel Reduction Factor SOLUTION': vma.VMA(
      filename=None, use_weight=False),
  't CO2-eq (Aggregate emissions) Reduced per Land Unit': vma.VMA(
      filename=None, use_weight=False),
  't CO2 Reduced per Land Unit': vma.VMA(
      filename=None, use_weight=False),
  't N2O-CO2-eq Reduced per Land Unit': vma.VMA(
      filename=None, use_weight=False),
  't CH4-CO2-eq Reduced per Land Unit': vma.VMA(
      filename=None, use_weight=False),
  'Indirect CO2 Emissions per CONVENTIONAL Implementation OR functional Unit -- CHOOSE ONLY ONE': vma.VMA(
      filename=None, use_weight=False),
  'Indirect CO2 Emissions per SOLUTION Implementation Unit': vma.VMA(
      filename=None, use_weight=False),
  'Sequestration Rates': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "Sequestration_Rates.csv"),
      use_weight=False),
  'Sequestered Carbon NOT Emitted after Cyclical Harvesting/Clearing': vma.VMA(
      filename=None, use_weight=False),
  'Disturbance Rate': vma.VMA(
      filename=None, use_weight=False),
  'Yield of Annual Staple Crops': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "Yield_of_Annual_Staple_Crops.csv"),
      use_weight=False),
  'Yield of Perennial Staple Crops': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "Yield_of_Perennial_Staple_Crops.csv"),
      use_weight=False),
}
vma.populate_fixed_summaries(vma_dict=VMAs, filename=THISDIR.joinpath('vma_data', 'VMA_info.csv'))
print(str(VMAs))

units = {
  "implementation unit": None,
  "functional unit": "Mha",
  "first cost": "US$B",
  "operating cost": "US$B",
}

name = 'Tropical Tree Staples'
solution_category = ac.SOLUTION_CATEGORY.LAND

scenarios = ac.load_scenarios_from_json(directory=THISDIR.joinpath('ac'), vmas=VMAs)


class Scenario:
  name = name
  units = units
  vmas = VMAs
  solution_category = solution_category

  def __init__(self, scenario=None):
    if scenario is None:
      scenario = list(scenarios.keys())[0]
    self.scenario = scenario
    self.ac = scenarios[scenario]

    # TLA
    self.ae = aez.AEZ(solution_name=self.name)
    if self.ac.use_custom_tla:
      self.c_tla = tla.CustomTLA(filename=THISDIR.joinpath('custom_tla_data.csv'))
      custom_world_vals = self.c_tla.get_world_values()
    else:
      custom_world_vals = None
    self.tla_per_region = tla.tla_per_region(self.ae.get_land_distribution(), custom_world_values=custom_world_vals)

    # Custom PDS Data
    ca_pds_columns = ['Year', 'World'] + dd.MAIN_REGIONS
    ca_pds_data_sources = [
      {'name': 'Average growth, linear trend', 'include': True,
          # This scenario is built on the historical (1962-2012) average global growth rate of
          # tropical staple crops. The historical data available for each decade was interpolated
          # based on the best curve fit and the interpolated data were then used in the
          # AdoptionData. The calculation uses the 2050 adopted value and calculates the
          # percentage with reference to the TLA, which is used to build this adoption scenario. 
          'datapoints': pd.DataFrame([
              [2014, 25.42446198181150, 0.0, 0.0, 0.0, 0.0, 0.0],
              [2050, self.tla_per_region.loc[2050, 'World'] * 0.6179095040166380,
                  0.0, 0.0, 0.0, 0.0, 0.0],
              ], columns=ca_pds_columns).set_index('Year')
          },
      {'name': 'Medium growth, linear trend', 'include': True,
          # This scenario is built on the historical (1962-2012) average global growth rate of
          # tropical staple crops. The historical data available for each decade was interpolated
          # based on the best curve fit and the interpolated data were then used in the
          # AdoptionData. This scenario presents the result assuming a 5% increase on the
          # historical growth rate. The calculation uses the 2050 adopted value and calculates
          # the percentage with reference to the TLA, which is used to build this adoption scenario.
          'datapoints': pd.DataFrame([
              [2014, 25.42446198181150, 0.0, 0.0, 0.0, 0.0, 0.0],
              [2050, self.tla_per_region.loc[2050, 'World'] * 0.648804979217470,
                  0.0, 0.0, 0.0, 0.0, 0.0],
              ], columns=ca_pds_columns).set_index('Year')
          },
      {'name': 'Low growth linear trend', 'include': True,
          # It is assumed that the adoption of tropical tree staples will reach 55% of its
          # TLA by 2050.
          'datapoints': pd.DataFrame([
              [2014, 25.42446198181150, 0.0, 0.0, 0.0, 0.0, 0.0],
              [2050, self.tla_per_region.loc[2050, 'World'] * 0.55, 0.0, 0.0, 0.0, 0.0, 0.0],
              ], columns=ca_pds_columns).set_index('Year')
          },
      {'name': 'Low early growth, linear trend', 'include': True,
          # This scenario assumes 60% adoption of the solution by 2030 and remains same until 2050.
          # The early adoption of the solution was considered because of the higher carbon and
          # financial impact of the solution and lower land availability.
          'datapoints': pd.DataFrame([
              [2014, 25.42446198181150, 0.0, 0.0, 0.0, 0.0, 0.0],
              [2030, self.tla_per_region.loc[2030, 'World'] * 0.6, 0.0, 0.0, 0.0, 0.0, 0.0],
              [2050, self.tla_per_region.loc[2050, 'World'] * 0.6, 0.0, 0.0, 0.0, 0.0, 0.0],
              ], columns=ca_pds_columns).set_index('Year')
          },
      {'name': 'Max early growth, linear trend', 'include': True,
          # This scenario assumes 100% adoption of the solution by 2050 with the assumption that
          # 70% of that adoption will be acheived by 2030. The early adoption of the solution was
          # considered because of the higher carbon and financial impact of the solution and lower
          # land availability.
          'datapoints': pd.DataFrame([
              [2014, 25.42446198181150, 0.0, 0.0, 0.0, 0.0, 0.0],
              [2030, self.tla_per_region.loc[2030, 'World'] * 0.7, 0.0, 0.0, 0.0, 0.0, 0.0],
              [2050, self.tla_per_region.loc[2050, 'World'] * 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
              ], columns=ca_pds_columns).set_index('Year')
          },
    ]
    self.pds_ca = customadoption.CustomAdoption(data_sources=ca_pds_data_sources,
        soln_adoption_custom_name=self.ac.soln_pds_adoption_custom_name,
        high_sd_mult=1.0, low_sd_mult=1.0,
        total_adoption_limit=self.tla_per_region)


    if False:
      # One may wonder why this is here. This file was code generated.
      # This 'if False' allows subsequent conditions to all be elif.
      pass
    elif self.ac.soln_pds_adoption_basis == 'Fully Customized PDS':
      pds_adoption_data_per_region = self.pds_ca.adoption_data_per_region()
      pds_adoption_trend_per_region = self.pds_ca.adoption_trend_per_region()
      pds_adoption_is_single_source = None

    ht_ref_adoption_initial = pd.Series(
      [25.424461981811515, 0.03142549034684199, 0.0, 28.59165470128803, 17.01389600193888,
       5.211947770049295, 0.0, 0.0, 0.0, 0.0],
       index=dd.REGIONS)
    ht_ref_adoption_final = self.tla_per_region.loc[2050] * (ht_ref_adoption_initial / self.tla_per_region.loc[2014])
    ht_ref_datapoints = pd.DataFrame(columns=dd.REGIONS)
    ht_ref_datapoints.loc[2014] = ht_ref_adoption_initial
    ht_ref_datapoints.loc[2050] = ht_ref_adoption_final.fillna(0.0)
    ht_pds_adoption_initial = ht_ref_adoption_initial
    ht_regions, ht_percentages = zip(*self.ac.pds_adoption_final_percentage)
    ht_pds_adoption_final_percentage = pd.Series(list(ht_percentages), index=list(ht_regions))
    ht_pds_adoption_final = ht_pds_adoption_final_percentage * self.tla_per_region.loc[2050]
    ht_pds_datapoints = pd.DataFrame(columns=dd.REGIONS)
    ht_pds_datapoints.loc[2014] = ht_pds_adoption_initial
    ht_pds_datapoints.loc[2050] = ht_pds_adoption_final.fillna(0.0)
    self.ht = helpertables.HelperTables(ac=self.ac,
        ref_datapoints=ht_ref_datapoints, pds_datapoints=ht_pds_datapoints,
        pds_adoption_data_per_region=pds_adoption_data_per_region,
        ref_adoption_limits=self.tla_per_region, pds_adoption_limits=self.tla_per_region,
        pds_adoption_trend_per_region=pds_adoption_trend_per_region,
        pds_adoption_is_single_source=pds_adoption_is_single_source)

    self.ef = emissionsfactors.ElectricityGenOnGrid(ac=self.ac)

    self.ua = unitadoption.UnitAdoption(ac=self.ac,
        ref_total_adoption_units=self.tla_per_region, pds_total_adoption_units=self.tla_per_region,
        electricity_unit_factor=1000000.0,
        soln_ref_funits_adopted=self.ht.soln_ref_funits_adopted(),
        soln_pds_funits_adopted=self.ht.soln_pds_funits_adopted(),
        bug_cfunits_double_count=True)
    soln_pds_tot_iunits_reqd = self.ua.soln_pds_tot_iunits_reqd()
    soln_ref_tot_iunits_reqd = self.ua.soln_ref_tot_iunits_reqd()
    conv_ref_tot_iunits = self.ua.conv_ref_tot_iunits()
    soln_net_annual_funits_adopted=self.ua.soln_net_annual_funits_adopted()

    self.fc = firstcost.FirstCost(ac=self.ac, pds_learning_increase_mult=2,
        ref_learning_increase_mult=2, conv_learning_increase_mult=2,
        soln_pds_tot_iunits_reqd=soln_pds_tot_iunits_reqd,
        soln_ref_tot_iunits_reqd=soln_ref_tot_iunits_reqd,
        conv_ref_tot_iunits=conv_ref_tot_iunits,
        soln_pds_new_iunits_reqd=self.ua.soln_pds_new_iunits_reqd(),
        soln_ref_new_iunits_reqd=self.ua.soln_ref_new_iunits_reqd(),
        conv_ref_new_iunits=self.ua.conv_ref_new_iunits(),
        conv_ref_first_cost_uses_tot_units=True,
        fc_convert_iunit_factor=land.MHA_TO_HA)

    self.oc = operatingcost.OperatingCost(ac=self.ac,
        soln_net_annual_funits_adopted=soln_net_annual_funits_adopted,
        soln_pds_tot_iunits_reqd=soln_pds_tot_iunits_reqd,
        soln_ref_tot_iunits_reqd=soln_ref_tot_iunits_reqd,
        conv_ref_annual_tot_iunits=self.ua.conv_ref_annual_tot_iunits(),
        soln_pds_annual_world_first_cost=self.fc.soln_pds_annual_world_first_cost(),
        soln_ref_annual_world_first_cost=self.fc.soln_ref_annual_world_first_cost(),
        conv_ref_annual_world_first_cost=self.fc.conv_ref_annual_world_first_cost(),
        single_iunit_purchase_year=2017,
        soln_pds_install_cost_per_iunit=self.fc.soln_pds_install_cost_per_iunit(),
        conv_ref_install_cost_per_iunit=self.fc.conv_ref_install_cost_per_iunit(),
        conversion_factor=land.MHA_TO_HA)

    self.c4 = ch4calcs.CH4Calcs(ac=self.ac,
        soln_pds_direct_ch4_co2_emissions_saved=self.ua.direct_ch4_co2_emissions_saved_land(),
        soln_net_annual_funits_adopted=soln_net_annual_funits_adopted)

    self.c2 = co2calcs.CO2Calcs(ac=self.ac,
        ch4_ppb_calculator=self.c4.ch4_ppb_calculator(),
        soln_pds_net_grid_electricity_units_saved=self.ua.soln_pds_net_grid_electricity_units_saved(),
        soln_pds_net_grid_electricity_units_used=self.ua.soln_pds_net_grid_electricity_units_used(),
        soln_pds_direct_co2eq_emissions_saved=self.ua.direct_co2eq_emissions_saved_land(),
        soln_pds_direct_co2_emissions_saved=self.ua.direct_co2_emissions_saved_land(),
        soln_pds_direct_n2o_co2_emissions_saved=self.ua.direct_n2o_co2_emissions_saved_land(),
        soln_pds_direct_ch4_co2_emissions_saved=self.ua.direct_ch4_co2_emissions_saved_land(),
        soln_pds_new_iunits_reqd=self.ua.soln_pds_new_iunits_reqd(),
        soln_ref_new_iunits_reqd=self.ua.soln_ref_new_iunits_reqd(),
        conv_ref_new_iunits=self.ua.conv_ref_new_iunits(),
        conv_ref_grid_CO2_per_KWh=self.ef.conv_ref_grid_CO2_per_KWh(),
        conv_ref_grid_CO2eq_per_KWh=self.ef.conv_ref_grid_CO2eq_per_KWh(),
        soln_net_annual_funits_adopted=soln_net_annual_funits_adopted,
        annual_land_area_harvested=self.ua.soln_pds_annual_land_area_harvested(),
        regime_distribution=self.ae.get_land_distribution())

