# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
import pandas as pd
from os import path
import geopandas
import json


def map_names():
    mapper = dict()
    df = pd.read_csv(
        os.path.join(os.path.dirname(__file__),
                     "./data/India_GeoSadak-zipfile_details.csv"))
    for i in range(28):
        mapper[df.iloc[i]["Facilities"]] = df.iloc[i]["State"]
    return mapper


def map_statvarnames():
    fac_mapper = {
        "Agro": "Count_CivicStructure_AgriculturalFacility",
        "Education": "Count_CivicStructure_EducationFacility",
        "Medical": "Count_CivicStructure_MedicalFacility",
        "Transport/Admin": "Count_CivicStructure_TransportOrAdminFacility"
    }
    return fac_mapper


class GeoSadakLoader:
    COLUMN_HEADERS = [
        "LgdCode",
        "StatVar",
        "Category_Count",
    ]

    def __init__(self, source, state_name):
        self.source = source
        self.state_name = state_name
        self.raw_df = None
        self.clean_df = None

    def load(self, fac_mapper):

        zipfile = "zip:///" + self.source
        fac_state = geopandas.read_file(zipfile)

        state_name = self.state_name

        f = open(
            os.path.join(os.path.dirname(__file__),
                         "./data/India_GeoSadak-lgd_fac_data.json"))
        data = json.load(f)

        lgdCode = []
        for i in data[state_name]:
            fac_id = list(i.keys())[:1][0]
            lgdCode.append(i[fac_id])
        lgdCode = pd.Series(lgdCode)
        fac_state = fac_state.assign(LgdCode=lgdCode.values)

        fac_state = fac_state.groupby(
            ['LgdCode',
             'FAC_CATEGO']).size().to_frame(name='count').reset_index()
        fac_state = fac_state[fac_state["LgdCode"] != '']

        fac_state.loc[fac_state["FAC_CATEGO"] == "Agro",
                      "FAC_CATEGO"] = fac_mapper["Agro"]
        fac_state.loc[fac_state["FAC_CATEGO"] == "Education",
                      "FAC_CATEGO"] = fac_mapper["Education"]
        fac_state.loc[fac_state["FAC_CATEGO"] == "Medical",
                      "FAC_CATEGO"] = fac_mapper["Medical"]
        fac_state.loc[fac_state["FAC_CATEGO"] == "Transport/Admin",
                      "FAC_CATEGO"] = fac_mapper["Transport/Admin"]

        f.close()
        self.raw_df = fac_state

    def _make_column_numerical(self, column):

        if column == "LgdCode":
            self.clean_df[column] = self.clean_df[column].astype(int)

        else:
            self.clean_df[column] = self.clean_df[column].astype(
                str).str.replace(",", "")
            self.clean_df[column] = pd.to_numeric(self.clean_df[column],
                                                  errors="ignore")

    def process(self):

        self.clean_df = self.raw_df

        # Rename columns
        self.clean_df.columns = self.COLUMN_HEADERS

        self._make_column_numerical("LgdCode")
        self._make_column_numerical("Category_Count")

    def save(self, csv_file_path):
        if path.exists(csv_file_path):
            # If the file exists then append to the same
            self.clean_df.to_csv(csv_file_path,
                                 mode='a',
                                 index=False,
                                 header=False)
        else:
            self.clean_df.to_csv(csv_file_path, index=False, header=True)


def main():
    """Runs the program."""

    mapper = map_names()
    fac_mapper = map_statvarnames()

    # If the final csv file already exists
    # Remove it, so that it can be regenerated
    csv_file_path = os.path.join(os.path.dirname(__file__),
                                 "./India_GeoSadak.csv")
    if path.exists(csv_file_path):
        os.remove(csv_file_path)

    files = os.listdir(
        os.path.join(os.path.dirname(__file__), "./data/facilities/"))
    for file_name in files:
        data_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data/facilities/{data_file}".format(data_file=file_name),
        )
        loader = GeoSadakLoader(data_file_path, mapper[file_name])
        loader.load(fac_mapper)
        loader.process()
        loader.save(csv_file_path)


if __name__ == "__main__":
    main()
