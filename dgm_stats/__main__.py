import collections
import logging
import os

import dgm_stats as ds
import pandas as pd

import dotenv

dotenv.load_dotenv()

if __name__ == '__main__':
    ds.initialize_logging(logging.DEBUG)

    api = ds.Api("https://discgolfmetrix.com/api.php", os.environ["DGM_CODE"])
    result = api.get_competition(2064106)

    # results = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict)))
    results = collections.defaultdict(lambda: collections.defaultdict(dict))

    user_results = collections.defaultdict(dict)

    for w_i, weekly_competition in enumerate(result["Competition"]["SubCompetitions"]):
        for s_i, sub_competition in enumerate(weekly_competition["SubCompetitions"]):
            for u_i, user_result in enumerate(sub_competition["Results"]):
                for h_i, hole in enumerate(user_result["PlayerResults"]):
                    if not hole:
                        continue
                    # results[weekly_competition["Name"]][sub_competition["Name"]][user_result["Name"]][i] = hole["Diff"]
                    # results[weekly_competition["Name"]][user_result["Name"]][i] = hole["Diff"]
                    user_results[user_result["Name"]][f"{w_i:02}{h_i:02}"] = hole["Diff"]



    # all_series = []
    # for user in result["Competition"]["Results"]:
    #     series = pd.DataFrame(user["PlayerResults"])["Diff"]
    #     series.name = user["Name"]
    #     series.index = range(1, 19)
    #     #series["Total"] = series.sum()
    #     all_series.append(series)
    #     #UserResult(user["Name"], user["ClassName"], int(user["Group"]), series)
    # df = pd.DataFrame(all_series)




