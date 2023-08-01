import sys
import os
import shutil
import urllib.request
from zipfile import ZipFile
import polars as pl
import pandas as pd
import requests
import json
from rapidfuzz import fuzz, distance, process, utils
import re
import time
from datetime import timedelta


def main():
    # extract_us_energy_dist()
    # extract_us_nutrient_reqs()
    # download_us_food_nutrients()
    ...


def time_it(func):
    """
    Decorator function to return time taken to execute another function.
    """

    def inner(*args, **kwargs):
        tic = time.perf_counter()
        output = func(*args, **kwargs)
        toc = time.perf_counter()
        delta = toc - tic
        duration = timedelta(seconds=delta)
        print(f"Function {func.__name__} completed in {duration}.")
        return output

    return inner



def download_us_food_nutrients():
    # Create filepath if it does not exist
    if not os.path.exists("data/sources"):
        os.makedirs("data/sources")
    # Download food data files
    urllib.request.urlretrieve(
        "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_survey_food_csv_2022-10-28.zip",
        "data/sources/FoodData_Central_survey_food_csv.zip",
    )
    with ZipFile("data/sources/FoodData_Central_survey_food_csv.zip", "r") as archive:
        archive.extractall("data/sources")
    os.remove("data/sources/FoodData_Central_survey_food_csv.zip")

    urllib.request.urlretrieve(
        "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip",
        "data/sources/FoodData_Central_legacy_food_csv.zip",
    )
    with ZipFile("data/sources/FoodData_Central_legacy_food_csv.zip", "r") as archive:
        archive.extractall("data/sources")
    os.remove("data/sources/FoodData_Central_legacy_food_csv.zip")

    # Read survey food (current) and legacy (more detailed) food data from downloaded files
    survey_food = pl.read_csv(
        "data/sources/FoodData_Central_survey_food_csv_2022-10-28/food.csv"
    ).select(pl.col("fdc_id"), pl.col("description"))
    legacy_food = pl.read_csv(
        "data/sources/FoodData_Central_sr_legacy_food_csv_2018-04/food.csv"
    ).select(pl.col("fdc_id"), pl.col("description"))
    # Use fuzzy matching to find overlapping entries between the 2 datasets
    matched_food = fuzzy_match(
        survey_food["description"],
        legacy_food["description"],
        scorer=fuzz.token_sort_ratio,
        score_cutoff=90,
    )
    # Replace entries in legacy food with matched survey_food entry and remove any resulting duplicates
    legacy_food = legacy_food.with_columns(
        pl.col("description").map_dict(matched_food, default=pl.first())
    ).unique(subset="description")
    # Survey food data
    # Read the nutrient list used in the survey food dataset
    survey_nutrient = (
        pl.read_csv(
            "data/sources/FoodData_Central_survey_food_csv_2022-10-28/nutrient.csv"
        )
        .select(pl.col("nutrient_nbr"), pl.col("name"))
        .rename({"nutrient_nbr": "nutrient_id"})
    )
    # Read the nutrient keys file used by the script to map nutrients in the survey food data
    survey_nutrient_keys = (
        pl.read_csv("data/nutrient_keys.tsv", separator="\t")
        .select(pl.col("name"), pl.col("nutrient_nbr"))
        .rename({"name": "new_name", "nutrient_nbr": "nutrient_id"})
    )
    survey_nutrient_keys = survey_nutrient_keys.with_columns(
        pl.col("nutrient_id").apply(lambda s: json.loads(s))
    ).explode("nutrient_id")
    # Read food to nutrient mapping for survey foods
    survey_food_nutrient = (
        pl.read_csv(
            "data/sources/FoodData_Central_survey_food_csv_2022-10-28/food_nutrient.csv"
        )
        .select(pl.col("fdc_id"), pl.col("nutrient_id"), pl.col("amount"))
        .with_columns(pl.col("nutrient_id").cast(pl.Float64))
    )
    # Create a combined dataframe for the survey food
    survey_food_df = (
        survey_food.join(survey_food_nutrient, on="fdc_id")
        .join(survey_nutrient, on="nutrient_id")
        .with_columns(pl.col("nutrient_id").cast(pl.Int64))
    )
    # EDIT
    survey_food_df = (
        survey_food_df.join(survey_nutrient_keys, on="nutrient_id", how="outer")
        .filter(pl.col("new_name").is_not_null())
        .filter(pl.col("description").is_not_null())
        .select(pl.col("description"), pl.col("amount"), pl.col("new_name"))
        .rename({"description": "food", "new_name": "nutrient"})
        .groupby(["food", "nutrient"])
        .agg(pl.col("amount").sum())
    )

    # Legacy food data
    # Read the nutrient list used in the survey food dataset
    legacy_nutrient = (
        pl.read_csv(
            "data/sources/FoodData_Central_sr_legacy_food_csv_2018-04/nutrient.csv"
        )
        .select(pl.col("id"), pl.col("name"))
        .rename({"id": "nutrient_id"})
    )
    # Read the nutrient keys file used by the script to map nutrients in the legacy food data
    legacy_nutrient_keys = (
        pl.read_csv("data/nutrient_keys.tsv", separator="\t")
        .select(pl.col("name"), pl.col("nutrient_id"))
        .rename({"name": "new_name"})
    )
    legacy_nutrient_keys = legacy_nutrient_keys.with_columns(
        pl.col("nutrient_id").apply(lambda s: json.loads(s))
    ).explode("nutrient_id")
    # Read food to nutrient mapping for legacy foods
    legacy_food_nutrient = (
        pl.read_csv(
            "data/sources/FoodData_Central_sr_legacy_food_csv_2018-04/food_nutrient.csv"
        )
        .select(pl.col("fdc_id"), pl.col("nutrient_id"), pl.col("amount"))
        .with_columns(pl.col("nutrient_id"))
    )
    # Create a combined dataframe for the legacy food
    legacy_food_df = (
        legacy_food.join(legacy_food_nutrient, on="fdc_id")
        .join(legacy_nutrient, on="nutrient_id")
        .with_columns(pl.col("nutrient_id"))
    )

    legacy_food_df = (
        legacy_food_df.join(legacy_nutrient_keys, on="nutrient_id", how="outer")
        .filter(pl.col("new_name").is_not_null())
        .filter(pl.col("description").is_not_null())
        .select(pl.col("description"), pl.col("amount"), pl.col("new_name"))
        .rename({"description": "food", "new_name": "nutrient"})
        .groupby(["food", "nutrient"])
        .agg(pl.col("amount").sum())
    )
    # Create a merged food dataframe from survey and legacy food data
    merged_food_df = survey_food_df.join(
        legacy_food_df, on=["food", "nutrient"], how="outer", suffix="_legacy"
    ).rename({"amount": "amount_survey"})
    merged_food_df = (
        merged_food_df.with_columns(
            pl.when(pl.col("amount_survey").is_null())
            .then(pl.col("amount_legacy"))
            .otherwise(pl.col("amount_survey"))
            .alias("amount")
        )
        .drop("amount_survey", "amount_legacy")
        .pivot(
            values="amount", index="food", columns="nutrient", aggregate_function=None
        )
    )
    # Export food list and dataframe to parquet files
    merged_food_df.select("food").write_parquet("data/sources/food_list.parquet")
    merged_food_df.write_parquet("data/sources/food_nutrients.parquet")
    # Remove downloaded files
    shutil.rmtree("data/sources/FoodData_Central_survey_food_csv_2022-10-28/")
    shutil.rmtree("data/sources/FoodData_Central_sr_legacy_food_csv_2018-04/")


def fuzzy_match(list1, list2, scorer=fuzz.ratio, score_cutoff=90):
    """
    Returns a dictionary of matched pairs from 2 lists.
    Refer to rapidfuzz docs for fuzzy match methods available, and the range of scores that can be outputted for that method (to use in the 'tolerance' argument).
    To reduce processing time, this function creates lists with pre-processed strings instead of using the processor kwarg in the rapidfuzz.process.extractOne method.
    """
    # Preprocess (e.g. remove non-alphabetic characters) of each list and create dictionaries for matching later on.
    list1_strip = []
    list1_key = {}
    list2_strip = []
    list2_key = {}
    for i in list1:
        list1_strip.append(utils.default_process(i))
        list1_key[utils.default_process(i)] = i
    for i in list2:
        list2_strip.append(utils.default_process(i))
        list2_key[utils.default_process(i)] = i
    # For each item in list1 (stripped) find matches that meet
    # the matching score cutoff in list2 (stripped).
    list2_match = []
    for i in list1_strip:
        row = process.extractOne(
            query=i, choices=list2_strip, scorer=scorer, score_cutoff=score_cutoff
        )
        if row:
            list2_match.append(row[0])
    # For each list2 item from the list of matches from list1 to list2
    # find matches that best match back to list1.
    list2_1_match = {}
    for i in list2_match:
        row = process.extractOne(
            query=i, choices=list1_strip, scorer=scorer, score_cutoff=score_cutoff
        )
        if row:
            list2_1_match[i] = row[0]
    # Create a dictionary with the matches using the original (unstripped) strings from each list.
    # Because it is a dictionary, duplicates replace existing values.
    result = {}
    for i in list2_1_match:
        result[list2_key[i]] = list1_key[list2_1_match[i]]

    return result


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
    energy_dist_lower["n-6 linoleic acid"] = energy_dist_lower[
        "n-6 linoleic acid"
    ].apply(lambda x: float(x) * 0.9)
    energy_dist_lower["n-3 a-linolenic Acid (ALA)"] = energy_dist_lower[
        "n-3 a-linolenic Acid (ALA)"
    ].apply(lambda x: float(x) * 0.9)
    energy_dist_upper["n-6 linoleic acid"] = energy_dist_upper[
        "n-6 linoleic acid"
    ].apply(lambda x: float(x) * 0.9)
    energy_dist_upper["n-3 a-linolenic Acid (ALA)"] = energy_dist_upper[
        "n-3 a-linolenic Acid (ALA)"
    ].apply(lambda x: float(x) * 0.9)
    # Export lower and upper ranges to CSVs
    energy_dist_lower.to_csv("data/energy_dist_lower.csv")
    energy_dist_upper.to_csv("data/energy_dist_upper.csv")


if __name__ == "__main__":
    main()
