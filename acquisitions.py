import sys
import os
import urllib.request
from zipfile import ZipFile
import polars as pl
import pandas as pd
import requests
import json


def main():
    extract_us_energy_dist()
    extract_us_nutrient_reqs()


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


def extract_us_nutrient_reqs():
    """
    Function to download recommended dietary allowances and tolerable upper limits for nutrients issued by the US Food and Nutrition Board.
    Link: https://ods.od.nih.gov/HealthInformation/nutrientrecommendations.aspx.
    """

    # helper function to extract and format table from html
    def parse_html(url):
        categories = pd.DataFrame(
            {
                "min_age": [
                    "0",
                    "0.5",
                    "1",
                    "4",
                    "9",
                    "14",
                    "19",
                    "31",
                    "51",
                    "70",
                    "9",
                    "14",
                    "19",
                    "31",
                    "51",
                    "70",
                    "14",
                    "19",
                    "31",
                    "14",
                    "19",
                    "31",
                ],
                "sex": [
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

        drop_rowlist = [
            "Infants",
            "Children",
            "Males",
            "Females",
            "Pregnancy",
            "Lactation",
        ]
        df = (
            pd.read_html(requests.get(url).content, index_col=0)[0]
            .drop(drop_rowlist)
            .replace("[^0-9.]", "", regex=True)
        )
        df = categories.join(df.reset_index(drop=True)).set_index(
            ["min_age", "sex", "maternity"]
        )
        return df

    # Create data folder if it does not exist
    if not os.path.exists("data"):
        os.makedirs("data")
    # Load standardised nutrient names
    with open("data/nutrient_names_US.json") as f:
        nutrient_names_US = json.load(f)
    # read rdas for minerals, vitamins and macros
    minerals_rda = parse_html(
        "https://www.ncbi.nlm.nih.gov/books/NBK545442/table/appJ_tab3/?report=objectonly"
    )
    vitamins_rda = parse_html(
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
    macros_rda = parse_html(
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
    rda["Copper"] = pd.to_numeric(rda["Copper"]).div(1000).fillna(0)
    rda["Fluoride"] = pd.to_numeric(rda["Fluoride"]).mul(1000).fillna(0)
    # Duplicate where 'sex' is 'none' to 'male' and 'female'.
    rda_none = rda.loc[pd.IndexSlice[:, "none"], :]
    rda_male = rda_none.copy()
    rda_male.index = rda_male.index.set_levels(["1", "2", "male"], level="sex")
    rda_female = rda_none.copy()
    rda_female.index = rda_female.index.set_levels(["1", "2", "female"], level="sex")
    rda_not_none = rda.loc[pd.IndexSlice[:, ["male", "female"]], :]
    rda_new = pd.concat([rda_not_none, rda_male, rda_female])
    # Export rdas to a csv.
    rda_new.replace("", 0).to_csv("data/rda.csv")

    # Read total upper limits for vitamins and minerals
    minerals_tul = parse_html(
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
            "Magnesium (mg/d)b",
        },
    )
    # Remove extra characters and change units
    minerals_tul.rename(
        inplace=True,
        columns={
            "Phosphorus (g/d)": "Phosphorus (mg/d)",
        },
    )
    vitamins_tul = parse_html(
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
    tul["Copper"] = pd.to_numeric(tul["Copper"]).div(1000).fillna(0)
    tul["Fluoride"] = pd.to_numeric(tul["Fluoride"]).mul(1000).fillna(0)
    tul["Phosphorus"] = pd.to_numeric(tul["Phosphorus"]).mul(1000).fillna(0)
    # Add Sodium limits from Appendix J, of
    # Dietary Reference Intakes for Sodium and Potassium (2019),
    # https://www.ncbi.nlm.nih.gov/books/NBK538102/pdf/Bookshelf_NBK538102.pdf.
    sodium = pd.DataFrame(
        {
            "min_age": [
                "0",
                "0.5",
                "1",
                "4",
                "9",
                "14",
                "19",
                "31",
                "51",
                "70",
            ],
            "Sodium": [
                "",
                "",
                1200,
                1500,
                1800,
                2300,
                2300,
                2300,
                2300,
                2300,
            ],
        }
    )
    tul = (
        tul.reset_index()
        .merge(sodium, on="min_age", how="left")
        .set_index(["min_age", "sex", "maternity"])
    )
    # Duplicate where 'sex' is 'none' to 'male' and 'female'.
    tul_none = tul.loc[pd.IndexSlice[:, "none"], :]
    tul_male = tul_none.copy()
    tul_male.index = tul_male.index.set_levels(["1", "2", "male"], level="sex")
    tul_female = tul_none.copy()
    tul_female.index = tul_female.index.set_levels(["1", "2", "female"], level="sex")
    tul_not_none = tul.loc[pd.IndexSlice[:, ["male", "female"]], :]
    tul_new = pd.concat([tul_not_none, tul_male, tul_female])
    # Export tuls to a csv.
    tul_new.to_csv("data/tul.csv")


def extract_us_energy_dist():
    """
    Function creates CSV files for lower and upper ranges for energy distribution between fats, carbohydrates and proteins in percentages.
    """
    # Add data folder if it does not exist
    if not os.path.exists("data"):
        os.makedirs("data")
    # Create an index column to later merge with the table read from the html page
    index_col = pd.DataFrame(
        {
            "min_age": [
                "0",
                "1",
                "4",
                "19",
            ]
        }
    )
    # Get energy distribution table from html page
    energy_distribution = (
        pd.read_html(
            requests.get(
                "https://www.ncbi.nlm.nih.gov/books/NBK56068/table/summarytables.t5/?report=objectonly"
            ).content
        )[0]
        .transpose()
        .reset_index(drop=True)
    )
    # Set 1st row as headers
    energy_distribution.columns = energy_distribution.iloc[0]
    energy_distribution = energy_distribution[1:]
    # Add index column for min_age
    energy_distribution = index_col.join(energy_distribution).set_index("min_age")
    # remove blank column
    energy_distribution = energy_distribution[1:]
    # Rename nutrients to standardised names
    energy_distribution.rename(
        inplace=True,
        columns={
            "Fat": "Total Fat",
            "n-6 polyunsaturated fatty acidsa (linoleic acid)": "n-6 linoleic acid",
            "n-3 polyunsaturated fatty acidsa (α-linolenic acid)": "n-3 a-linolenic Acid (ALA)",
            "Carbohydrate": "Total Carbohydrates",
            "Protein": "Total Protein",
        },
    )

    # Add Long-chain Poly-Unsaturated Fat (LC-PUFAs) requirement of 10% of n-3 and n-6 fatty acids
    energy_distribution["LC-PUFAs"] = "0.56–1.12"


    # Function to extract part of each string to left (n = 0), or right (n = 1) of '-'.
    def extract_part(s, n):
        return s.split("–")[n]

    # Seperate upper and lower ranges into two dataframes
    energy_dist_lower = energy_distribution.applymap(extract_part, n=0)
    energy_dist_upper = energy_distribution.applymap(extract_part, n=1)
    # Multiply n-3 and n-6 fats by 90% to account for 10% attributed to LC-PUFAs.
    energy_dist_lower["n-6 linoleic acid"] = energy_dist_lower["n-6 linoleic acid"].apply(lambda x: float(x) *0.9)
    energy_dist_lower["n-3 a-linolenic Acid (ALA)"] = energy_dist_lower["n-3 a-linolenic Acid (ALA)"].apply(lambda x: float(x) *0.9)
    energy_dist_upper["n-6 linoleic acid"] = energy_dist_upper["n-6 linoleic acid"].apply(lambda x: float(x) *0.9)
    energy_dist_upper["n-3 a-linolenic Acid (ALA)"] = energy_dist_upper["n-3 a-linolenic Acid (ALA)"].apply(lambda x: float(x) *0.9)
    # Export lower and upper ranges to CSVs
    energy_dist_lower.to_csv("data/energy_dist_lower.csv")
    energy_dist_upper.to_csv("data/energy_dist_upper.csv")


if __name__ == "__main__":
    main()
