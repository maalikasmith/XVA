import classBGM_test
import datetime
import pandas as pd
import os
import cal
# import matplotlib.pyplot as plt
from date import daycount as dc
import sys

# --------------------------- Data --------------------------------
euribor_zero_curve = pd.read_csv("C:\\Marco\\discount_curve.csv")
BGM_fwd_rates = pd.read_csv("C:\\Marco\\BGM_forward_rates_euribor_zero_curve.csv")

for d in range(len(euribor_zero_curve["Start Date"])):
    euribor_zero_curve.loc[d, "Start Date"] = \
        datetime.datetime.strptime(euribor_zero_curve.loc[d, "Start Date"], "%d-%b-%y")
    euribor_zero_curve.loc[d, "End Date"] = \
        datetime.datetime.strptime(euribor_zero_curve.loc[d, "End Date"], "%d-%b-%y")

zero_curve = euribor_zero_curve["df"]
zero_curve.index = euribor_zero_curve["End Date"]

BGM_fwd_rates.columns = euribor_zero_curve["End Date"][1:-1]
BGM_fwd_rates_one_path = pd.DataFrame(BGM_fwd_rates.iloc[0], index=BGM_fwd_rates.columns)
BGM_fwd_rates_one_path.columns = ["fwd"]

for d in range(len(BGM_fwd_rates_one_path)):
    BGM_fwd_rates_one_path["fwd"][d] = float(BGM_fwd_rates_one_path["fwd"][d].replace(',', '.'))

# ---------------------------------------------------------------------
displacement_beta = 0.0316
BGM_fwd_rates_one_path = BGM_fwd_rates_one_path.add(displacement_beta)

t = datetime.datetime(2020, 1, 1)
S = datetime.datetime(2020, 4, 14)
T = datetime.datetime(2020, 10, 12)
tenor_1 = datetime.datetime(2020, 4, 14)
tenor_2 = datetime.datetime(2021, 10, 11)
delta = dc.yearfrac(BGM_fwd_rates_one_path.index[0], BGM_fwd_rates_one_path.index[1], 'ACTUAL/365 FIXED')
Interpolation_method_object = classBGM_test.BGM(zero_curve, BGM_fwd_rates_one_path, displacement_beta, delta)
# print(Interpolation_method_object.animal_type)
# print(Interpolation_method_object.age)
# print(new_shark.fwd_rates_dataframe)
# print(Interpolation_method_object.zero_curve)
# Interpolation_method_object.set_followers(100)

print('T_q test:', Interpolation_method_object.T_q(t))
print('LI zero curve testL', Interpolation_method_object.df_from_zero_curve_by_LI(t))
print('fwd rate test:', Interpolation_method_object.fwd_rate_on_start_date(S, T))
print('alpha tilde test:', Interpolation_method_object.alpha_tilde(t))
print('f_t test:', Interpolation_method_object.f_t(t))
print('P(t,t_q_t):', Interpolation_method_object.df_from_closest_next_tenor_to_t(t))
print('df_between_tenors test:', Interpolation_method_object.df_between_tenors(tenor_1, tenor_2))

forward_1 = Interpolation_method_object.df_from_T_to_t_BERT(t, T)
forward_2 = Interpolation_method_object.df_from_T_to_t_BERT(t, S)
print('df_from_T_to_t_BERT:', forward_1)


def fwd_rate_proxy(df_1, time_1, df_2, time_2):
    return 1 / dc.yearfrac(time_1, time_2, 'ACTUAL/365 FIXED') * \
           (df_1 / df_2 - 1)


print('Proxy fwd rate:', fwd_rate_proxy(forward_2, S, forward_1, T))
