#!/usr/bin/env python

import json
import os
import random
import sys
import uuid
from collections import defaultdict
from dataclasses import dataclass

import requests

# fmt: off

firstnames = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Margaret",
    "Matthew", "Lisa", "Anthony", "Betty", "Donald", "Dorothy", "Mark", "Sandra",
    "Paul", "Ashley", "Steven", "Kimberly", "Andrew", "Donna", "Kenneth", "Emily",
    "George", "Michelle", "Joshua", "Carol", "Kevin", "Amanda", "Brian", "Melissa",
    "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Laura",
    "Jeffrey", "Sharon", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Shirley", "Eric", "Angela", "Stephen", "Helen", "Jonathan", "Anna",
    "Larry", "Brenda", "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Ruth",
    "Benjamin", "Katherine", "Samuel", "Samantha", "Gregory", "Christine", "Frank", "Emma",
    "Alexander", "Catherine", "Raymond", "Debra", "Patrick", "Virginia", "Jack", "Rachel",
    "Dennis", "Carolyn", "Jerry", "Janet", "Tyler", "Maria", "Aaron", "Heather",
    "Henry", "Diane", "Douglas", "Julie", "Peter", "Joyce", "Adam", "Victoria",
    "Nathan", "Kelly", "Zachary", "Christina", "Walter", "Lauren", "Kyle", "Joan",
    "Harold", "Evelyn", "Carl", "Olivia", "Arthur", "Judith", "Gerald", "Megan",
    "Roger", "Cheryl", "Keith", "Martha", "Jeremy", "Andrea", "Terry", "Frances",
    "Lawrence", "Hannah", "Sean", "Jacqueline", "Christian", "Ann", "Albert", "Gloria",
    "Joe", "Jean", "Ethan", "Kathryn", "Austin", "Alice", "Jesse", "Teresa",
    "Willie", "Sara", "Billy", "Janice", "Bryan", "Doris", "Bruce", "Madison",
    "Jordan", "Julia", "Ralph", "Grace", "Roy", "Judy", "Noah", "Abigail",
    "Dylan", "Marie", "Eugene", "Denise", "Wayne", "Beverly", "Alan", "Amber",
    "Juan", "Theresa", "Louis", "Marilyn", "Russell", "Danielle", "Gabriel", "Diana",
    "Randy", "Brittany", "Philip", "Natalie", "Harry", "Sophia", "Vincent", "Rose",
    "Bobby", "Isabella", "Johnny", "Charlotte"
]

lastnames = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza",
    "Ruiz", "Hughes", "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers",
    "Long", "Ross", "Foster", "Jimenez", "Powell", "Jenkins", "Perry", "Russell",
    "Sullivan", "Bell", "Coleman", "Butler", "Henderson", "Barnes", "Gonzales", "Fisher",
    "Vasquez", "Simmons", "Romero", "Jordan", "Patterson", "Alexander", "Hamilton", "Graham",
    "Reynolds", "Griffin", "Wallace", "Moreno", "West", "Cole", "Hayes", "Bryant",
    "Herrera", "Gibson", "Ellis", "Tran", "Medina", "Aguilar", "Stevens", "Murray",
    "Ford", "Castro", "Marshall", "Owens", "Harrison", "Fernandez", "Mcdonald", "Woods",
    "Washington", "Kennedy", "Wells", "Vargas", "Henry", "Chen", "Freeman", "Webb",
    "Tucker", "Guzman", "Burns", "Crawford", "Olson", "Simpson", "Porter", "Hunter",
    "Gordon", "Mendez", "Silva", "Shaw", "Snyder", "Mason", "Dixon", "Munoz",
    "Hunt", "Hicks", "Holmes", "Palmer", "Wagner", "Black", "Robertson", "Boyd",
    "Rose", "Stone", "Salazar", "Fox", "Warren", "Mills", "Meyer", "Rice",
    "Schmidt", "Garza", "Daniels", "Ferguson", "Nichols", "Stephens", "Soto", "Weaver",
    "Ryan", "Gardner", "Payne", "Grant", "Dunn", "Kelley", "Spencer", "Hawkins",
    "Arnold", "Pierce", "Vazquez", "Hansen"
]

cities = [
    ("New York City", "New York", "Northeast"),
    ("Los Angeles", "California", "West"),
    ("Chicago", "Illinois", "Midwest"),
    ("Houston", "Texas", "South"),
    ("Phoenix", "Arizona", "West"),
    ("Philadelphia", "Pennsylvania", "Northeast"),
    ("San Antonio", "Texas", "South"),
    ("San Diego", "California", "West"),
    ("Dallas", "Texas", "South"),
    ("San Jose", "California", "West"),
    ("Austin", "Texas", "South"),
    ("Jacksonville", "Florida", "South"),
    ("Fort Worth", "Texas", "South"),
    ("Columbus", "Ohio", "Midwest"),
    ("Indianapolis", "Indiana", "Midwest"),
    ("Charlotte", "North Carolina", "South"),
    ("San Francisco", "California", "West"),
    ("Seattle", "Washington", "West"),
    ("Denver", "Colorado", "West"),
    ("Washington", "District of Columbia", "South"),
    ("Boston", "Massachusetts", "Northeast"),
    ("El Paso", "Texas", "South"),
    ("Nashville", "Tennessee", "South"),
    ("Detroit", "Michigan", "Midwest"),
    ("Oklahoma City", "Oklahoma", "South"),
    ("Portland", "Oregon", "West"),
    ("Las Vegas", "Nevada", "West"),
    ("Memphis", "Tennessee", "South"),
    ("Louisville", "Kentucky", "South"),
    ("Baltimore", "Maryland", "South"),
    ("Milwaukee", "Wisconsin", "Midwest"),
    ("Albuquerque", "New Mexico", "West"),
    ("Tucson", "Arizona", "West"),
    ("Fresno", "California", "West"),
    ("Mesa", "Arizona", "West"),
    ("Sacramento", "California", "West"),
    ("Atlanta", "Georgia", "South"),
    ("Kansas City", "Missouri", "Midwest"),
    ("Colorado Springs", "Colorado", "West"),
    ("Miami", "Florida", "South"),
    ("Raleigh", "North Carolina", "South"),
    ("Omaha", "Nebraska", "Midwest"),
    ("Long Beach", "California", "West"),
    ("Virginia Beach", "Virginia", "South"),
    ("Oakland", "California", "West"),
    ("Minneapolis", "Minnesota", "Midwest"),
    ("Tulsa", "Oklahoma", "South"),
    ("Arlington", "Texas", "South"),
    ("New Orleans", "Louisiana", "South"),
    ("Wichita", "Kansas", "Midwest"),
    ("Cleveland", "Ohio", "Midwest"),
    ("Tampa", "Florida", "South"),
    ("Bakersfield", "California", "West"),
    ("Aurora", "Colorado", "West"),
    ("Anaheim", "California", "West"),
    ("Honolulu", "Hawaii", "West"),
    ("Santa Ana", "California", "West"),
    ("Riverside", "California", "West"),
    ("Corpus Christi", "Texas", "South"),
    ("Lexington", "Kentucky", "South"),
    ("Henderson", "Nevada", "West"),
    ("Stockton", "California", "West"),
    ("Saint Paul", "Minnesota", "Midwest"),
    ("Cincinnati", "Ohio", "Midwest"),
    ("St. Louis", "Missouri", "Midwest"),
    ("Pittsburgh", "Pennsylvania", "Northeast"),
    ("Greensboro", "North Carolina", "South"),
    ("Lincoln", "Nebraska", "Midwest"),
    ("Anchorage", "Alaska", "West"),
    ("Plano", "Texas", "South"),
    ("Orlando", "Florida", "South"),
    ("Irvine", "California", "West"),
    ("Newark", "New Jersey", "Northeast"),
    ("Durham", "North Carolina", "South"),
    ("Chula Vista", "California", "West"),
    ("Toledo", "Ohio", "Midwest"),
    ("Fort Wayne", "Indiana", "Midwest"),
    ("St. Petersburg", "Florida", "South"),
    ("Laredo", "Texas", "South"),
    ("Jersey City", "New Jersey", "Northeast"),
    ("Chandler", "Arizona", "West"),
    ("Madison", "Wisconsin", "Midwest"),
    ("Lubbock", "Texas", "South"),
    ("Scottsdale", "Arizona", "West"),
    ("Reno", "Nevada", "West"),
    ("Buffalo", "New York", "Northeast"),
    ("Gilbert", "Arizona", "West"),
    ("Glendale", "Arizona", "West"),
    ("North Las Vegas", "Nevada", "West"),
    ("Winston-Salem", "North Carolina", "South"),
    ("Chesapeake", "Virginia", "South"),
    ("Norfolk", "Virginia", "South"),
    ("Fremont", "California", "West"),
    ("Garland", "Texas", "South"),
    ("Irving", "Texas", "South"),
    ("Hialeah", "Florida", "South"),
    ("Richmond", "Virginia", "South"),
    ("Boise", "Idaho", "West"),
    ("Spokane", "Washington", "West"),
    ("Baton Rouge", "Louisiana", "South"),
    ("Tacoma", "Washington", "West"),
    ("San Bernardino", "California", "West"),
    ("Modesto", "California", "West"),
    ("Fontana", "California", "West"),
    ("Des Moines", "Iowa", "Midwest"),
    ("Moreno Valley", "California", "West"),
    ("Santa Clarita", "California", "West"),
    ("Fayetteville", "North Carolina", "South"),
    ("Birmingham", "Alabama", "South"),
    ("Oxnard", "California", "West"),
    ("Rochester", "New York", "Northeast"),
    ("Port St. Lucie", "Florida", "South"),
    ("Grand Rapids", "Michigan", "Midwest"),
    ("Huntsville", "Alabama", "South"),
    ("Salt Lake City", "Utah", "West"),
    ("Frisco", "Texas", "South"),
    ("Yonkers", "New York", "Northeast"),
    ("Amarillo", "Texas", "South"),
    ("Glendale", "California", "West"),
    ("Huntington Beach", "California", "West"),
    ("McKinney", "Texas", "South"),
    ("Montgomery", "Alabama", "South"),
    ("Augusta", "Georgia", "South"),
    ("Aurora", "Illinois", "Midwest"),
    ("Akron", "Ohio", "Midwest"),
    ("Little Rock", "Arkansas", "South"),
    ("Tempe", "Arizona", "West"),
    ("Overland Park", "Kansas", "Midwest"),
    ("Grand Prairie", "Texas", "South"),
    ("Tallahassee", "Florida", "South"),
    ("Cape Coral", "Florida", "South"),
    ("Mobile", "Alabama", "South"),
    ("Knoxville", "Tennessee", "South"),
    ("Shreveport", "Louisiana", "South"),
    ("Worcester", "Massachusetts", "Northeast"),
    ("Ontario", "California", "West"),
    ("Vancouver", "Washington", "West"),
    ("Sioux Falls", "South Dakota", "Midwest"),
    ("Chattanooga", "Tennessee", "South"),
    ("Brownsville", "Texas", "South"),
    ("Fort Lauderdale", "Florida", "South"),
    ("Providence", "Rhode Island", "Northeast"),
    ("Newport News", "Virginia", "South"),
    ("Rancho Cucamonga", "California", "West"),
    ("Santa Rosa", "California", "West"),
    ("Peoria", "Arizona", "West"),
    ("Oceanside", "California", "West"),
    ("Elk Grove", "California", "West"),
    ("Salem", "Oregon", "West"),
    ("Pembroke Pines", "Florida", "South"),
    ("Eugene", "Oregon", "West"),
    ("Garden Grove", "California", "West"),
    ("Cary", "North Carolina", "South"),
    ("Fort Collins", "Colorado", "West"),
    ("Corona", "California", "West"),
    ("Springfield", "Missouri", "Midwest"),
    ("Jackson", "Mississippi", "South"),
    ("Alexandria", "Virginia", "South"),
    ("Hayward", "California", "West"),
    ("Clarksville", "Tennessee", "South"),
    ("Lakewood", "Colorado", "West"),
    ("Lancaster", "California", "West"),
    ("Salinas", "California", "West"),
    ("Palmdale", "California", "West"),
    ("Hollywood", "Florida", "South"),
    ("Springfield", "Massachusetts", "Northeast"),
    ("Macon", "Georgia", "South")
]

job_titles = [
    "Store Manager",
    "Assistant Store Manager",
    "Department Manager",
    "Shift Supervisor",
    "Cashier",
    "Customer Service Representative",
    "Stock Clerk",
    "Grocery Clerk",
    "Produce Clerk",
    "Bakery Clerk",
    "Deli Clerk",
    "Meat Clerk",
    "Seafood Clerk",
    "Dairy Clerk",
    "Frozen Food Clerk",
    "Beverage Clerk",
    "Bulk Foods Clerk",
    "Pharmacy Technician",
    "Pharmacist",
    "Pharmacy Manager",
    "Floral Clerk",
    "Fuel Station Attendant",
    "Front End Supervisor",
    "Assistant Front End Manager",
    "Customer Service Manager",
    "Loss Prevention Associate",
    "Security Guard",
    "Human Resources Coordinator",
    "Recruiter",
    "Training Coordinator",
    "Employee Relations Specialist",
    "Payroll Administrator",
    "Benefits Specialist",
    "Marketing Coordinator",
    "Advertising Manager",
    "Promotions Specialist",
    "Community Relations Manager",
    "Public Relations Coordinator",
    "Event Coordinator",
    "Social Media Manager",
    "IT Support Specialist",
    "Network Administrator",
    "Systems Analyst",
    "Web Developer",
    "Mobile App Developer",
    "Data Analyst",
    "Business Intelligence Analyst",
    "Financial Analyst",
    "Accountant",
    "Budget Analyst",
    "Procurement Specialist",
    "Inventory Manager",
    "Supply Chain Analyst",
    "Logistics Coordinator",
    "Transportation Manager",
    "Distribution Center Manager",
    "Warehouse Supervisor",
    "Forklift Operator",
    "Truck Driver",
    "Quality Assurance Inspector",
    "Food Safety Specialist",
    "Health and Safety Coordinator",
    "Environmental Compliance Manager",
    "Sustainability Coordinator",
    "Facilities Manager",
    "Maintenance Technician",
    "Electrician",
    "HVAC Technician",
    "Plumber",
    "Carpenter",
    "General Contractor",
    "Project Manager",
    "Construction Superintendent",
    "Store Designer",
    "Interior Decorator",
    "Merchandiser",
    "Visual Merchandising Manager",
    "Planogram Coordinator",
    "Retail Buyer",
    "Purchasing Manager",
    "Vendor Relations Coordinator",
    "Product Development Specialist",
    "Private Label Manager",
    "Brand Manager",
    "Pricing Analyst",
    "Sales Associate",
    "Product Demonstrator",
    "Brand Ambassador",
    "Loyalty Program Coordinator",
    "Rewards Specialist",
    "Financial Services Representative",
    "Money Services Manager",
    "Check-out Supervisor",
    "Self-Checkout Attendant",
    "Bagging Assistant",
    "Return Desk Clerk",
    "Membership Coordinator",
    "Club Services Specialist",
    "Catering Coordinator",
    "Party Planner"
]


# fmt: on


def random_name_generator():
    seen = set()

    def generate_random_name() -> tuple[str, str]:
        name = (random.choice(firstnames), random.choice(lastnames))
        if name in seen:
            return generate_random_name()
        else:
            seen.add(name)
            return name

    return generate_random_name


get_random_name = random_name_generator()


def generate_registered_actors(count: int):
    for _ in range(count):
        firstname, lastname = get_random_name()
        yield {
            "ref": str(uuid.uuid4()),
            "type": "user",
            "name": "%s %s" % (firstname, lastname),
            "extra": [
                {
                    "name": "email",
                    "value": "%s.%s@example.com"
                    % (firstname.lower(), lastname.lower()),
                }
            ],
        }


def generate_applicant_actors(count: int):
    for _ in range(count):
        firstname, lastname = get_random_name()
        email = "%s.%s@example.net" % (firstname.lower(), lastname.lower())
        yield {
            "ref": email,
            "type": "applicant",
            "name": "%s %s" % (firstname, lastname),
            "extra": [{"name": "email", "value": email}],
        }


def generate_node_paths(count: int):
    # Assign a unique ref to each item level
    # two level dict:
    # - first level is the depth of the item
    # - second level is the value itself (the city, the state, etc...)
    # and the value of the second level dict is a UUID
    refs = defaultdict(defaultdict)
    for item in cities:
        for level, value in enumerate(item):
            refs[level][value] = str(uuid.uuid4())

    for item, _ in zip(cities, range(count)):
        yield list(
            reversed(
                [
                    {
                        "ref": refs[level][value],
                        "name": value,
                    }
                    for level, value in enumerate(item)
                ]
            )
        )


@dataclass
class LogProvider:
    registered_actors: list[dict]
    applicant_actors: list[dict]
    node_paths: list[list[dict]]

    @classmethod
    def prepare(cls):
        return cls(
            registered_actors=list(generate_registered_actors(1000)),
            applicant_actors=list(generate_applicant_actors(5000)),
            node_paths=list(generate_node_paths(len(cities))),
        )

    def _build_job_offer_creation_log(self):
        job_title = random.choice(job_titles)
        node_path = random.choice(self.node_paths)
        return {
            "action": {
                "category": "job-offers",
                "type": "job-offer-creation",
            },
            "actor": random.choice(self.registered_actors),
            "source": [
                {
                    "name": "application",
                    "value": "myATS",
                },
                {
                    "name": "application-version",
                    "value": "1.0.0",
                },
            ],
            "resource": {
                "ref": str(uuid.uuid4()),
                "type": "job-offer",
                "name": job_title + " in " + node_path[-1]["name"],
            },
            "details": [
                {
                    "name": "job-title",
                    "value": job_title,
                }
            ],
            "node_path": node_path,
        }

    def _build_job_offer_close_log(self, job_offer_log, reason):
        return {
            "action": {
                "category": "job-offers",
                "type": "job-offer-close",
            },
            "actor": job_offer_log["actor"],
            "source": [
                {
                    "name": "application",
                    "value": "myATS",
                },
                {
                    "name": "application-version",
                    "value": "1.0.0",
                },
            ],
            "resource": job_offer_log["resource"],
            "details": [
                {
                    "name": "reason",
                    "value": reason,
                }
            ],
            "node_path": job_offer_log["node_path"],
        }

    def _build_job_application_creation_log(self, job_offer_log):
        applicant = random.choice(self.applicant_actors)
        attachments = [
            {
                "name": "resume.txt",
                "data": b"This is the resume of someone great",
                "type": "resume",
            }
        ]
        return {
            "action": {
                "category": "job-applications",
                "type": "job-application",
            },
            "actor": applicant,
            "source": [
                {
                    "name": "job-board",
                    "value": "Get a job today !",
                },
            ],
            "resource": job_offer_log["resource"],
            "details": [
                {
                    "name": "comment",
                    "value": "I'm very interested in this job",
                }
            ],
            "node_path": job_offer_log["node_path"],
            "tags": [
                {
                    "type": "applicant",
                    "ref": applicant["ref"],
                    "name": applicant["name"],
                }
            ],
        }, attachments

    def _build_job_application_status_change_log(
        self, job_application_log, job_offer_log, status
    ):
        return {
            "action": {
                "category": "job-applications",
                "type": "job-application-status-change",
            },
            "actor": job_offer_log["actor"],
            "source": [
                {
                    "name": "application",
                    "value": "myATS",
                },
                {
                    "name": "application-version",
                    "value": "1.0.0",
                },
            ],
            "resource": job_application_log["actor"],
            "details": [
                {
                    "name": "status",
                    "value": status,
                }
            ],
            "node_path": job_application_log["node_path"],
            "tags": job_application_log["tags"],
        }

    def _build_job_application_logs(self):
        job_offer_log = self._build_job_offer_creation_log()
        yield job_offer_log
        for _ in range(5):
            job_application_log, attachments = self._build_job_application_creation_log(
                job_offer_log
            )
            yield job_application_log, attachments
            yield self._build_job_application_status_change_log(
                job_application_log,
                job_offer_log,
                random.choice(("accepted", "rejected", "interview")),
            )
        yield self._build_job_offer_close_log(
            job_offer_log, random.choice(("position filled", "position cancelled"))
        )

    def _build_user_creation_log(self):
        user = random.choice(self.registered_actors)
        return {
            "action": {
                "category": "users",
                "type": "user-creation",
            },
            "actor": random.choice(self.registered_actors),
            "source": [
                {
                    "name": "application",
                    "value": "myATS",
                },
                {
                    "name": "application-version",
                    "value": "1.0.0",
                },
            ],
            "resource": {
                "ref": user["ref"],
                "type": "user",
                "name": user["name"],
            },
            "details": [
                {
                    "name": "granted-role",
                    "value": "Administrator",
                }
            ],
            "node_path": random.choice(self.node_paths),
            "tags": [
                {
                    "type": "security",
                },
                {"type": "important"},
            ],
        }

    def _build_logs(self):
        yield self._build_user_creation_log()
        for log in self._build_job_application_logs():
            yield log

    def build_logs(self):
        # Infinite log builder
        while True:
            for log in self._build_logs():
                attachments = []
                if isinstance(log, tuple):
                    log, attachments = log
                yield log, attachments


def jsonify(data):
    return json.dumps(data, indent=4, ensure_ascii=False)


def inject_log(base_url, repo_id, api_key, log, attachments):
    resp = requests.post(
        f"{base_url}/api/repos/{repo_id}/logs",
        headers={"Authorization": f"Bearer " + api_key},
        json=log,
    )
    if not resp.ok:
        sys.exit(
            "Error %s while pushing log:\n%s" % (resp.status_code, jsonify(resp.json()))
        )
    log_id = resp.json()["id"]
    for attachment in attachments:
        resp = requests.post(
            f"{base_url}/api/repos/{repo_id}/logs/{log_id}/attachments",
            headers={"Authorization": f"Bearer " + api_key},
            files={"file": (attachment["name"], attachment["data"])},
            data={
                "type": attachment["type"],
            },
        )
        if not resp.ok:
            sys.exit(
                "Error %s while pushing attachment: %s"
                % (resp.status_code, jsonify(resp.json()))
            )


def main(argv):
    if len(argv) != 2:
        sys.exit("Usage: %s COUNT" % argv[0])

    try:
        base_url = os.environ["AUDITIZE_URL"]
        repo_id = os.environ["AUDITIZE_REPO"]
        api_key = os.environ["AUDITIZE_APIKEY"]
    except KeyError as e:
        sys.exit("Missing environment variable: %s" % e)

    count = int(argv[1])

    provider = LogProvider.prepare()

    for (log, attachments), i in zip(provider.build_logs(), range(count)):
        print("Inject log %d of %d" % (i + 1, count), end="\r")
        inject_log(base_url, repo_id, api_key, log, attachments)
    print()


if __name__ == "__main__":
    main(sys.argv)
