from datetime import date
import uuid
from math import floor
import re
import csv
import json


class Person:
    def __init__(
        self,
        name,
        dob,
        sex,
        height,
        weight,
        due_date=None,
        breastfeeding=None,
        pal=None,
        desired_weight=None,
        desired_bmi=None,
    ):
        self.name = name
        self.dob = dob
        self.sex = sex
        self.height = height
        self.weight = weight
        self.due_date = due_date
        self.breastfeeding = breastfeeding
        self.pal = pal
        self.desired_weight = desired_weight
        self.desired_bmi = desired_bmi
        # Add unique user id. check if it's already taken (check against user file once established)
        uid = uuid.uuid1()
        if uid not in []:
            self.uid = uid

    def __str__(self):
        if self.due_date:
            return f"{self.name}, {self.sex}, aged {self.age_rounded}, currently {self.gestation} weeks pregnant in trimester {self.trimester}."
        elif self.breastfeeding == 1:
            return f"{self.name}, {self.sex}, aged {self.age_rounded} currently into 1st 6 months of breastfeeding."
        elif self.breastfeeding == 2:
            return f"{self.name}, {self.sex}, aged {self.age_rounded} currently breastfeeding, more than 6 months in."
        else:
            return f"{self.name}, {self.sex}, aged {self.age_rounded}."

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        name = name.strip().title()
        if not name:
            raise ValueError("Must provide the person's username.")
        # Check against stored file/db with usernames
        if name in []:
            raise ValueError("Username must be unique")
        self._name = name

    @property
    def dob(self):
        return self._dob

    @dob.setter
    def dob(self, dob):
        if not dob:
            raise ValueError("Must provide a date of birth")
        dob = re.sub(r"[^0-9\-]", "", dob)
        try:
            date.fromisoformat(dob)
        except:
            raise ValueError("Must provide date of birth in the isoformat: yyyy-mm-dd")
        if date.fromisoformat(dob) > date.today():
            raise ValueError("Must provide a date from the past")
        self._dob = dob

    @property
    def age(self):
        delta = date.today() - date.fromisoformat(self.dob)
        return delta.days / 365

    @property
    def age_rounded(self):
        if self.age < 1:
            return floor(self.age * 100) / 100
        else:
            return floor(self.age)

    @property
    def sex(self):
        return self._sex

    @sex.setter
    def sex(self, sex):
        sex = sex.strip().lower()
        if not sex:
            raise ValueError("Must provide the person's sex.")
        if sex in ["male", "m"]:
            sex = "male"
        elif sex in ["female", "f"]:
            sex = "female"
        else:
            raise ValueError("Provide 'm', 'male', 'f', or 'female'")
        self._sex = sex

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, height):
        try:
            height = float(re.sub(r"[^0-9.]", "", height))
        except:
            raise ValueError("Provide a number for height in cm")
        if height > 0:
            self._height = height
        else:
            raise ValueError("Provide a number greater than 0 for height in cm")

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, weight):
        try:
            weight = float(re.sub(r"[^0-9.]", "", weight))
        except:
            raise ValueError("Provide a number for weight in kg")
        if weight > 0:
            self._weight = weight
        else:
            raise ValueError("Provide a number greater than 0 for weight in kg")

    @property
    def bmi(self):
        return self.weight / ((self.height / 100) ** 2)

    @property
    def due_date(self):
        return self._due_date

    @due_date.setter
    def due_date(self, due_date):
        if due_date:
            due_date = re.sub(r"[^0-9\-]", "", due_date)
            try:
                date.fromisoformat(due_date)
            except:
                raise ValueError("Must provide due date in the isoformat: yyyy-mm-dd")
            if date.fromisoformat(due_date) < date.today():
                due_date = None
            self._due_date = date.fromisoformat(due_date)
        else:
            self._due_date = None

    @property
    def gestation(self):
        if self.due_date:
            days_left = self.due_date - date.today()
            print(date.today())
            week = 1 + (280 - days_left.days) // 7
            return week
        else:
            return None

    @property
    def trimester(self):
        if self.gestation > 28:
            return 3
        elif self.gestation > 12:
            return 2
        elif self.gestation > 0:
            return 1
        else:
            return None

    @property
    def breastfeeding(self):
        return self._breastfeeding

    @breastfeeding.setter
    def breastfeeding(self, breastfeeding):
        if breastfeeding:
            if breastfeeding not in [1, 2]:
                raise ValueError(
                    "Use 1 to indicate breastfeeding within 1st 6 months, use 2 to indicate breastfeeding after."
                )
        self._breastfeeding = breastfeeding

    @property
    def pal(self):
        return self._pal

    @pal.setter
    def pal(self, pal):
        pal = pal.strip().lower()
        if not pal:
            raise ValueError("Must provide the person's physical activity level.")
        if pal in [1, "1", "inactive"]:
            pal = "Inactive"
        elif pal in [2, "2", "low active"]:
            pal = "Low active"
        elif pal in [3, "3", "active"]:
            pal = "Active"
        elif pal in [4, "4", "very active"]:
            pal = "Very active"
        else:
            raise ValueError(
                "Provide activity level as number (1 to 4) or text. e.g. 1, or 'Inactive'."
            )
        self._pal = pal

    @property
    def diet_rqmts(self):
        def float_to_str(n):
            if n.is_integer():
                return str(int(n))
            else:
                return str(n)

        def str_to_float(s):
            try:
                return float(s)
            except (ValueError, TypeError):
                return 0

        def kcal():
            dct = {}
            min_ages = []
            min_BMIs = []
            with open("data/energy.csv") as csvfile:
                data_headers = list(csv.reader(csvfile))[0]
                remove_headers = [
                    "min_age",
                    "sex",
                    "maternity",
                    "stage",
                    "PAL",
                    "min_BMI",
                ]
                for i in remove_headers:
                    data_headers.remove(i)
            with open("data/energy.csv") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row["min_age"] not in dct:
                        dct[row["min_age"]] = {}
                    if row["sex"] not in dct[row["min_age"]]:
                        dct[row["min_age"]][row["sex"]] = {}
                    if row["maternity"] not in dct[row["min_age"]][row["sex"]]:
                        dct[row["min_age"]][row["sex"]][row["maternity"]] = {}
                    if (
                        row["stage"]
                        not in dct[row["min_age"]][row["sex"]][row["maternity"]]
                    ):
                        dct[row["min_age"]][row["sex"]][row["maternity"]][
                            row["stage"]
                        ] = {}
                    if (
                        row["PAL"]
                        not in dct[row["min_age"]][row["sex"]][row["maternity"]][
                            row["stage"]
                        ]
                    ):
                        dct[row["min_age"]][row["sex"]][row["maternity"]][row["stage"]][
                            row["PAL"]
                        ] = {}
                    if (
                        row["min_BMI"]
                        not in dct[row["min_age"]][row["sex"]][row["maternity"]][
                            row["stage"]
                        ][row["PAL"]]
                    ):
                        dct[row["min_age"]][row["sex"]][row["maternity"]][row["stage"]][
                            row["PAL"]
                        ][row["min_BMI"]] = {}
                    dct[row["min_age"]][row["sex"]][row["maternity"]][row["stage"]][
                        row["PAL"]
                    ][row["min_BMI"]] = {i: str_to_float(row[i]) for i in data_headers}
                    if str_to_float(row["min_age"]) not in min_ages:
                        min_ages.append(str_to_float(row["min_age"]))
                    if row["min_BMI"] != "none":
                        if str_to_float(row["min_BMI"]) not in min_BMIs:
                            min_BMIs.append(str_to_float(row["min_BMI"]))
            min_age = float_to_str(max(age for age in min_ages if age < self.age))
            sex = self.sex
            if self.due_date:
                maternity = "pregnant"
                stage = str(self.trimester)
                if self.trimester > 1:
                    if self.desired_bmi:
                        min_BMI = str(
                            max(bmi for bmi in min_BMIs if bmi < self.desired_bmi)
                        )
                    elif self.bmi:
                        min_BMI = str(max(bmi for bmi in min_BMIs if bmi < self.bmi))
                    else:
                        min_BMI = "none"
            elif self.breastfeeding:
                maternity = "breastfeeding"
                stage = str(self.breastfeeding)
                min_BMI = "none"
            else:
                maternity = "none"
                stage = "none"
                min_BMI = "none"
            pal = self.pal
            constant = dct[min_age][sex][maternity][stage][pal][min_BMI]["constant"]
            age_param = dct[min_age][sex][maternity][stage][pal][min_BMI]["age_param"]
            height_param = dct[min_age][sex][maternity][stage][pal][min_BMI][
                "height_param"
            ]
            weight_param = dct[min_age][sex][maternity][stage][pal][min_BMI][
                "weight_param"
            ]
            growth_cost = dct[min_age][sex][maternity][stage][pal][min_BMI][
                "growth_cost"
            ]
            gestation_param = dct[min_age][sex][maternity][stage][pal][min_BMI][
                "gestation_param"
            ]
            energy_deposition = dct[min_age][sex][maternity][stage][pal][min_BMI][
                "energy_deposition"
            ]
            milk_production = dct[min_age][sex][maternity][stage][pal][min_BMI][
                "milk_production"
            ]
            energy_mobilization = dct[min_age][sex][maternity][stage][pal][min_BMI][
                "energy_mobilization"
            ]
            if self.desired_weight:
                weight = self.desired_weight
            else:
                weight = self.weight
            if self.gestation:
                gestation = self.gestation
            else:
                gestation = 0
            kcal = (
                constant
                + (age_param * self.age)
                + (height_param * self.height)
                + (weight_param * weight)
                + growth_cost
                + (gestation_param * gestation)
                + energy_deposition
                + milk_production
                + energy_mobilization
            )
            return kcal

        def rda():
            dct = {}
            min_ages = []
            with open("data/rda.csv") as csvfile:
                data_headers = list(csv.reader(csvfile))[0]
                remove_headers = ["min_age", "sex", "maternity"]
                for i in remove_headers:
                    data_headers.remove(i)
            with open("data/rda.csv") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row["min_age"] not in dct:
                        dct[row["min_age"]] = {}
                    if row["sex"] not in dct[row["min_age"]]:
                        dct[row["min_age"]][row["sex"]] = {}
                    if row["maternity"] not in dct[row["min_age"]][row["sex"]]:
                        dct[row["min_age"]][row["sex"]][row["maternity"]] = {}
                    dct[row["min_age"]][row["sex"]][row["maternity"]] = {
                        i: str_to_float(row[i]) for i in data_headers
                    }
                    if str_to_float(row["min_age"]) not in min_ages:
                        min_ages.append(str_to_float(row["min_age"]))
            min_age = float_to_str(max(age for age in min_ages if age < self.age))
            sex = self.sex
            if self.due_date:
                maternity = "pregnant"
            elif self.breastfeeding:
                maternity = "breastfeeding"
            else:
                maternity = "none"
            rda = dct[min_age][sex][maternity]
            return rda

        def tul():
            dct = {}
            min_ages = []
            with open("data/tul.csv") as csvfile:
                data_headers = list(csv.reader(csvfile))[0]
                remove_headers = ["min_age", "sex", "maternity"]
                for i in remove_headers:
                    data_headers.remove(i)
            with open("data/tul.csv") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row["min_age"] not in dct:
                        dct[row["min_age"]] = {}
                    if row["sex"] not in dct[row["min_age"]]:
                        dct[row["min_age"]][row["sex"]] = {}
                    if row["maternity"] not in dct[row["min_age"]][row["sex"]]:
                        dct[row["min_age"]][row["sex"]][row["maternity"]] = {}
                    dct[row["min_age"]][row["sex"]][row["maternity"]] = {
                        i: str_to_float(row[i]) for i in data_headers
                    }
                    if str_to_float(row["min_age"]) not in min_ages:
                        min_ages.append(str_to_float(row["min_age"]))
            min_age = float_to_str(max(age for age in min_ages if age < self.age))
            sex = self.sex
            if self.due_date:
                maternity = "pregnant"
            elif self.breastfeeding:
                maternity = "breastfeeding"
            else:
                maternity = "none"
            tul = dct[min_age][sex][maternity]
            return tul

        def proteins():
            dct = {}
            min_ages = []
            if self.desired_weight:
                weight = float(self.desired_weight)
            else:
                weight = float(self.weight)
            with open("data/proteins.csv") as csvfile:
                data_headers = list(csv.reader(csvfile))[0]
                remove_headers = ["min_age", "sex", "maternity"]
                for i in remove_headers:
                    data_headers.remove(i)
            with open("data/proteins.csv") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row["min_age"] not in dct:
                        dct[row["min_age"]] = {}
                    if row["sex"] not in dct[row["min_age"]]:
                        dct[row["min_age"]][row["sex"]] = {}
                    if row["maternity"] not in dct[row["min_age"]][row["sex"]]:
                        dct[row["min_age"]][row["sex"]][row["maternity"]] = {}
                    dct[row["min_age"]][row["sex"]][row["maternity"]] = {
                        i: str_to_float(row[i]) * weight for i in data_headers
                    }
                    if str_to_float(row["min_age"]) not in min_ages:
                        min_ages.append(str_to_float(row["min_age"]))
            min_age = float_to_str(max(age for age in min_ages if age < self.age))
            sex = self.sex
            if self.due_date:
                maternity = "pregnant"
            elif self.breastfeeding:
                maternity = "breastfeeding"
            else:
                maternity = "none"
            proteins = dct[min_age][sex][maternity]
            return proteins

        kcal = kcal()

        def energy_upper():
            dct = {}
            min_ages = []
            kcal_to_gram = {}
            with open("data/kcal_per_gram.csv") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    kcal_to_gram[row["name"]] = str_to_float(row["kcal/g"])
            with open("data/energy_dist_upper.csv") as csvfile:
                data_headers = list(csv.reader(csvfile))[0]
                data_headers.remove("min_age")
            with open("data/energy_dist_upper.csv") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row["min_age"] not in dct:
                        dct[row["min_age"]] = {}
                    dct[row["min_age"]] = {
                        "Total Fat": (str_to_float(row["Total Fat"]) / 100)
                        * kcal
                        / kcal_to_gram["Total Fat"],
                        "n-6 linoleic acid": (
                            str_to_float(row["n-6 linoleic acid"]) / 100
                        )
                        * kcal
                        / kcal_to_gram["Total Fat"],
                        "n-3 a-linolenic Acid (ALA)": (
                            str_to_float(row["n-3 a-linolenic Acid (ALA)"]) / 100
                        )
                        * kcal
                        / kcal_to_gram["Total Fat"],
                        "Total Carbohydrates": (
                            str_to_float(row["Total Carbohydrates"]) / 100
                        )
                        * kcal
                        / kcal_to_gram["Total Carbohydrates"],
                        "Total Protein": (str_to_float(row["Total Protein"]) / 100)
                        * kcal
                        / kcal_to_gram["Total Protein"],
                        "LC-PUFAs": (str_to_float(row["LC-PUFAs"]) / 100)
                        * kcal
                        / kcal_to_gram["Total Fat"],
                    }
                    if str_to_float(row["min_age"]) not in min_ages:
                        min_ages.append(str_to_float(row["min_age"]))
            min_age = float_to_str(max(age for age in min_ages if age < self.age))

            energy_upper = dct[min_age]
            return energy_upper

        def energy_lower():
            dct = {}
            min_ages = []
            kcal_to_gram = {}
            with open("data/kcal_per_gram.csv") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    kcal_to_gram[row["name"]] = str_to_float(row["kcal/g"])
            with open("data/energy_dist_lower.csv") as csvfile:
                data_headers = list(csv.reader(csvfile))[0]
                data_headers.remove("min_age")
            with open("data/energy_dist_lower.csv") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row["min_age"] not in dct:
                        dct[row["min_age"]] = {}
                    dct[row["min_age"]] = {
                        "Total Fat": (str_to_float(row["Total Fat"]) / 100)
                        * kcal
                        / kcal_to_gram["Total Fat"],
                        "n-6 linoleic acid": (
                            str_to_float(row["n-6 linoleic acid"]) / 100
                        )
                        * kcal
                        / kcal_to_gram["Total Fat"],
                        "n-3 a-linolenic Acid (ALA)": (
                            str_to_float(row["n-3 a-linolenic Acid (ALA)"]) / 100
                        )
                        * kcal
                        / kcal_to_gram["Total Fat"],
                        "Total Carbohydrates": (
                            str_to_float(row["Total Carbohydrates"]) / 100
                        )
                        * kcal
                        / kcal_to_gram["Total Carbohydrates"],
                        "Total Protein": (str_to_float(row["Total Protein"]) / 100)
                        * kcal
                        / kcal_to_gram["Total Protein"],
                        "LC-PUFAs": (str_to_float(row["LC-PUFAs"]) / 100)
                        * kcal
                        / kcal_to_gram["Total Fat"],
                    }
                    if str_to_float(row["min_age"]) not in min_ages:
                        min_ages.append(str_to_float(row["min_age"]))
            min_age = float_to_str(max(age for age in min_ages if age < self.age))

            energy_lower = dct[min_age]
            return energy_lower

        dct = {}
        rda = rda()
        tul = tul()
        proteins = proteins()
        energy_lower = energy_lower()
        energy_upper = energy_upper()

        with open("data/nutrient_keys.tsv") as tsvfile:
            reader = csv.DictReader(tsvfile, dialect="excel-tab")
            for row in reader:
                if row["name"] not in dct:
                    dct[row["name"]] = {}
                dct[row["name"]]["unit"] = row["unit"]
                dct[row["name"]]["nutrient_nbr"] = json.loads(row["nutrient_nbr"])
                dct[row["name"]]["nutrient_id"] = json.loads(row["nutrient_id"])
                dct[row["name"]]["amount_lower"] = None
                dct[row["name"]]["amount_upper"] = None
                dct[row["name"]]["amount_tul"] = None
                if row["name"] in rda:
                    dct[row["name"]]["amount_lower"] = rda[row["name"]]
                    dct[row["name"]]["amount_upper"] = rda[row["name"]]
                if row["name"] in tul:
                    dct[row["name"]]["amount_tul"] = tul[row["name"]]
                if row["name"] in proteins:
                    dct[row["name"]]["amount_lower"] = proteins[row["name"]]
                    dct[row["name"]]["amount_upper"] = proteins[row["name"]]

        dct["Energy"]["amount_lower"] = kcal
        dct["Energy"]["amount_upper"] = kcal
        dct["Total Fat"]["amount_lower"] = max(
            energy_lower["Total Fat"], rda["Total Fat"]
        )
        dct["Total Fat"]["amount_upper"] = max(
            energy_upper["Total Fat"], rda["Total Fat"]
        )
        dct["n-6 linoleic acid"]["amount_lower"] = max(
            energy_lower["n-6 linoleic acid"], rda["n-6 linoleic acid"]
        )
        dct["n-6 linoleic acid"]["amount_upper"] = max(
            energy_upper["n-6 linoleic acid"], rda["n-6 linoleic acid"]
        )
        dct["n-3 a-linolenic Acid (ALA)"]["amount_lower"] = max(
            energy_lower["n-3 a-linolenic Acid (ALA)"],
            rda["n-3 a-linolenic Acid (ALA)"],
        )
        dct["n-3 a-linolenic Acid (ALA)"]["amount_upper"] = max(
            energy_upper["n-3 a-linolenic Acid (ALA)"],
            rda["n-3 a-linolenic Acid (ALA)"],
        )
        dct["Total Carbohydrates"]["amount_lower"] = max(
            energy_lower["Total Carbohydrates"], rda["Total Carbohydrates"]
        )
        dct["Total Carbohydrates"]["amount_upper"] = max(
            energy_upper["Total Carbohydrates"], rda["Total Carbohydrates"]
        )
        dct["Total Protein"]["amount_lower"] = max(
            energy_lower["Total Protein"], proteins["Total Protein"]
        )
        dct["Total Protein"]["amount_upper"] = max(
            energy_upper["Total Protein"],
            rda["Total Protein"],
            proteins["Total Protein"],
        )
        dct["LC-PUFAs"]["amount_lower"] = energy_lower["LC-PUFAs"]
        dct["LC-PUFAs"]["amount_upper"] = energy_upper["LC-PUFAs"]

        return dct

    @classmethod
    def get(cls):
        due_date = None
        breastfeeding = None
        due_date = None
        name = input("Username: ")
        dob = input("Date of birth (in the isoformat: yyyy-mm-dd): ")
        sex = input("Sex (male or female): ")
        if sex.strip().lower() in ["f", "female"]:
            check_pregnant = input("Are you pregnant (y/n): ")
            if check_pregnant.strip().lower() in ["y", "yes"]:
                due_date = input("Due date (in the isoformat: yyyy-mm-dd): ")
            else:
                check_breastfeeding = input("Are you breastfeeding (y/n): ")
                if check_breastfeeding.strip().lower() in ["y", "yes"]:
                    answer_breastfeeding = input(
                        "Have you been breastfeeding for more than 6 months (y/n): "
                    )
                    if answer_breastfeeding.strip().lower() in ["y", "yes"]:
                        breastfeeding = 2
                    else:
                        breastfeeding = 1
        height = input("Height in cm: ")
        weight = input("Weight in kg: ")
        age_delta = date.today() - date.fromisoformat(re.sub(r"[^0-9\-]", "", dob))
        if age_delta.days / 365 > 1:
            pal = input(
                "What is your physical activity level? \n [1] 'Inactive', \n [2] 'Low active', \n [3] 'Active', \n [4] 'Very active' \n: "
            )
        else:
            pal = None
        check_desired_weight = input("Do you have a desired weight (y/n): ")
        if check_desired_weight.strip().lower() in ["y", "yes"]:
            check_calc_with_bmi = input(
                "Would you like to calculate the desired weight based on a desired BMI (y/n): "
            )
            if check_calc_with_bmi.strip().lower() in ["y", "yes"]:
                desired_bmi = float(
                    input(
                        "Desired BMI (18.5 < normal range < 25, with 22 a good default): "
                    )
                )
                desired_weight = desired_bmi * ((float(height) / 100) ** 2)
            else:
                desired_weight = float(input("Desired weight in kg: "))
                desired_bmi = desired_weight / ((float(height) / 100) ** 2)
        else:
            desired_weight = None
            desired_bmi = None

        return cls(
            name,
            dob,
            sex,
            height,
            weight,
            due_date,
            breastfeeding,
            pal,
            desired_weight,
            desired_bmi,
        )
