'''

This python script works as a backend for parsing the copied text from  mail  and 
calculate SPI score for perticular user. Flask is used to deploy the  core  logic
to the webserver(Heroku in my case). re is regular expression module  provided by
python useful in parsing the given user string and extract the useful information

'''

import roman
import re
from flask import Flask, Response
from flask_restful import Resource, Api
import numpy as np
from flask_cors import CORS
from flask import render_template


app = Flask(__name__)
api = Api(app)
CORS(app)

###     branch wise data of credits scrapped from the nirmauniversity site is stored
###     in the credit file. You can check it for your reference in  home   directory
file = 'credit'   

###     database is dictionary data structure which stores the parsed details   for 
###     each branch semester wise.
database = {}    

###     These are some predefined variable. Use of each is decribed in further code 
count = 0
current_branch = ""
current_sem = 0


map_of_grade = {
    "A+":10.0,
    "A":9.0,
    "B+":8.0,
    "B":7.0,
    "C+":6.0,
    "C":5.0,
    "D":4.0,
    "FF":0.0,
    "IF":0.0,
    "IF(S)":0.0
}


map_of_branch = {
    "CH" : "Chemical Engineering",
    "CL" : "Civil Engineering",
    "EE" : "Electrical Engineering",
    "CE" : "Computer Engineering",
    "IT" : "Information Technology",
    "EC" : "Electronics and Communication Engineering",
    "IC" : "Instrumentation and Control Engineering",
    "ME" : "Mechanical Engineering"
}

'''
Read the credit file line by line. Have a look at some lines from credit file for
understanding the logic.

---------------------------------- Credit ----------------------------------------

Code:1 Course:Chemical Engineering
Semester : I
Subject Code	Subject	Credits
MA101	Calculus	4.00
...
...
...
...
Semester : II
Subject Code	Subject	Credits
MA201	Linear Algebra	4.00
PY101	Physics	3.00
...
...

----------------------------------------------------------------------------------

First line of each branch starts with " Code:X Course:XXXX XXXXX " followed by the
semester in roman which is converted into decimals. Thrid line is useless   and we 
cab then sart storing the subject details for current branch and  current semester


''' 
with open(file, 'rb') as inputfile:
    for line in inputfile:
        line = str(line)

    ### Remove the b' and \n from line
        line = line.replace("b'","")
        line = line.replace("\\n'","")

        if line.startswith("Code"):
            count = 0
        elif line.startswith("Semester"):
            count = 1

    ### if we are the at third lime of one branch block follow below logic
        if count == -1:
            count = -1

        ### Split the line by \t and add subject to current semester under current branch 
            subject_details = line.split("\\t")
            course_code = subject_details[0]
            course_name = subject_details[1]

        ### if course credit is not defined take it as 0.0  
            try:
                course_credit = subject_details[2]
            except:
                course_credit = 0.0

            database[current_branch][current_sem].update({course_name:course_credit})

    ### if we are at the first line of block than intialize new object for a branch
        elif count == 0:
            count = 1

        ### Collecting the couse name
            data = line.split(" ",1)
            code = data[0].split(":")[1]
            course = data[1].split(":")[1]
            current_branch = course
            database.update({course:{}})

    ### if we are at the second line of block than intialize new object for a semster
        elif count == 1:
            count = 2

        ### Collecting the semester number
            sem = line.replace(" ","").split(":")[1]
            sem = roman.fromRoman(sem)
            current_sem = sem
            database[current_branch].update({current_sem:{}})
        else:
            count = -1



def count_spi(result):
'''

This function a takes a string of below form and  returns a  html   output for response.
First two arguments are name and semester followed by the Course name and grade obtained
which is separated by ':'

------- sample query -----

result = 'Civil Engineering,7,Minor Project:B+,Practical Training:B,Geomatics:B+,Human 
Resource Management:B+,Design of Structures - III:B,Organizational Behavior:B+,Traffic 
Engineering and Design:B+,Construction and Project Management:B+,Professional Practice:B'

--------------------------

'''
    grade_details = result.split(",")
    branch = grade_details[0]
    semester = int(grade_details[1])

    total_credits_earned = 0
    sum_of_credits = 0

    result_html = ""


    for i in range(2,len(grade_details)):
        subject = grade_details[i].split(":")[0]
        grade = grade_details[i].split(":")[1]

        try:
            credit = float(database[branch][semester][subject])
        except:
            credit = 3.0

        score = float(map_of_grade[grade])

        total_credits_earned += score*credit
        sum_of_credits += credit

        try:
            credit = float(database[branch][semester][subject])
            result_html += '<tr><th scope="row">'+subject+'</th><td><input type="text" id="credit" value='+str(credit)+' ></td><td>'+str(grade)+'</td><td id="point">'+str(score)+'</td></tr>'
        except:
            result_html += '<tr><th scope="row">'+subject+'</th><td><input type="text" id="credit" class="error" value='+str(credit)+' ></td><td>'+str(grade)+'</td><td id="point">'+str(score)+'</td></tr>'

        

    spi = np.round(total_credits_earned/sum_of_credits,decimals=3)
    result_html += '<thead class="thead-dark"><tr><th scope="row">Credits Earned : <span id="ce">'+str(total_credits_earned)+'</span></th><th>Max Credits : <span id="mc">'+str(sum_of_credits)+'</span></th><th colspan=2>SPI : <span id="spi">'+str(spi)+'</span></th></tr></thead>'

    response = """
                <table class="table">
                  <thead class="thead-dark">
                    <tr>
                      <th scope="col">Course Name</th>
                      <th scope="col">Credit</th>
                      <th scope="col">Grade</th>
                      <th scope="col">Points</th>
                    </tr>
                  </thead>
                  <tbody>
            """+result_html+"""
                  </tbody>
                </table>
            """


    return response

def parse_string(query):
'''

This function gets the raw query as input from mail and generate  the  modified query for
count_spi function. Branch of student is extracted from roll no. for   e.g CE -> Computer
Engineering in map_of_branch map defined earlier.

Subject code and semester number from each line is removed using regular expression match

For e.g Course code can be a string of alphabets following of alpha numeric character

'''
    roll_no = query [ query.find("Roll No : ",1)+len('Roll No :  ') : query.find(" Student Name",1) ]
    name = query [ query.find("Student Name : ",1)+len('Student Name : ') : query.find(" Course",1) ]
    grades = query[ query.find("Course Grade",1)+len('Course Grade '):len(query) ]
    sem = re.findall("[' '][\d][' ']",grades,1)[0].replace(" ","")
    branch = map_of_branch[roll_no[3:5]]

    modified = re.sub("[' '][\d][' ']",":",grades)
    modified = re.sub("[' ']?[A-Z]+[\d][\d]?[A-Z]?[\d][' ']",",",modified)

    return branch+","+sem+modified



###  Following is the API logic in flask for mapping input string to html response. 

class my_spi(Resource):
    def get(self, query):
        try:
            parsed_query = parse_string(query)
            results = count_spi(parsed_query)
        except:
            results = "Something Went Wrong.!!"
        resp = Response(response='<body>'+str(results)+'</body>',
        status=200,
        mimetype="text/html")
        return(resp)


api.add_resource(my_spi, '/grades/<query>')

@app.route('/')
def index():
    return render_template('index.html')
    
if __name__ == '__main__':
     app.run()
