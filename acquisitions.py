import sys
import os
import urllib.request
from zipfile import ZipFile
import polars as pl
import pandas as pd
import requests
import json


def main():
    dri_energy('data/sources/energy.csv')

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
    # Load standardised nutrient names
    with open("nutrient_names_fda.json") as f:
        nutrient_names_fda = json.load(f)
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
    # Rename all columns to standardised names from nutrient_names_fda.json
    rda.rename(columns=nutrient_names_fda, inplace=True)
    # Convert units: [copper: {UG: MG}, fluoride: {MG: UG}]
    rda['Copper'] = pd.to_numeric(rda['Copper']).div(1000).fillna(0)
    rda['Fluoride'] = pd.to_numeric(rda['Fluoride']).mul(1000).fillna(0)
    # Export rdas to a json file, first by seperating out the index into a nested dictionary.
    rda_dict = fda_to_dict(rda)
    with open("rdas.json", "w", encoding="utf8") as file:
        json.dump(rda_dict, file, ensure_ascii=False)

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
    # Rename all columns to standardised names from nutrient_names_fda.json
    tul.rename(columns=nutrient_names_fda, inplace=True)
    # Convert units: [copper: {UG: MG}, fluoride: {MG: UG}, Phosphorus: {G: MG}]
    tul['Copper'] = pd.to_numeric(tul['Copper']).div(1000).fillna(0)
    tul['Fluoride'] = pd.to_numeric(tul['Fluoride']).mul(1000).fillna(0)
    tul['Phosphorus'] = pd.to_numeric(tul['Phosphorus']).mul(1000).fillna(0)
    # Export tuls to a json file, first by seperating out the index into a nested dictionary.
    tul_dict = fda_to_dict(tul)
    with open("tuls.json", "w", encoding="utf8") as file:
        json.dump(tul_dict, file, ensure_ascii=False)

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


def fda_to_dict(df):
    # turn dataframe into dictionary
    dict = df.to_dict(orient="index")
    # Remove empty keys and convert strings to numbers
    for key, nutrient_requirements in dict.items():
        dict[key] = {
            nutrient: format_number(requirements)
            for nutrient, requirements in nutrient_requirements.items()
            if requirements
        }
    dict_copy = {}
    for key, nutrient_requirements in dict.items():
        age, sex, category = key
        if age not in dict_copy:
            dict_copy[age] = {}
        if sex not in dict_copy[age]:
            dict_copy[age][sex] = {}
        dict_copy[age][sex][category] = nutrient_requirements
    return dict_copy


def energy_to_dict(df):
    # turn dataframe into dictionary
    dict = df.to_dict(orient="index")
    # Remove empty keys and convert strings to numbers
    for key, nutrient_requirements in dict.items():
        dict[key] = {
            nutrient: format_number(requirements)
            for nutrient, requirements in nutrient_requirements.items()
            if requirements
        }
    dict_copy = {}
    for key, nutrient_requirements in dict.items():
        age, sex, category, stage, pal, min_BMI = key
        if age not in dict_copy:
            dict_copy[age] = {}
        if sex not in dict_copy[age]:
            dict_copy[age][sex] = {}
        if category not in dict_copy[age][sex]:
            dict_copy[age][sex][category] = {}
        if stage not in dict_copy[age][sex][category]:
            dict_copy[age][sex][category][stage] = {}
        if pal not in dict_copy[age][sex][category][stage]:
            dict_copy[age][sex][category][stage][pal] = {}
        dict_copy[age][sex][category][stage][pal][min_BMI] = nutrient_requirements
    return dict_copy

def format_number(s):
    try:
        n = float(s)
        if n.is_integer():
            return int(round(n,0))
        else:
            return float(s)
    except ValueError:
        return s


def dri_protein(file):
    # delete and just use the json file
    df = pd.read_csv(file)
    df = df.set_index(["min_age", "gender", "maternity"])
    protein_dict = fda_to_dict(df)
    with open("protein.json", "w", encoding="utf8") as file:
        json.dump(protein_dict, file, ensure_ascii=False)

def dri_energy(file):
    # delete and just use the json file
    df = pd.read_csv(file)
    df = df.set_index(["min_age", "gender", "maternity", "stage", "PAL", "min_BMI"])
    energy_dict = energy_to_dict(df)
    with open("energy.json", "w", encoding="utf8") as file:
        json.dump(energy_dict, file, ensure_ascii=False)

if __name__ == "__main__":
    main()
