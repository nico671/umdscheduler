from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from resources.courses.all_courses import AllCoursesList
from resources.courses.all_courses_mini import AllCoursesListMini
from resources.courses.semesters import Semesters
from resources.departments import Departments
from resources.majors import Majors

app = Flask(__name__)
CORS(app)
api = Api(app)

api.add_resource(Majors, "/majors")
api.add_resource(Departments, "/courses/departments")
api.add_resource(AllCoursesList, "/courses")
api.add_resource(AllCoursesListMini, "/courses/minified")
# api.add_resource(Course, "/courses/<string:course_id>")
# api.add_resource(CourseSections, "/courses/<string:course_id>/sections")
# api.add_resource(CourseSection, "/courses/<string:course_id>/sections/<int:section_id>")
api.add_resource(Semesters, "/courses/semesters")


if __name__ == "__main__":
    app.run(debug=True)
