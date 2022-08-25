from premium.exception import PremiumException
from premium.logger import logging
from premium.entity.config_entity import DataIngestionConfig
from premium.entity.artifact_entity import DataIngestionArtifact
from sklearn.model_selection import StratifiedShuffleSplit
from premium.constant import *
from six.moves import urllib

import os, sys
import zipfile
import numpy as np
import pandas as pd


class DataIngestion:
    def __init__(self, data_ingestion_config : DataIngestionConfig):
        try:
            logging.info(f"{'='*20} DataIngestion log started. {'='*20}")
            self.data_ingestion_config = data_ingestion_config

        except Exception as e:
            raise PremiumException(e,sys) from e
    

    def download_premium_data(self):
        try:
            download_url = self.data_ingestion_config.dataset_download_url

            zip_download_url = self.data_ingestion_config.zip_download_dir

            os.makedirs(zip_download_url,exist_ok=True)
            premium_file_name = "insurance"

            zip_file_path = os.path.join(zip_download_url, premium_file_name)
            logging.info(f"Downloading file from :[{download_url}] into :[{zip_file_path}]")

            urllib.request.urlretrieve(download_url, zip_file_path)
            logging.info(f"File :[{zip_file_path}] has been downloaded successfully.")
            
            return zip_file_path
        
        except Exception as e:
            raise PremiumException(e,sys) from e


    def extract_zip_file(self, zip_file_path:str):
        try:
            raw_data_dir = self.data_ingestion_config.raw_data_dir
            
            os.makedirs(raw_data_dir, exist_ok=True)

            logging.info(f"Extraction of data started from [{zip_file_path}] into dir :[{raw_data_dir}]")
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(raw_data_dir)

            logging.info(f"Extraction completed")

        except Exception as e:
            raise PremiumException(e,sys) from e


    def split_data_as_train_test(self) -> DataIngestionArtifact:
        try:
            raw_data_dir = self.data_ingestion_config.raw_data_dir
            #file_name = "insurance"
            file_name = os.listdir(raw_data_dir)[0]

            premium_file_path = os.path.join(raw_data_dir, file_name)

            logging.info(f"Reading csv file: [{premium_file_path}]")

            premium_data_frame = pd.read_csv(premium_file_path)

            premium_data_frame["bmi_category"] = pd.cut(
                premium_data_frame["bmi"],
                bins = [0.0, 20.0, 30.0, 40.0, 50.0, np.inf],
                labels = [1,2,3,4,5]
            )

            logging.info(f"Spliting data into train and test")

            strat_train_set = None
            strat_test_set = None

            split = StratifiedShuffleSplit(n_splits=1, test_size = 0.3, random_state=42)

            for train_index,test_index in split.split(premium_data_frame, premium_data_frame["bmi_category"]):
                strat_train_set = premium_data_frame.loc[train_index].drop(["bmi_category"],axis=1)
                strat_test_set = premium_data_frame.loc[test_index].drop(["bmi_category"],axis=1)

            train_file_path = os.path.join(self.data_ingestion_config.ingested_train_dir, file_name)
            test_file_path = os.path.join(self.data_ingestion_config.ingested_test_dir, file_name)

            if strat_train_set is not None:
                os.makedirs(self.data_ingestion_config.ingested_train_dir, exist_ok=True)
                logging.info(f"Exporting training datset to file: [{train_file_path}]")
                strat_train_set.to_csv(train_file_path,index=False)

            if strat_test_set is not None:
                os.makedirs(self.data_ingestion_config.ingested_test_dir, exist_ok= True)
                logging.info(f"Exporting test dataset to file: [{test_file_path}]")
                strat_test_set.to_csv(test_file_path,index=False)

            data_ingestion_artifact = DataIngestionArtifact(
                train_file_path = train_file_path,
                test_file_path = test_file_path,
                is_ingested = True,
                message = f"Data ingestion completed successfully.")

            logging.info(f"Data Ingestion artifact:[{data_ingestion_artifact}]")
            return data_ingestion_artifact

        except Exception as e:
            raise PremiumException(e,sys) from e


    def initiate_data_ingestion(self) -> DataIngestionArtifact:
        try:
            zip_file_path = self.download_premium_data()
            #self.extract_tgz_file(tgz_file_path=tgz_file_path)
            self.extract_zip_file(zip_file_path=zip_file_path)
            return self.split_data_as_train_test()

        except Exception as e:
            raise PremiumException(e,sys) from e

    def __del__(self):
        logging.info(f"{'='*20}Data Ingestion log completed.{'='*20} \n")