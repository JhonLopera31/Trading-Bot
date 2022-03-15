from pandas.core.dtypes.missing import isnull
from pandas.core.indexes.base import Index
from extractor import search_data_files
import pandas as pd
import numpy as np
from pathlib import Path
DEFAULT_DATA_FOLDER = ".results"

def list_data_files(folder_name):

    data_folder = Path.cwd() / folder_name
    print(f'Path: {data_folder} \n')
    data_files = [x for x in data_folder.iterdir()]
    return data_files
    
def read_csv(data_path):
    print(data_path)
    data = pd.read_csv(data_path, sep=',', header=[0], index_col=None)
    return data, data_path.name

def sort_by_time(dataFrame,interval_time,win_group):
    star_time=0
    interval_time_vector=[]
    win_bet=[]
    lose_bet=[]

    for interval in range(1,25,interval_time):
        end_time =star_time+1

        if(interval<=23):
            date_interval=dataFrame.between_time(f'{star_time}:00', f'{end_time}:00')
            interval_time_vector.append(f'{star_time}:00-{end_time}:00')
            star_time+=1

        else:
            date_interval=dataFrame.between_time(f'{star_time}:00', f'{star_time}:59')
            interval_time_vector.append(f'{star_time}:00-{star_time}:59')
            
        
        win_bet.append(len(date_interval[date_interval.n_groups<=win_group]))
        lose_bet.append(len(date_interval[date_interval.n_groups>win_group]))
        
    time_dataframe=pd.DataFrame({"Time":interval_time_vector, "Win_bets":win_bet, "Lose_bets":lose_bet})
    return time_dataframe  

if __name__ == '__main__':

    interval_time = '1m'
    n_groups = 4
    data_path = Path(f'{DEFAULT_DATA_FOLDER}_{interval_time}').joinpath("groups4")
    files_path=list_data_files(data_path)

    for i in range (len(files_path)):

        data,file_name = read_csv(files_path[i])
        n_groups = data.Groups_positive
        time = pd.DatetimeIndex(data.From_positive)
        
        positive_trends = pd.DataFrame({"n_groups": n_groups, "time": time}).set_index('time')
        positive_trends = positive_trends.dropna() #delete null values
        

        n_groups = data.Groups_negative
        time = pd.DatetimeIndex(data.From_negative)
        negative_trends = pd.DataFrame({"n_groups": n_groups, "time": time}).set_index('time')
        negative_trends = negative_trends.dropna() #delete null values

        win_groups=11
        sorted_positive_trends=sort_by_time(positive_trends,1,win_groups)
        sorted_negative_trends=sort_by_time(negative_trends,1,win_groups)

        complete_groups = sorted_positive_trends.join(sorted_negative_trends.drop("Time",axis=1), lsuffix='_positive', rsuffix='_negative')
        print(complete_groups,"\n")

        save_folder=Path(f'{DEFAULT_DATA_FOLDER}_{interval_time}').joinpath("hourly classification")
        save_path = save_folder.joinpath(file_name)

        #print(f'Exporting results in: {save_path} ...')
        if not(save_folder.is_dir()):
            save_folder.mkdir()
        
        #complete_groups.to_csv(save_path, sep=",", index=False)


