from datetime import date
import uuid
from math import floor

class Person:
    def __init__(self, name, dob, sex, pregnant=None, breastfeeding=None):
        self.name = name
        self.dob = dob
        self.sex = sex
        self.pregnant = pregnant
        self.breastfeeding = breastfeeding
        # Add unique user id. check if it's already taken (check against user file once established)
        uid = uuid.uuid1()
        if uid not in []:
            self.uid = uid

    def __str__(self):
        if self.pregnant:
            return f"{self.name}, {self.sex}, aged {self._age_rounded}, currently pregnant in trimester {self.pregnant}."
        elif self.breastfeeding == 1:
            return f"{self.name}, {self.sex}, aged {self._age_rounded} currently into 1st 6 months of breastfeeding."
        elif self.breastfeeding == 2:
            return f"{self.name}, {self.sex}, aged {self._age_rounded} currently breastfeeding, more than 6 months in."
        else:
            return f"{self.name}, {self.sex}, aged {self._age_rounded}."
        
    
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
        try:
            date.fromisoformat(dob)
        except:
            raise ValueError("Must provide date of birth in the isoformat: yyyy-mm-dd")
        if date.fromisoformat(dob) > date.today():
            raise ValueError("Must provide a date from the past")
        delta = date.today() - date.fromisoformat(dob)
        age = delta.days/365
        if age < 1:
            self._age_rounded = floor(age * 100) / 100
        else:
            self._age_rounded = floor(age)
        self._dob = dob
        self._age = age

        
    @property
    def sex(self):
        return self._sex
    
    @sex.setter
    def sex(self, sex):
        sex = sex.strip().lower()
        if not sex:
            raise ValueError("Must provide the person's sex.")
        # Check against stored file/db with usersexs
        if sex in ['male', 'm']:
            sex = 'male'
        elif sex in ['female', 'f']:
            sex = 'female'
        else:
            raise ValueError("Provide 'm', 'male', 'f', or 'female'")
        self._sex = sex

    @property
    def pregnant(self):
        return self._pregnant
    
    @pregnant.setter
    def pregnant(self, pregnant):
        if  pregnant:
            if pregnant not in [1, 2, 3]:
                raise ValueError("Provide number for trimester (1, 2 or 3)")
        self._pregnant = pregnant

    @property
    def breastfeeding(self):
        return self._breastfeeding
    
    @breastfeeding.setter
    def breastfeeding(self, breastfeeding):
        if  breastfeeding:
            if breastfeeding not in [1, 2]:
                raise ValueError("Use 1 to indicate breastfeeding within 1st 6 months, use 2 to indicate breastfeeding after.")
        self._breastfeeding = breastfeeding

    @classmethod
    def get(cls):
        pregnant = None
        breastfeeding = None
        name = input("Username: ")
        dob = input("Date of birth (in the isoformat: yyyy-mm-dd): ")
        sex = input("Sex (male or female): ")
        if sex.strip().lower() in ['f', 'female']:
            check_pregnant = input("Are you pregnant (y/n): ")
            if check_pregnant.strip().lower() in ['y', 'yes']:
                pregnant = input("Which trimester are you in: ")
            else:
                check_breastfeeding = input("Are you breastfeeding (y/n): ")
                if check_breastfeeding.strip().lower() in ['y', 'yes']:
                    answer_breastfeeding = input("Have you been breastfeeding for more than 6 months (y/n): ")
                    if answer_breastfeeding.strip().lower() in ['y', 'yes']:
                        breastfeeding = 2
                    else:
                        breastfeeding = 1
        return cls(name, dob, sex, pregnant, breastfeeding)