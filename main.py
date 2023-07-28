from Persons import Person
import csv
import json


# with open('rda.json', 'w') as file:
#      json.dump(dct, file)

person = Person.get()

print(person)
print(person.uid)
print(person.bmi)
print(person.desired_bmi)
print(person.desired_weight)
print(person.kcal)
print(person.rda['Total Water'])
print(person.tul['Retinol'])
print(person.proteins)