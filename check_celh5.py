import os, sys
sys.path.insert(0, "src/value/tanuki_valuation")
import inspect
from data_fetcher import TanukiDataFetcher
print(inspect.getsource(TanukiDataFetcher._calc_fcf_2yr_avg))
