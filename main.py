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
print(person.kcal)
print(person.rda['Iron'])
print(person.tul['Retinol'])
print(person.proteins)
print(person.energy_upper)
print(person.energy_lower)
for nutrient in person.diet_rqmts:
    print(f"{nutrient}: {person.diet_rqmts[nutrient]['amount_lower']} {person.diet_rqmts[nutrient]['unit']}")