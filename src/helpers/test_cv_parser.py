from cv_parser import parse_cv

sample_cv = """
KATHY JAMES
Programmer

k_james@email.com

(123) 456-7890
Tulsa, Oklahoma

LinkedIn
Github
www.kjcodes.com

WORK EXPERIENCE

Programmer
Proficient
September 2018 - current
Tulsa, OK

• Designed and coded 1,000+ unit and integration testing using Jest and Proficient methodology
• Troubleshooted 2,000+ code-related issues and defects
• Produced detailed design documentation, unit tests, and documented code for 50+ clients
• Practiced strong configuration management and version control for projects across 7 teams
• Represented Proficient in 50+ team meetings
• Attended 100+ weekly stand-up meetings to receive tasks and instruction for weekly goals

Software Engineering Intern
TIBCO
June 2018 - September 2018
Tuscaloosa, AL

• Delivered 8 front-end applications written in Angular.js
• Developed 3 Eclipse-based applications written in Java
• Contributed to 6 VSCode extensions
• Developed and executed 200+ unit tests using Jest
• Collaborated with 30+ colleagues in local and remote locations
• Mastered and taught engineering group’s best practices and coding standards

PROJECTS

Social Media Scheduler
Creator

• Built a responsive web app using Django and Node that allowed users to schedule social media posts across Instagram, Twitter, and Facebook
• Utilized the Twitter and Instagram APIs
• Built features using scikit-learn in Python that learned what time of day maximized engagement with social media posts
• Increased the overall user engagement rate by 15%

CAREER OBJECTIVE

Graduate of computer science with experience working across the full-stack of software development. I have built 30+ projects on 7 small teams and am looking for a role with TIBCO where I can grow and continue to learn from other experienced team members.

EDUCATION

B.S.
Computer Science
University of Alabama
2014 - 2018
Tuscaloosa, AL

SKILLS

• JavaScript
• HTML, CSS
• Django
• SQL
• REST APIs
• Angular.js
• React.js
• Jest
• Eclipse
• Java
"""

result = parse_cv(sample_cv)

print("Parsed CV Output:")
for k, v in result.items():
    print(f"{k}: {v}")
