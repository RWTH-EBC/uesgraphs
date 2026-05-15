# -*- coding: utf-8 -*-
"""
Tests for the TEASER and OpenDHW integration.

This module tests if TEASER and OpenDHW are able to generate the expected demand profiles 
with the provided GeoJSON, so that the installation of TEASER and OpenDHW is verified.
"""

import pytest
import uesgraphs.DHW_estimation.OpenDHW as OpenDHW
# Close all loggers to release file handles
import logging
import matplotlib.pyplot as plt

class Test_OpenDHW:
    """Integration test OpenDHW functions for DHW demand estimation."""

    def test_OpenDHW(self, monkeypatch):
        """
        Test OpenDHW  for DHW demand estimation.
        """
        monkeypatch.setattr(plt, "show", lambda: None)  # Mock plt.show to prevent blocking during tests
        holidays = OpenDHW.get_holidays(country_code = "DE", year = 2019)
        try:                
            # Step 1: Run OpenDHW for demand generations
            timeseries_df = OpenDHW.generate_dhw_profile(s_step=60, 
                                    categories=1, 
                                    mean_drawoff_vol_per_day=40, 
                                    occupancy=5, 
                                    holidays=holidays, 
                                    building_type="SFH", 
                                    weekend_weekday_factor=1.0)
            timeseries_df = OpenDHW.compute_heat(timeseries_df=timeseries_df)

            OpenDHW.draw_lineplot(timeseries_df=timeseries_df)

            OpenDHW.draw_histplot(timeseries_df=timeseries_df)

            timeseries_dhw_calc = OpenDHW.import_from_dhwcalc(s_step=60*15,
                    categories=1,
                    occupancy=4,
                    mean_drawoff_vol_per_day=40,
                    daylight_saving=False)
            
            OpenDHW.draw_detailed_histplot(timeseries_df=timeseries_dhw_calc)

            timeseries_df_1 = OpenDHW.add_additional_runs(timeseries_df=timeseries_df, 
                                    holidays=holidays, 
                                    occupancy=10, 
                                    building_type="MFH")
            
            OpenDHW.plot_multiple_runs(timeseries_df=timeseries_df_1)

            OpenDHW.compare_generators(timeseries_df_1=timeseries_df, timeseries_df_2=timeseries_df_1)

            OpenDHW.plot_three_histplots(timeseries_df_1=timeseries_df, timeseries_df_2=timeseries_df_1, timeseries_df_3=timeseries_df_1)

            OpenDHW.resample_water_series(timeseries_df=timeseries_df, s_step_output=120)

            OpenDHW.reduce_no_drawoffs(timeseries_df=timeseries_df)

            plt.close("all")
        except Exception as e:
            pytest.fail(f"OpenDHW failed: {e}")
        finally:
            # Close all loggers to release file handles
            logging.shutdown()


