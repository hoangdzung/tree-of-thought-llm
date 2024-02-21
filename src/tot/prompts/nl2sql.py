# 5 shot
cot_prompt = '''Given the schema and question, your task is to decompose the question and write corresponding queries until you reach the original question.

Schema: 
CREATE TABLE "Document_Types" (
	document_type_code VARCHAR(10), 
	document_description VARCHAR(255) NOT NULL, 
	PRIMARY KEY (document_type_code)
)

CREATE TABLE "Organisation_Types" (
	organisation_type VARCHAR(10), 
	organisation_type_description VARCHAR(255) NOT NULL, 
	PRIMARY KEY (organisation_type)
)

CREATE TABLE "Research_Outcomes" (
	outcome_code VARCHAR(10), 
	outcome_description VARCHAR(255) NOT NULL, 
	PRIMARY KEY (outcome_code)
)

CREATE TABLE "Staff_Roles" (
	role_code VARCHAR(10), 
	role_description VARCHAR(255) NOT NULL, 
	PRIMARY KEY (role_code)
)

CREATE TABLE "Organisations" (
	organisation_id INTEGER, 
	organisation_type VARCHAR(10) NOT NULL, 
	organisation_details VARCHAR(255) NOT NULL, 
	PRIMARY KEY (organisation_id), 
	FOREIGN KEY(organisation_type) REFERENCES "Organisation_Types" (organisation_type)
)

CREATE TABLE "Grants" (
	grant_id INTEGER, 
	organisation_id INTEGER NOT NULL, 
	grant_amount DECIMAL(19, 4) DEFAULT 0 NOT NULL, 
	grant_start_date DATETIME NOT NULL, 
	grant_end_date DATETIME NOT NULL, 
	other_details VARCHAR(255) NOT NULL, 
	PRIMARY KEY (grant_id), 
	FOREIGN KEY(organisation_id) REFERENCES "Organisations" (organisation_id)
)

CREATE TABLE "Projects" (
	project_id INTEGER, 
	organisation_id INTEGER NOT NULL, 
	project_details VARCHAR(255) NOT NULL, 
	PRIMARY KEY (project_id), 
	FOREIGN KEY(organisation_id) REFERENCES "Organisations" (organisation_id)
)

CREATE TABLE "Research_Staff" (
	staff_id INTEGER, 
	employer_organisation_id INTEGER NOT NULL, 
	staff_details VARCHAR(255) NOT NULL, 
	PRIMARY KEY (staff_id), 
	FOREIGN KEY(employer_organisation_id) REFERENCES "Organisations" (organisation_id)
)

CREATE TABLE "Documents" (
	document_id INTEGER, 
	document_type_code VARCHAR(10), 
	grant_id INTEGER NOT NULL, 
	sent_date DATETIME NOT NULL, 
	response_received_date DATETIME NOT NULL, 
	other_details VARCHAR(255) NOT NULL, 
	PRIMARY KEY (document_id), 
	FOREIGN KEY(grant_id) REFERENCES "Grants" (grant_id), 
	FOREIGN KEY(document_type_code) REFERENCES "Document_Types" (document_type_code)
)

CREATE TABLE "Project_Outcomes" (
	project_id INTEGER NOT NULL, 
	outcome_code VARCHAR(10) NOT NULL, 
	outcome_details VARCHAR(255), 
	FOREIGN KEY(outcome_code) REFERENCES "Research_Outcomes" (outcome_code), 
	FOREIGN KEY(project_id) REFERENCES "Projects" (project_id)
)

CREATE TABLE "Project_Staff" (
	staff_id DOUBLE, 
	project_id INTEGER NOT NULL, 
	role_code VARCHAR(10) NOT NULL, 
	date_from DATETIME, 
	date_to DATETIME, 
	other_details VARCHAR(255), 
	PRIMARY KEY (staff_id), 
	FOREIGN KEY(role_code) REFERENCES "Staff_Roles" (role_code), 
	FOREIGN KEY(project_id) REFERENCES "Projects" (project_id)
)

CREATE TABLE "Tasks" (
	task_id INTEGER, 
	project_id INTEGER NOT NULL, 
	task_details VARCHAR(255) NOT NULL, 
	"eg Agree Objectives" VARCHAR(1), 
	PRIMARY KEY (task_id), 
	FOREIGN KEY(project_id) REFERENCES "Projects" (project_id)
)

Question: Find out the send dates of the documents with the grant amount of more than 5000 were granted by organisation type described as "Research".

Decomposition:
Q: Find out the send dates of the documents.
A: SELECT sent_date FROM documents
Q: Find out the grandt id with the grant amount of more than 5000.
A: SELECT grandt_id FROM grants WHERE grant_amount > 5000
Q: Find out the send dates of the documents with the grant amount of more than 5000
A: SELECT T1.sent_date FROM documents AS T1 JOIN grants AS T2 ON T1.grant_id = T2.grant_id WHERE T2.grant_amount > 5000
Q: Find out the organisation type described as "Research".
A: SELECT organisation_type FROM organisation_types WHERE organisation_type_description = "Research"
Q: Find out the organisation id whose organisation type is described as "Research".
A: SELECT T3.organisation_id FROM organisations AS T3 JOIN organisation_types AS T4 ON T3.organisation_type = T4.organisation_type WHERE T4.organisation_type_description = "Research"
Q: Find out the send dates of the documents with the grant amount of more than 5000 were granted by organisation type described as "Research".
A: SELECT T1.sent_date FROM documents AS T1 JOIN Grants AS T2 ON T1.grant_id = T2.grant_id JOIN Organisations AS T3 ON T2.organisation_id = T3.organisation_id JOIN organisation_Types AS T4 ON T3.organisation_type = T4.organisation_type WHERE T2.grant_amount > 5000 AND T4.organisation_type_description = ’Research’

Schema:
{input}

Decomposition:
'''
vote_prompt = '''Given the schema, question and several choices of intermediate steps, decide which choice is most promising to lead to a correct query. Analyze each choice in detail, then conclude in the last line "The best choice is {s}", where s the integer id of the choice.
Schema:
'''