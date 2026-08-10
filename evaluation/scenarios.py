"""
Evaluation Scenarios — Deterministic Software Development Scenarios

Five controlled scenarios spanning supported domains, each with
deterministic requirements, acceptance criteria, and constraints.

These are loaded by the experiment runner as fixed inputs.
No fabricated expected results are included.
"""

from evaluation.schemas import ScenarioDefinition, ScenarioComplexity


SCENARIOS: dict[str, ScenarioDefinition] = {
    "ecommerce-catalog": ScenarioDefinition(
        scenario_id="ecommerce-catalog",
        domain="ecommerce",
        complexity=ScenarioComplexity.MEDIUM,
        requirement=(
            "Build a product catalog REST API with CRUD operations for products. "
            "Each product has an id, name, description, price, category, and stock quantity. "
            "Implement inventory management: reject orders when stock is insufficient, "
            "and decrement stock on successful order placement."
        ),
        acceptance_criteria=[
            "CRUD endpoints for products (create, read, update, delete)",
            "Product schema validation (name required, price > 0, stock >= 0)",
            "Inventory check on order: reject if stock < requested quantity",
            "Stock decrement on successful order",
            "Proper HTTP status codes (201, 200, 400, 404)",
        ],
        constraints=[
            "Use Python",
            "RESTful design",
            "No external database required (in-memory acceptable)",
        ],
        expected_functionality=[
            "POST /products — Create a product",
            "GET /products — List all products",
            "GET /products/{id} — Get product by ID",
            "PUT /products/{id} — Update a product",
            "DELETE /products/{id} — Delete a product",
            "POST /orders — Place an order (validates stock)",
        ],
        evaluation_criteria=[
            "Code compiles without syntax errors",
            "All acceptance criteria addressed in generated code",
            "No path traversal or injection vulnerabilities",
        ],
    ),
    "healthcare-intake": ScenarioDefinition(
        scenario_id="healthcare-intake",
        domain="healthcare",
        complexity=ScenarioComplexity.HIGH,
        requirement=(
            "Build a patient intake form processing module. Accept patient data "
            "(name, date of birth, medical record number, insurance ID, chief complaint). "
            "Implement data anonymization: when generating reports, replace patient name "
            "with a hash and mask the last 4 digits of insurance ID."
        ),
        acceptance_criteria=[
            "Accept and validate patient intake data",
            "Required fields: name, date_of_birth, medical_record_number",
            "Anonymization function for patient name (SHA-256 hash)",
            "Insurance ID masking (show only last 4 digits)",
            "Generate anonymized patient summary report",
        ],
        constraints=[
            "Use Python",
            "No external database required",
            "Anonymization must be deterministic (same input = same hash)",
        ],
        expected_functionality=[
            "PatientIntake data model with validation",
            "anonymize_name(name) -> hashed string",
            "mask_insurance_id(insurance_id) -> masked string",
            "generate_report(patient) -> anonymized summary",
        ],
        evaluation_criteria=[
            "Anonymization correctly implemented",
            "No PII leakage in generated reports",
            "Input validation present",
        ],
    ),
    "finance-ledger": ScenarioDefinition(
        scenario_id="finance-ledger",
        domain="finance",
        complexity=ScenarioComplexity.MEDIUM,
        requirement=(
            "Build a transaction ledger validation script. Accept a list of transactions "
            "(id, amount, type: credit/debit, timestamp). Validate that the running balance "
            "never goes negative. Report any transactions that would cause a negative balance."
        ),
        acceptance_criteria=[
            "Parse a list of transactions with id, amount, type, timestamp",
            "Calculate running balance after each transaction",
            "Flag transactions that would cause negative balance",
            "Generate a validation report with pass/fail per transaction",
            "Final summary: total credits, total debits, final balance",
        ],
        constraints=[
            "Use Python",
            "Transactions must be processed in timestamp order",
            "All amounts must be positive numbers",
        ],
        expected_functionality=[
            "Transaction data model",
            "validate_ledger(transactions) -> ValidationReport",
            "Running balance calculation",
            "Negative balance detection",
        ],
        evaluation_criteria=[
            "Correct arithmetic in balance calculations",
            "Proper chronological ordering",
            "Edge cases handled (empty ledger, single transaction)",
        ],
    ),
    "education-enrollment": ScenarioDefinition(
        scenario_id="education-enrollment",
        domain="education",
        complexity=ScenarioComplexity.LOW,
        requirement=(
            "Build a simple course enrollment service. Students can enroll in courses. "
            "Each course has a maximum capacity. Reject enrollment when the course is full."
        ),
        acceptance_criteria=[
            "Course data model with id, name, max_capacity, enrolled_students",
            "Student data model with id, name",
            "Enroll student in course (reject if full)",
            "List enrolled students for a course",
            "Drop a student from a course",
        ],
        constraints=[
            "Use Python",
            "In-memory data storage",
            "No authentication required",
        ],
        expected_functionality=[
            "create_course(name, max_capacity) -> Course",
            "enroll_student(student_id, course_id) -> success/failure",
            "drop_student(student_id, course_id) -> success/failure",
            "get_enrollment(course_id) -> list of students",
        ],
        evaluation_criteria=[
            "Capacity enforcement works correctly",
            "Duplicate enrollment prevention",
            "Clean error handling",
        ],
    ),
    "travel-flights": ScenarioDefinition(
        scenario_id="travel-flights",
        domain="travel",
        complexity=ScenarioComplexity.MEDIUM,
        requirement=(
            "Build a flight availability aggregator. Given a list of flights "
            "(flight_number, origin, destination, departure_time, seats_available, price), "
            "implement search by origin/destination, filter by date range, and sort by price."
        ),
        acceptance_criteria=[
            "Flight data model with required fields",
            "Search flights by origin and destination",
            "Filter by departure date range",
            "Sort results by price (ascending/descending)",
            "Return empty list when no flights match",
        ],
        constraints=[
            "Use Python",
            "In-memory flight data",
            "Date handling with standard library",
        ],
        expected_functionality=[
            "Flight data model",
            "search_flights(origin, destination) -> list[Flight]",
            "filter_by_date(flights, start, end) -> list[Flight]",
            "sort_by_price(flights, ascending=True) -> list[Flight]",
        ],
        evaluation_criteria=[
            "Search filtering is correct",
            "Date comparison handles edge cases",
            "Sort order is correct",
        ],
    ),
}


def get_scenario(scenario_id: str) -> ScenarioDefinition:
    """Retrieve a scenario by ID. Raises KeyError if not found."""
    if scenario_id not in SCENARIOS:
        raise KeyError(f"Unknown scenario: {scenario_id}. Available: {list(SCENARIOS.keys())}")
    return SCENARIOS[scenario_id]


def list_scenario_ids() -> list[str]:
    """Return all available scenario IDs."""
    return list(SCENARIOS.keys())
