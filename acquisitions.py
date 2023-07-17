import sys
import os
import urllib.request
from zipfile import ZipFile
import polars as pl
import pandas as pd
import requests
import json


def main():
    ...

def download_fda_nutrients():
    if not os.path.exists("data/sources"):
        os.makedirs("data/sources")
    urllib.request.urlretrieve(
        "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_survey_food_csv_2022-10-28.zip",
        "data/sources/FoodData_Central_survey_food_csv.zip",
    )
    with ZipFile("data/sources/FoodData_Central_survey_food_csv.zip", "r") as archive:
        archive.extractall("data/sources")
    os.remove("data/sources/FoodData_Central_survey_food_csv.zip")


def read_dri_html():
    if not os.path.exists("data"):
        os.makedirs("data")
    # Load standardised nutrient names
    with open("data/nutrient_names_US.json") as f:
        nutrient_names_US = json.load(f)
    # read rdas for minerals, vitamins and macros
    minerals_rda = parse_dri_html(
        "https://www.ncbi.nlm.nih.gov/books/NBK545442/table/appJ_tab3/?report=objectonly"
    )
    vitamins_rda = parse_dri_html(
        "https://www.ncbi.nlm.nih.gov/books/NBK56068/table/summarytables.t2/?report=objectonly"
    )
    # Remove extra characters
    vitamins_rda.rename(
        inplace=True,
        columns={
            "Vitamin A (μg/d)a": "Vitamin A (μg/d)",
            "Vitamin D (μg/d)b,c": "Vitamin D (μg/d)",
            "Vitamin E (mg/d)d": "Vitamin E (mg/d)",
            "Niacin (mg/d)e": "Niacin (mg/d)",
            "Folate (μg/d)f": "Folate (μg/d)",
            "Choline (mg/d)g": "Choline (mg/d)",
        },
    )
    macros_rda = parse_dri_html(
        "https://www.ncbi.nlm.nih.gov/books/NBK56068/table/summarytables.t4/?report=objectonly"
    )
    # Remove extra characters
    macros_rda.rename(
        inplace=True,
        columns={
            "Total Watera (L/d)": "Total Water (L/d)",
            "Proteinb (g/d)": "Protein (g/d)",
        },
    )
    # Combine macros, vitamins and minerals into one dataframe
    rda = macros_rda.join(vitamins_rda).join(minerals_rda)
    # Rename all columns to standardised names from nutrient_names_US.json
    rda.rename(columns=nutrient_names_US, inplace=True)
    # Convert units: [copper: {UG: MG}, fluoride: {MG: UG}]
    rda['Copper'] = pd.to_numeric(rda['Copper']).div(1000).fillna(0)
    rda['Fluoride'] = pd.to_numeric(rda['Fluoride']).mul(1000).fillna(0)
    # Export rdas to a csv.
    rda.replace('',0).to_csv('data/rda.csv', encoding='utf-8-sig')

    # Read total upper limits for vitamins and minerals
    minerals_tul = parse_dri_html(
        "https://www.ncbi.nlm.nih.gov/books/NBK545442/table/appJ_tab9/?report=objectonly"
    )
    # Delete columns with undetermined values, and columns where there are no rdas as well as no data tracked for food.
    minerals_tul.drop(
        inplace=True,
        columns={
            "Arsenica",
            "Boron (mg/d)",
            "Chromium",
            "Nickel (mg/d)",
            "Potassium",
            "Siliconc",
            "Sulfate",
            "Vanadium (mg/d)d",
            "Sodiume",
            "Magnesium (mg/d)b"
        },
    )
    # Remove extra characters and change units
    minerals_tul.rename(
        inplace=True,
        columns={
            "Phosphorus (g/d)": "Phosphorus (mg/d)",
        },
    )
    vitamins_tul = parse_dri_html(
        "https://www.ncbi.nlm.nih.gov/books/NBK56068/table/summarytables.t7/?report=objectonly"
    )
    # Delete columns with undetermined values.
    vitamins_tul.drop(
        inplace=True,
        columns={
            "Vitamin K",
            "Thiamin",
            "Riboflavin",
            "Vitamin B12",
            "Pantothenic Acid",
            "Biotin",
            "Carotenoidsd",
        },
    )
    # Remove extra characters and convert upper limits to nutrient subtypes the limit applies to
    vitamins_tul.rename(
        inplace=True,
        columns={
            "Vitamin A (μg/d)a": "Retinol (μg/d)",
            "Vitamin E (mg/d)b,c": "Vitamin E added (mg/d)",
            "Niacin (mg/d)c": "Niacin added (mg/d)",
            "Folate (μg/d)c": "Folic acid (μg/d)",
        },
    )
    # Combine vitamins and minerals into one dataframe
    tul = vitamins_tul.join(minerals_tul)
    # Rename all columns to standardised names from nutrient_names_US.json
    tul.rename(columns=nutrient_names_US, inplace=True)
    # Convert units: [copper: {UG: MG}, fluoride: {MG: UG}, Phosphorus: {G: MG}]
    tul['Copper'] = pd.to_numeric(tul['Copper']).div(1000).fillna(0)
    tul['Fluoride'] = pd.to_numeric(tul['Fluoride']).mul(1000).fillna(0)
    tul['Phosphorus'] = pd.to_numeric(tul['Phosphorus']).mul(1000).fillna(0)
    # Export tuls to a csv.
    tul.replace('',0).to_csv('data/tul.csv', encoding='utf-8-sig')

    # energy_distribution = pd.read_html(
    #     requests.get(
    #         "https://www.ncbi.nlm.nih.gov/books/NBK56068/table/summarytables.t5/?report=objectonly"
    #     ).content
    # )[0]
    # print(energy_distribution)


def parse_dri_html(url):
    categories = pd.DataFrame(
        {
            "min_age": [
                0,
                0.5,
                1,
                4,
                9,
                14,
                19,
                31,
                51,
                70,
                9,
                14,
                19,
                31,
                51,
                70,
                14,
                19,
                31,
                14,
                19,
                31,
            ],
            "gender": [
                "none",
                "none",
                "none",
                "none",
                "male",
                "male",
                "male",
                "male",
                "male",
                "male",
                "female",
                "female",
                "female",
                "female",
                "female",
                "female",
                "female",
                "female",
                "female",
                "female",
                "female",
                "female",
            ],
            "maternity": [
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "none",
                "pregnant",
                "pregnant",
                "pregnant",
                "breastfeeding",
                "breastfeeding",
                "breastfeeding",
            ],
        }
    )

    drop_rowlist = ["Infants", "Children", "Males", "Females", "Pregnancy", "Lactation"]
    df = (
        pd.read_html(requests.get(url).content, index_col=0)[0]
        .drop(drop_rowlist)
        .replace("[^0-9.]", "", regex=True)
    )
    df = categories.join(df.reset_index(drop=True)).set_index(
        ["min_age", "gender", "maternity"]
    )
    return df



if __name__ == "__main__":
    main()
