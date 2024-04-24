struct Person:
    name: String[50]
    age: uint256[2]

struct Person2:
    person: Person[3]

@external
def getPersonDetails(person:Person2) -> String[100]:
    details:String[100]= concat("Name: ", person.person[0].name, ", Age: ", convert(person.person[0].age[0], String[30]))
    # details:String[100]= concat("Name: ", person.name)
    return details

@external
def createPerson(name:String[50],age:uint256) -> Person:
    new_person: Person = Person({name:name, age:[age, age]})
    return new_person