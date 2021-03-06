﻿// ********************************************************************************************************************************************
// Copyright (c) 2019
// Author: USA
// Product: CHILI
// Version: 1.0.0
// ********************************************************************************************************************************************

using System;
using Usa.chili.Common;

namespace Usa.chili.Domain
{
    /// <summary>
    /// Handle business logic for ExtremesTday.
    /// </summary>
    public partial class ExtremesTday
    {
        /// <summary>
        /// Performs any necessary calculations and conversions
        /// </summary>
        /// <param name="isMetricUnits">Returns data in metric units if true, english units if false</param>
        /// <returns>ExtremesTday with calculations and conversions performed</returns>
        public ExtremesTday ConvertUnits(bool isMetricUnits)
        {
            // Prepare English unit versions of the "Today's Extremes" data values
            if (!isMetricUnits)
            {
                // Maximum Wind Speed at 10m
                if (WndSpd10mMax != null)
                {
                    WndSpd10mMax = WndSpd10mMax * Constant.mps2Mph;
                }
                // Maximum Air Temperature at 2m
                if (AirT2mMax != null)
                {
                    AirT2mMax = Math.Round(Constant.nineFifths * (AirT2mMax ?? 0) + 32, 2);
                }
                // Minimum Air Temperature at 2m
                if (AirT2mMin != null)
                {
                    AirT2mMin = Math.Round(Constant.nineFifths * (AirT2mMin ?? 0) + 32, 2);
                }
                // Maximum Dew Point at 2m
                if (DewPt2mMax != null)
                {
                    DewPt2mMax = Math.Round(Constant.nineFifths * (DewPt2mMax ?? 0) + 32, 2);
                }
                // Minimum Dew Point at 2m
                if (DewPt2mMin != null)
                {
                    DewPt2mMin = Math.Round(Constant.nineFifths * (DewPt2mMin ?? 0) + 32, 2);
                }
            }

            return this;
        }
    }
}
