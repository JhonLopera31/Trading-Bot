from numpy.core.numeric import ones
import pandas as pd
import numpy as np
from pathlib import Path
from time import time
import warnings
warnings.filterwarnings("ignore")

DEFAULT_DATA_FOLDER = ".raw_data"
DEFAULT_SAVE_FOLDER = ".results"
CLEAN_DATA = False  # set as "True" if the csv files contain weekend data

def search_data_files(folder_name):
    """
    List data files of a given folder path
    """
    data_folder = Path.cwd() / folder_name
    print(f'Path: {data_folder} \n')
    print('Choose a option:')
    data_files = [x for x in data_folder.iterdir()]

    for i, data_file in enumerate(data_files):
        print(f'   {i}: {data_file}')
    option = int(input("option: "))
    print()
    print(f'{option}: {data_files[option]}')
    return data_files[option]

def prepare_csv(data_path):
    """
    Read data, assing the column names and remove weekend data
    """
    columns_name = ['date', 'time', 'Open', 'Max', 'Min', 'Close', "Volume"]
    data = pd.read_csv(data_path, sep=',', header=None, names=columns_name, parse_dates=[[0, 1]])
    data = data.drop(["Volume"], axis=1)

    if (CLEAN_DATA):
        print('\nbefore cleaning:')
        data.info()
        data = data[data.date_time.dt.dayofweek < 5]
        print('\nafter cleaning:')
        data.info()

    return data, data_path.name
              
def correct_labels_including_zeros(df,n_groups):
    df_zeros=(df[df.Group_Label==0])
    print(len(df_zeros))

    for i in range(0,len(df_zeros)):
        
        if df.Group_Label[df_zeros.index[i]]==0 and df_zeros.index[i]>1 and df_zeros.index[i]<len(df):
            index=df_zeros.index[i]
            Group_Label=df.Group_Label[df.index==index-1].values[0]
            groups=df.Group_Label[df.Group_Label==Group_Label]

            if len(groups)>=n_groups:
                next_Group_Label=Group_Label+1
                Trend_before=df.Trend[df.Group_Label==Group_Label].iloc[0]
                Trend_after= df.Trend[df.Group_Label==next_Group_Label].iloc[0]

                if Trend_before==Trend_after:
                    index2=df.index[df.Group_Label==next_Group_Label][-1]
                    df.Trend[df.Group_Label==Group_Label]=Trend_before
                    df.Group_Label[index2:]=df.Group_Label[index2:]-1
                    df.Group_Label[df.Group_Label==-1]=0
                else:
                    index2=df.index[df.Group_Label==next_Group_Label][0]
                    df.Group_Label[index-1:index2-1]=Group_Label
                    df.Trend[df.Group_Label==Group_Label]=Trend_before
    return df


def including_zeros_probable_case(dataFrame,n_groups):
    """This function considers only the case where there is a zero Candle group between positive or negative trends.
    """
    print("Calculating a probable case case")

    # Calculate labels according to slopes changes
    dataFrame["Group_Label"]=((abs(dataFrame.Trend.diff())).cumsum())

    # Delete first row after assing labels
    dataFrame=dataFrame.drop(dataFrame.iloc[[0]].index,axis=0)
    
    #Zero's label is assigned an odd number
    f=dataFrame.pivot_table(index=['Group_Label'], aggfunc='size') #Frequency table by label
    mayor_groups=f.index[f>=n_groups] # Obtain labels with frequencies biggest or equal to 3
    mayor_groups=mayor_groups[np.where(mayor_groups%2==0)].to_numpy()# Obtaining Mayor groups w/o zeros
    
    zeros_labels=f.index[f.index%2!=0].to_numpy() #Obtaining Zero's labels
    label_aux=np.intersect1d(mayor_groups,zeros_labels-1) # Find zeros beside and below de mayor groups
    
    mayor_groups=np.hstack((mayor_groups,(label_aux+1)))
    dataFrame1=dataFrame.loc[dataFrame.Group_Label.isin(mayor_groups)]#.reset_index(drop=True)
    dataFrame1.Group_Label= dataFrame1.Group_Label.apply(lambda x: x - x%2)

    dataFrame1.Trend=dataFrame1.Trend.replace(to_replace=0, method='ffill').values
    dataFrame2=dataFrame.drop(dataFrame1.index.to_list())
    dataFrame_final=pd.concat([dataFrame1, dataFrame2]).sort_index()

    dataFrame_final["Group_Label"]=(abs(dataFrame_final.Trend.diff())).cumsum()
    dataFrame_final.Group_Label=2+dataFrame_final["Group_Label"].where(dataFrame_final.Trend%2!=0, -2)
    dataFrame_final.Group_Label=dataFrame_final.Group_Label/2
    dataFrame_final=dataFrame_final.drop(dataFrame_final.iloc[[0]].index,axis=0)
    return(dataFrame_final)

def group_data_with_zeros_worse_case(dataFrame):
    """
    This function consideres the worse case, which implies that all zero entries can 
    cause a money lose
    """

    print("Calculating worse case")
    dataFrame.Trend=dataFrame.Trend.replace(to_replace=0, method='ffill')
    dataFrame["Group_Label"]=(abs(dataFrame.Trend.diff())).cumsum()
    dataFrame.Group_Label=2+dataFrame["Group_Label"].where(dataFrame.Trend%2!=0, -2)
    dataFrame.Group_Label=dataFrame.Group_Label/2
    dataFrame=dataFrame.drop(dataFrame.iloc[[0]].index,axis=0)
    return dataFrame


def group_data(data,n_groups):
    """
    This function groups sequences of numbers according to their behavior (increasing or decreasing)

    Trend: Assigns -1 or 1 if according with sign of operation Open-Close
              if Open-Close < 0 => Trend = (-1)  
              if Open-Close > 0 => Trend = 1
              if Open-Close == 0 => Trend = 0   
    Group_Label: Assigns a label for each group of consecutive numbers    
    """

    data["Trend"] = (data["Close"]-data["Open"]) / abs(data["Close"]-data["Open"])
    data["Trend"] = data["Trend"].where(~(data["Trend"].isnull()), 0)

    #data=including_zeros_probable_case(data,n_groups)
    data=group_data_with_zeros_worse_case(data)
    # --------- Frequency tables (Positive candles an Negative Candles) ---------
    data["Group_Label"] = data["Group_Label"]*data["Trend"]
    FreqTable = data.pivot_table(index=['Group_Label'], aggfunc='size')  
    FreqTable = FreqTable.drop(FreqTable.index[FreqTable == max(FreqTable)].tolist())
    
    positive_groups= FreqTable[(FreqTable.index >= 0)]
    negative_groups = FreqTable[(FreqTable.index < 0)]

    return data, positive_groups, negative_groups

def group_frequency(Groups):
    p = np.zeros((max(Groups)))
    groups_aux = []
    for i in range(0, max(Groups)):
        p[i] = sum(Groups == i+1)
        groups_aux.append((i+1))
        print(f' p[Group = {i+1}]: {np.round(p[i],4)}')
    Frequencies = pd.DataFrame({"Groups": groups_aux, "Frequencies": p})
    return Frequencies

def groups_with_date(data, grouped_data, n):
    """
    data: Complete data frame is used to extract dates for each group
    grouped_data: Contain the grouped data according with the candles trends
    n: grouping data with frequency greater than n
    """
    n_groups = grouped_data[grouped_data >= n]
    some_values=grouped_data.index[grouped_data >= n].to_list()
    data=data.loc[data.Group_Label.isin(some_values)]
    data=data.drop_duplicates(subset=['Group_Label']) 

    df=pd.DataFrame({"n_groups": n_groups.to_list(), "date": data.date_time})
    df=df.reset_index(drop=True)
    return df

if __name__ == '__main__':
    interval_time = '1m'
    n_groups = 3
    
    star_time = time()

    data_path = f'{DEFAULT_DATA_FOLDER}_{interval_time}'
    data_path = search_data_files(data_path)
    data, file_name = prepare_csv(data_path)

    save_folder = Path(f'{DEFAULT_SAVE_FOLDER}_{interval_time}')
    save_path = Path(f'{DEFAULT_SAVE_FOLDER}_{interval_time}').joinpath(file_name)

    data, positive_groups, negative_groups = group_data(data,n_groups)
    
    #------------------ Calculating data's frequencies --------------------
    print("Frequency table -> Positive candles")
    positive_freq=group_frequency(positive_groups)
    print("")
    
    print("Frequency table -> Negative candles")
    negative_freq=group_frequency(negative_groups)
    print("")
    freq_groups = positive_freq.join(negative_freq, lsuffix='_positive', rsuffix='_negative')
    
    positive_groups = groups_with_date(data, positive_groups, n_groups)
    negative_groups = groups_with_date(data, negative_groups, n_groups)
    
    complete_groups = positive_groups.join(negative_groups, lsuffix='_positive', rsuffix='_negative')

    complete_groups=complete_groups.join(freq_groups)

    print(f'Exporting results in: {save_path} ...')
    if not(save_folder.is_dir()):
        save_folder.mkdir()

    #complete_groups.to_csv(save_path, sep=",", index=False)

    print(f'Elapsed time: {time()-star_time} s')
