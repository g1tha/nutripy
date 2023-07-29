from Persons import Person
import csv
import json

# with open('dct.json', 'w') as file:
#      json.dump(dct, file)

person = Person.get()

print(person)
print(person.uid)
print(person.bmi)
print(person.desired_bmi)
print(person.desired_weight)

for nutrient in person.diet_rqmts:
    if (
        person.diet_rqmts[nutrient]["amount_lower"]
        and person.diet_rqmts[nutrient]["amount_upper"]
        and person.diet_rqmts[nutrient]["amount_lower"]
        != person.diet_rqmts[nutrient]["amount_upper"]
    ):
        if person.diet_rqmts[nutrient]["amount_tul"]:
            print(
                f"{nutrient}: {person.diet_rqmts[nutrient]['amount_lower']:.2f}-{person.diet_rqmts[nutrient]['amount_upper']:.2f} ({person.diet_rqmts[nutrient]['amount_tul']:.2f} limit) {person.diet_rqmts[nutrient]['unit']}"
            )
        else:
            print(
                f"{nutrient}: {person.diet_rqmts[nutrient]['amount_lower']:.2f}-{person.diet_rqmts[nutrient]['amount_upper']:.2f} {person.diet_rqmts[nutrient]['unit']}"
            )
    elif person.diet_rqmts[nutrient]["amount_lower"]:
        if person.diet_rqmts[nutrient]["amount_tul"]:
            print(
                f"{nutrient}: {person.diet_rqmts[nutrient]['amount_lower']:.2f} ({person.diet_rqmts[nutrient]['amount_tul']:.2f} limit) {person.diet_rqmts[nutrient]['unit']}"
            )
        else:
            print(
                f"{nutrient}: {person.diet_rqmts[nutrient]['amount_lower']:.2f} {person.diet_rqmts[nutrient]['unit']}"
            )
