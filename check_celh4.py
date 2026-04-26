import os, sys
sys.path.insert(0, "src/value/tanuki_valuation")
from data_fetcher import TanukiDataFetcher
df = TanukiDataFetcher.__new__(TanukiDataFetcher)
fcf_list = [323375000, 239569000, 123829000, 99981000, -99642592]
result = df._calc_fcf_2yr_avg(fcf_list)
print("result:", result)
print("expected:", (323375000 + 239569000) / 2)
